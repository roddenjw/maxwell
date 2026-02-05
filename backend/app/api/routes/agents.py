"""
Agent API Routes

Endpoints for agent-based writing analysis including:
- Multi-agent analysis (all agents in parallel)
- Single-agent quick checks
- Suggestion feedback tracking
- Author insights and learning data
- Smart Coach conversational interface
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.agents.orchestrator.writing_assistant import WritingAssistantOrchestrator
from app.agents.coach.smart_coach_agent import SmartCoachAgent, create_smart_coach
from app.agents.base.agent_config import AgentType, ModelConfig, ModelProvider
from app.services.author_learning_service import author_learning_service
from app.database import SessionLocal
from app.models.agent import AgentAnalysis, SuggestionFeedback, CoachSession


router = APIRouter(prefix="/api/agents", tags=["agents"])


# Request/Response Models

class AnalyzeTextRequest(BaseModel):
    """Request for multi-agent analysis"""
    api_key: str
    text: str
    user_id: str
    manuscript_id: str
    chapter_id: Optional[str] = None

    # Optional model selection
    model_provider: Optional[str] = "anthropic"
    model_name: Optional[str] = "claude-3-haiku-20240307"

    # Which agents to run (default: all)
    agents: Optional[List[str]] = None

    # Include author insights in response
    include_insights: bool = True


class QuickCheckRequest(BaseModel):
    """Request for single-agent quick check"""
    api_key: str
    text: str
    user_id: str
    manuscript_id: str
    agent_type: str  # continuity, style, structure, voice

    # Optional model selection
    model_provider: Optional[str] = "anthropic"
    model_name: Optional[str] = "claude-3-haiku-20240307"


class SuggestionFeedbackRequest(BaseModel):
    """Request to record suggestion feedback"""
    user_id: str
    agent_type: str
    suggestion_type: str
    suggestion_text: str
    action: str  # accepted, rejected, modified, ignored
    original_text: Optional[str] = None
    modified_text: Optional[str] = None
    manuscript_id: Optional[str] = None
    analysis_id: Optional[str] = None
    user_explanation: Optional[str] = None


# Smart Coach Request Models

class StartCoachSessionRequest(BaseModel):
    """Request to start a new coaching session"""
    api_key: str
    user_id: str
    manuscript_id: Optional[str] = None
    title: Optional[str] = None
    initial_context: Optional[Dict[str, Any]] = None

    # Optional model selection
    model_provider: Optional[str] = "anthropic"
    model_name: Optional[str] = "claude-3-haiku-20240307"


class CoachChatRequest(BaseModel):
    """Request to send a message to the coach"""
    api_key: str
    user_id: str
    session_id: str
    message: str
    context: Optional[Dict[str, Any]] = None  # selected_text, chapter_id, etc.

    # Optional model selection
    model_provider: Optional[str] = "anthropic"
    model_name: Optional[str] = "claude-3-haiku-20240307"


# Endpoints

@router.post("/analyze")
async def analyze_text(
    request: AnalyzeTextRequest,
    background_tasks: BackgroundTasks
):
    """
    Run multi-agent analysis on text.

    Runs all enabled agents in parallel and returns combined results.
    Results include recommendations, issues, teaching points, and costs.

    Returns:
        Combined analysis from all agents with:
        - recommendations: List of improvement suggestions
        - issues: List of potential problems found
        - teaching_points: Craft principles explained
        - praise: What the text does well
        - agent_results: Individual agent outputs
        - total_cost: Combined API cost
        - author_insights: Learning data about this author
    """
    try:
        # Build model config
        model_config = ModelConfig(
            provider=ModelProvider(request.model_provider),
            model_name=request.model_name,
            temperature=0.7,
            max_tokens=4096
        )

        # Determine which agents to run
        enabled_agents = None
        if request.agents:
            enabled_agents = [
                AgentType(agent) for agent in request.agents
                if agent in [a.value for a in AgentType]
            ]

        # Create orchestrator
        orchestrator = WritingAssistantOrchestrator(
            api_key=request.api_key,
            model_config=model_config,
            enabled_agents=enabled_agents
        )

        # Run analysis
        result = await orchestrator.analyze(
            text=request.text,
            user_id=request.user_id,
            manuscript_id=request.manuscript_id,
            current_chapter_id=request.chapter_id,
            include_author_insights=request.include_insights
        )

        # Store analysis result in background
        background_tasks.add_task(
            _store_analysis,
            user_id=request.user_id,
            manuscript_id=request.manuscript_id,
            chapter_id=request.chapter_id,
            input_text=request.text,
            result=result.to_dict()
        )

        return {
            "success": True,
            "data": result.to_dict(),
            "cost": {
                "total": result.total_cost,
                "formatted": f"${result.total_cost:.4f}"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick-check")
async def quick_check(request: QuickCheckRequest):
    """
    Run a single agent for quick feedback.

    Useful for real-time checks while writing.
    Faster and cheaper than full multi-agent analysis.
    """
    try:
        # Validate agent type
        try:
            agent_type = AgentType(request.agent_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agent type: {request.agent_type}. "
                       f"Valid types: {[a.value for a in AgentType]}"
            )

        # Build model config
        model_config = ModelConfig(
            provider=ModelProvider(request.model_provider),
            model_name=request.model_name,
            temperature=0.7,
            max_tokens=2048
        )

        # Create orchestrator with single agent
        orchestrator = WritingAssistantOrchestrator(
            api_key=request.api_key,
            model_config=model_config,
            enabled_agents=[agent_type]
        )

        # Run quick check
        result = await orchestrator.quick_check(
            text=request.text,
            user_id=request.user_id,
            manuscript_id=request.manuscript_id,
            focus_area=agent_type
        )

        return {
            "success": True,
            "data": result.to_dict(),
            "cost": {
                "total": result.cost,
                "formatted": f"${result.cost:.4f}"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def record_feedback(request: SuggestionFeedbackRequest):
    """
    Record user feedback on a suggestion.

    Used to learn author preferences and improve future suggestions.
    Actions: accepted, rejected, modified, ignored
    """
    try:
        # Validate action
        valid_actions = ["accepted", "rejected", "modified", "ignored"]
        if request.action not in valid_actions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action: {request.action}. "
                       f"Valid actions: {valid_actions}"
            )

        # Record feedback
        feedback = author_learning_service.record_suggestion_feedback(
            user_id=request.user_id,
            agent_type=request.agent_type,
            suggestion_type=request.suggestion_type,
            suggestion_text=request.suggestion_text,
            action=request.action,
            original_text=request.original_text,
            modified_text=request.modified_text,
            manuscript_id=request.manuscript_id,
            analysis_id=request.analysis_id,
            user_explanation=request.user_explanation
        )

        return {
            "success": True,
            "data": {
                "id": feedback.id,
                "action": feedback.action,
                "message": f"Feedback recorded: {request.action}"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/{user_id}")
async def get_author_insights(user_id: str):
    """
    Get author insights and learning data.

    Returns:
        - common_issues: Most frequently flagged issues
        - strengths: What the author does well
        - improvement_areas: Where to focus
        - progress: Improvement tracking over time
        - personalization: How we've adapted to this author
    """
    try:
        insights = author_learning_service.get_author_insights(user_id)

        return {
            "success": True,
            "data": insights
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{user_id}")
async def get_analysis_history(
    user_id: str,
    manuscript_id: Optional[str] = None,
    limit: int = 20
):
    """
    Get history of agent analyses for a user.

    Useful for reviewing past feedback and tracking progress.
    """
    db = SessionLocal()
    try:
        query = db.query(AgentAnalysis).filter(
            AgentAnalysis.user_id == user_id
        )

        if manuscript_id:
            query = query.filter(AgentAnalysis.manuscript_id == manuscript_id)

        analyses = query.order_by(
            AgentAnalysis.created_at.desc()
        ).limit(limit).all()

        return {
            "success": True,
            "data": [
                {
                    "id": a.id,
                    "manuscript_id": a.manuscript_id,
                    "agent_types": a.agent_types,
                    "total_cost": a.total_cost,
                    "created_at": a.created_at.isoformat(),
                    "recommendation_count": len(a.recommendations or []),
                    "issue_count": len(a.issues or []),
                    "user_rating": a.user_rating
                }
                for a in analyses
            ]
        }

    finally:
        db.close()


@router.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Get a specific analysis by ID"""
    db = SessionLocal()
    try:
        analysis = db.query(AgentAnalysis).filter(
            AgentAnalysis.id == analysis_id
        ).first()

        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        return {
            "success": True,
            "data": {
                "id": analysis.id,
                "user_id": analysis.user_id,
                "manuscript_id": analysis.manuscript_id,
                "chapter_id": analysis.chapter_id,
                "agent_types": analysis.agent_types,
                "recommendations": analysis.recommendations,
                "issues": analysis.issues,
                "teaching_points": analysis.teaching_points,
                "agent_results": analysis.agent_results,
                "total_cost": analysis.total_cost,
                "total_tokens": analysis.total_tokens,
                "execution_time_ms": analysis.execution_time_ms,
                "user_rating": analysis.user_rating,
                "user_feedback": analysis.user_feedback,
                "created_at": analysis.created_at.isoformat()
            }
        }

    finally:
        db.close()


@router.put("/analysis/{analysis_id}/rate")
async def rate_analysis(analysis_id: str, rating: int, feedback: Optional[str] = None):
    """
    Rate an analysis (1-5 stars).

    Used to improve agent quality over time.
    """
    if not 1 <= rating <= 5:
        raise HTTPException(
            status_code=400,
            detail="Rating must be between 1 and 5"
        )

    db = SessionLocal()
    try:
        analysis = db.query(AgentAnalysis).filter(
            AgentAnalysis.id == analysis_id
        ).first()

        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        analysis.user_rating = rating
        if feedback:
            analysis.user_feedback = feedback

        db.commit()

        return {
            "success": True,
            "message": f"Analysis rated {rating}/5"
        }

    finally:
        db.close()


@router.get("/types")
async def get_agent_types():
    """Get available agent types and their descriptions"""
    return {
        "success": True,
        "data": [
            {
                "type": "continuity",
                "name": "Continuity",
                "description": "Checks character facts, timeline consistency, and world rules"
            },
            {
                "type": "style",
                "name": "Style",
                "description": "Analyzes prose quality, show vs tell, pacing, word choice"
            },
            {
                "type": "structure",
                "name": "Structure",
                "description": "Checks beat alignment, story progression, scene goals"
            },
            {
                "type": "voice",
                "name": "Voice",
                "description": "Analyzes dialogue authenticity and character voice consistency"
            }
        ]
    }


# ============================================================================
# Smart Coach Endpoints
# ============================================================================

@router.post("/coach/session")
async def start_coach_session(request: StartCoachSessionRequest):
    """
    Start a new coaching session.

    Creates a conversation context for the Smart Coach.
    Sessions persist across messages and can be resumed later.
    """
    try:
        model_config = ModelConfig(
            provider=ModelProvider(request.model_provider),
            model_name=request.model_name,
            temperature=0.7,
            max_tokens=2048
        )

        coach = create_smart_coach(
            api_key=request.api_key,
            user_id=request.user_id,
            model_config=model_config
        )

        session = await coach.start_session(
            manuscript_id=request.manuscript_id,
            initial_context=request.initial_context,
            title=request.title
        )

        return {
            "success": True,
            "data": {
                "id": session.id,
                "title": session.title,
                "manuscript_id": session.manuscript_id,
                "status": session.status,
                "created_at": session.created_at.isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/coach/chat")
async def coach_chat(request: CoachChatRequest):
    """
    Send a message to the Smart Coach and get a response.

    The coach can answer questions about your story using tools
    to query your Codex, Timeline, Outline, and Manuscript.
    """
    try:
        model_config = ModelConfig(
            provider=ModelProvider(request.model_provider),
            model_name=request.model_name,
            temperature=0.7,
            max_tokens=2048
        )

        coach = create_smart_coach(
            api_key=request.api_key,
            user_id=request.user_id,
            model_config=model_config
        )

        response = await coach.chat(
            session_id=request.session_id,
            message=request.message,
            context=request.context
        )

        return {
            "success": True,
            "data": response.to_dict(),
            "cost": {
                "total": response.cost,
                "formatted": f"${response.cost:.4f}"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/coach/sessions/{user_id}")
async def list_coach_sessions(
    user_id: str,
    manuscript_id: Optional[str] = None,
    include_archived: bool = False,
    limit: int = 20
):
    """
    List coaching sessions for a user.

    Returns recent sessions with basic metadata.
    """
    db = SessionLocal()
    try:
        query = db.query(CoachSession).filter(
            CoachSession.user_id == user_id
        )

        if manuscript_id:
            query = query.filter(CoachSession.manuscript_id == manuscript_id)

        if not include_archived:
            query = query.filter(CoachSession.status == "active")

        sessions = query.order_by(
            CoachSession.updated_at.desc()
        ).limit(limit).all()

        return {
            "success": True,
            "data": [
                {
                    "id": s.id,
                    "title": s.title,
                    "manuscript_id": s.manuscript_id,
                    "message_count": s.message_count,
                    "total_cost": s.total_cost,
                    "status": s.status,
                    "created_at": s.created_at.isoformat(),
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                    "last_message_at": s.last_message_at.isoformat() if s.last_message_at else None
                }
                for s in sessions
            ]
        }

    finally:
        db.close()


@router.get("/coach/session/{session_id}")
async def get_coach_session(session_id: str):
    """Get a specific coaching session with its messages."""
    db = SessionLocal()
    try:
        session = db.query(CoachSession).filter(
            CoachSession.id == session_id
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get messages
        from app.models.agent import CoachMessage
        messages = db.query(CoachMessage).filter(
            CoachMessage.session_id == session_id
        ).order_by(
            CoachMessage.created_at.asc()
        ).all()

        return {
            "success": True,
            "data": {
                "session": {
                    "id": session.id,
                    "title": session.title,
                    "manuscript_id": session.manuscript_id,
                    "message_count": session.message_count,
                    "total_cost": session.total_cost,
                    "total_tokens": session.total_tokens,
                    "status": session.status,
                    "initial_context": session.initial_context,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat() if session.updated_at else None
                },
                "messages": [
                    {
                        "id": m.id,
                        "role": m.role,
                        "content": m.content,
                        "tools_used": m.tools_used,
                        "cost": m.cost,
                        "tokens": m.tokens,
                        "created_at": m.created_at.isoformat()
                    }
                    for m in messages
                ]
            }
        }

    finally:
        db.close()


@router.put("/coach/session/{session_id}/archive")
async def archive_coach_session(session_id: str, user_id: str):
    """Archive a coaching session."""
    db = SessionLocal()
    try:
        session = db.query(CoachSession).filter(
            CoachSession.id == session_id,
            CoachSession.user_id == user_id
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        session.status = "archived"
        db.commit()

        return {
            "success": True,
            "message": "Session archived"
        }

    finally:
        db.close()


@router.put("/coach/session/{session_id}/title")
async def update_coach_session_title(session_id: str, user_id: str, title: str):
    """Update a coaching session's title."""
    db = SessionLocal()
    try:
        session = db.query(CoachSession).filter(
            CoachSession.id == session_id,
            CoachSession.user_id == user_id
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        session.title = title
        db.commit()

        return {
            "success": True,
            "message": "Session title updated"
        }

    finally:
        db.close()


# ============================================================================
# Consistency Checking Endpoints
# ============================================================================

class ConsistencyCheckRequest(BaseModel):
    """Request for consistency checking"""
    api_key: str
    text: str
    user_id: str
    manuscript_id: str
    chapter_id: Optional[str] = None
    focus: Optional[str] = "all"  # character, timeline, world, relationship, location, all

    # Optional model selection
    model_provider: Optional[str] = "anthropic"
    model_name: Optional[str] = "claude-3-haiku-20240307"


class FullScanRequest(BaseModel):
    """Request for full manuscript consistency scan"""
    api_key: str
    user_id: str
    manuscript_id: str
    chapter_ids: Optional[List[str]] = None  # If not provided, scans all
    include_resolved: bool = False

    # Optional model selection
    model_provider: Optional[str] = "anthropic"
    model_name: Optional[str] = "claude-3-haiku-20240307"


@router.post("/consistency/check")
async def consistency_quick_check(request: ConsistencyCheckRequest):
    """
    Perform a quick consistency check on text.

    Ideal for real-time checking while writing.
    Focus areas: character, timeline, world, relationship, location, all
    """
    try:
        from app.agents.specialized.consistency_agent import (
            create_consistency_agent,
            ConsistencyFocus
        )

        model_config = ModelConfig(
            provider=ModelProvider(request.model_provider),
            model_name=request.model_name,
            temperature=0.3,  # Lower temperature for consistency checking
            max_tokens=2048
        )

        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        config.model_config = model_config

        agent = create_consistency_agent(request.api_key, config)

        # Parse focus area
        try:
            focus = ConsistencyFocus(request.focus)
        except ValueError:
            focus = ConsistencyFocus.ALL

        result = await agent.quick_check(
            text=request.text,
            user_id=request.user_id,
            manuscript_id=request.manuscript_id,
            focus=focus,
            chapter_id=request.chapter_id
        )

        return {
            "success": True,
            "data": result.to_dict(),
            "cost": {
                "total": result.cost,
                "formatted": f"${result.cost:.4f}"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/consistency/full-scan")
async def consistency_full_scan(request: FullScanRequest, background_tasks: BackgroundTasks):
    """
    Perform a comprehensive consistency scan of the manuscript.

    This is thorough but slower - runs in background for large manuscripts.
    """
    try:
        from app.agents.specialized.consistency_agent import create_consistency_agent

        model_config = ModelConfig(
            provider=ModelProvider(request.model_provider),
            model_name=request.model_name,
            temperature=0.3,
            max_tokens=4096
        )

        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        config.model_config = model_config

        agent = create_consistency_agent(request.api_key, config)

        result = await agent.full_scan(
            user_id=request.user_id,
            manuscript_id=request.manuscript_id,
            chapter_ids=request.chapter_ids,
            include_resolved=request.include_resolved
        )

        return {
            "success": True,
            "data": result.to_dict(),
            "cost": {
                "total": result.cost,
                "formatted": f"${result.cost:.4f}"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Research & Worldbuilding Endpoints
# ============================================================================

class WorldbuildingRequest(BaseModel):
    """Request for worldbuilding generation"""
    api_key: str
    topic: str
    user_id: str
    manuscript_id: str
    category: Optional[str] = None  # culture, magic_system, geography, etc.
    constraints: Optional[List[str]] = None
    count: int = 3
    genre: str = "fantasy"

    # Optional model selection
    model_provider: Optional[str] = "anthropic"
    model_name: Optional[str] = "claude-3-haiku-20240307"


class ResearchTopicRequest(BaseModel):
    """Request for topic research"""
    api_key: str
    topic: str
    user_id: str
    manuscript_id: Optional[str] = None
    purpose: str = "worldbuilding inspiration"
    questions: Optional[List[str]] = None
    use_web_search: bool = False  # Not yet implemented

    # Optional model selection
    model_provider: Optional[str] = "anthropic"
    model_name: Optional[str] = "claude-3-haiku-20240307"


@router.post("/research/worldbuilding")
async def generate_worldbuilding(request: WorldbuildingRequest):
    """
    Generate interconnected worldbuilding elements.

    Creates elements that fit the existing world context and can be
    imported into the Codex as draft entities.
    """
    try:
        from app.agents.specialized.research_agent import (
            create_research_agent,
            WorldbuildingCategory
        )

        model_config = ModelConfig(
            provider=ModelProvider(request.model_provider),
            model_name=request.model_name,
            temperature=0.8,  # Higher temperature for creativity
            max_tokens=4096
        )

        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        config.model_config = model_config
        config.response_format = "json"

        agent = create_research_agent(request.api_key, config)

        # Parse category if provided
        category = None
        if request.category:
            try:
                category = WorldbuildingCategory(request.category)
            except ValueError:
                pass

        result = await agent.generate_worldbuilding(
            topic=request.topic,
            user_id=request.user_id,
            manuscript_id=request.manuscript_id,
            category=category,
            constraints=request.constraints,
            count=request.count,
            genre=request.genre
        )

        return {
            "success": True,
            "data": result.to_dict(),
            "cost": {
                "total": result.cost,
                "formatted": f"${result.cost:.4f}"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/research/topic")
async def research_topic(request: ResearchTopicRequest):
    """
    Research a topic for fiction writing.

    Provides key facts, interesting details, and story-worthy aspects
    adapted for the author's world.
    """
    try:
        from app.agents.specialized.research_agent import create_research_agent

        model_config = ModelConfig(
            provider=ModelProvider(request.model_provider),
            model_name=request.model_name,
            temperature=0.7,
            max_tokens=4096
        )

        config = AgentConfig.for_agent_type(AgentType.CONTINUITY)
        config.model_config = model_config
        config.response_format = "json"

        agent = create_research_agent(request.api_key, config)

        result = await agent.research_topic(
            topic=request.topic,
            user_id=request.user_id,
            manuscript_id=request.manuscript_id,
            purpose=request.purpose,
            questions=request.questions,
            use_web_search=request.use_web_search
        )

        return {
            "success": True,
            "data": result.to_dict(),
            "cost": {
                "total": result.cost,
                "formatted": f"${result.cost:.4f}"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/research/categories")
async def get_worldbuilding_categories():
    """Get available worldbuilding categories"""
    from app.agents.specialized.research_agent import WorldbuildingCategory

    return {
        "success": True,
        "data": [
            {"value": cat.value, "name": cat.value.replace("_", " ").title()}
            for cat in WorldbuildingCategory
        ]
    }


# ============================================================================
# Story Structure Guide Endpoints
# ============================================================================

class OutlineGuideRequest(BaseModel):
    """Request for outline guidance from Maxwell"""
    api_key: str
    user_id: str
    manuscript_id: str

    # Mode of operation
    mode: str = "analyze"  # analyze, suggest_beat, suggest_scenes, chapter_feedback, next_step

    # Optional parameters for specific modes
    query: Optional[str] = None  # Free-form query
    beat_id: Optional[str] = None
    beat_label: Optional[str] = None
    chapter_id: Optional[str] = None
    from_beat: Optional[str] = None  # For suggest_scenes mode
    to_beat: Optional[str] = None    # For suggest_scenes mode

    # Response control
    detail_level: str = "standard"  # quick, standard, detailed

    # Optional model selection
    model_provider: Optional[str] = "anthropic"
    model_name: Optional[str] = "claude-3-haiku-20240307"


@router.post("/maxwell/outline-guide")
async def outline_guide(request: OutlineGuideRequest):
    """
    Get Maxwell's guidance on story structure and outlining.

    This is a specialized endpoint for helping writers develop their outlines.
    Unlike the general analysis endpoints (which analyze written prose),
    this helps writers BUILD their outline from scratch.

    Modes:
    - analyze: Full outline analysis with gaps and suggestions
    - suggest_beat: Get content suggestions for a specific beat
    - suggest_scenes: Get scene ideas between two beats
    - chapter_feedback: Analyze chapter against its linked beat
    - next_step: Get recommendation for what to work on next

    Detail levels:
    - quick: 2-3 key points
    - standard: Comprehensive but focused
    - detailed: Full breakdown with examples and craft explanations
    """
    try:
        from app.agents.specialized.story_structure_guide_agent import (
            create_story_structure_guide_agent
        )
        from app.agents.base.agent_config import AgentConfig, AgentType

        model_config = ModelConfig(
            provider=ModelProvider(request.model_provider),
            model_name=request.model_name,
            temperature=0.7,
            max_tokens=4096
        )

        config = AgentConfig.for_agent_type(AgentType.STORY_STRUCTURE_GUIDE)
        config.model_config = model_config

        agent = create_story_structure_guide_agent(request.api_key, config)

        result = await agent.guide_outline(
            mode=request.mode,
            user_id=request.user_id,
            manuscript_id=request.manuscript_id,
            query=request.query,
            beat_id=request.beat_id,
            beat_label=request.beat_label,
            chapter_id=request.chapter_id,
            from_beat=request.from_beat,
            to_beat=request.to_beat,
            detail_level=request.detail_level
        )

        return {
            "success": True,
            "data": result.to_dict(),
            "cost": {
                "total": result.cost,
                "formatted": f"${result.cost:.4f}"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/outline-guide/modes")
async def get_outline_guide_modes():
    """Get available outline guide modes and their descriptions"""
    return {
        "success": True,
        "data": [
            {
                "mode": "analyze",
                "name": "Analyze Outline",
                "description": "Get a full analysis of your outline - what's done, what's missing, and recommended next steps"
            },
            {
                "mode": "suggest_beat",
                "name": "Suggest Beat Content",
                "description": "Get story-specific suggestions for what should happen at a particular beat"
            },
            {
                "mode": "suggest_scenes",
                "name": "Suggest Bridge Scenes",
                "description": "Get scene ideas to connect two beats in your story"
            },
            {
                "mode": "chapter_feedback",
                "name": "Chapter-Beat Feedback",
                "description": "Analyze how well a chapter fulfills its linked beat's purpose"
            },
            {
                "mode": "next_step",
                "name": "What's Next?",
                "description": "Get a recommendation for what to work on next in your outline"
            }
        ]
    }


# ============================================================================
# Unified Maxwell Endpoints
# ============================================================================

class MaxwellChatRequest(BaseModel):
    """Request for unified Maxwell chat"""
    api_key: str
    user_id: str
    message: str
    manuscript_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None  # selected_text, chapter_id, etc.
    auto_analyze: bool = True  # Whether to auto-invoke agents when needed

    # Optional model selection
    model_provider: Optional[str] = "anthropic"
    model_name: Optional[str] = "claude-3-haiku-20240307"


class MaxwellAnalyzeRequest(BaseModel):
    """Request for unified Maxwell analysis"""
    api_key: str
    user_id: str
    text: str
    manuscript_id: str
    chapter_id: Optional[str] = None
    tone: Optional[str] = "encouraging"  # encouraging, direct, teaching, celebratory

    # Optional model selection
    model_provider: Optional[str] = "anthropic"
    model_name: Optional[str] = "claude-3-haiku-20240307"


class MaxwellQuickCheckRequest(BaseModel):
    """Request for Maxwell quick check"""
    api_key: str
    user_id: str
    text: str
    focus: str  # style, continuity, structure, voice, dialogue, pacing
    manuscript_id: Optional[str] = None

    # Optional model selection
    model_provider: Optional[str] = "anthropic"
    model_name: Optional[str] = "claude-3-haiku-20240307"


class MaxwellExplainRequest(BaseModel):
    """Request for Maxwell to explain a writing concept"""
    api_key: str
    user_id: str
    topic: str  # e.g., "show vs tell", "pacing", "dialogue tags"
    context: Optional[str] = None  # Optional manuscript excerpt for relevance

    # Optional model selection
    model_provider: Optional[str] = "anthropic"
    model_name: Optional[str] = "claude-3-haiku-20240307"


@router.post("/maxwell/chat")
async def maxwell_chat(request: MaxwellChatRequest):
    """
    Chat with Maxwell - the unified writing coach.

    Maxwell automatically determines whether to:
    - Respond conversationally
    - Invoke specialized agents for analysis
    - Combine both for comprehensive feedback

    This is the PRIMARY entry point for interacting with Maxwell.
    Users talk to ONE entity who internally delegates to specialists.
    """
    try:
        from app.agents.orchestrator.maxwell_unified import create_maxwell

        model_config = ModelConfig(
            provider=ModelProvider(request.model_provider),
            model_name=request.model_name,
            temperature=0.7,
            max_tokens=2048
        )

        maxwell = create_maxwell(
            api_key=request.api_key,
            user_id=request.user_id,
            model_config=model_config
        )

        response = await maxwell.chat(
            message=request.message,
            manuscript_id=request.manuscript_id,
            context=request.context,
            auto_analyze=request.auto_analyze
        )

        return {
            "success": True,
            "data": response.to_dict(),
            "cost": {
                "total": response.cost,
                "formatted": f"${response.cost:.4f}"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/maxwell/analyze")
async def maxwell_analyze(
    request: MaxwellAnalyzeRequest,
    background_tasks: BackgroundTasks
):
    """
    Request a full analysis from Maxwell.

    Runs all specialized agents (Style, Continuity, Structure, Voice)
    and synthesizes their feedback into Maxwell's unified voice.

    Returns conversational feedback that feels like talking to one expert,
    plus structured data for UI display.
    """
    try:
        from app.agents.orchestrator.maxwell_unified import create_maxwell
        from app.agents.orchestrator.maxwell_synthesizer import SynthesisTone

        model_config = ModelConfig(
            provider=ModelProvider(request.model_provider),
            model_name=request.model_name,
            temperature=0.7,
            max_tokens=4096
        )

        # Map tone string to enum
        tone_map = {
            "encouraging": SynthesisTone.ENCOURAGING,
            "direct": SynthesisTone.DIRECT,
            "teaching": SynthesisTone.TEACHING,
            "celebratory": SynthesisTone.CELEBRATORY
        }
        tone = tone_map.get(request.tone, SynthesisTone.ENCOURAGING)

        maxwell = create_maxwell(
            api_key=request.api_key,
            user_id=request.user_id,
            model_config=model_config
        )

        response = await maxwell.analyze(
            text=request.text,
            manuscript_id=request.manuscript_id,
            chapter_id=request.chapter_id,
            tone=tone
        )

        # Store analysis in background
        background_tasks.add_task(
            _store_analysis,
            user_id=request.user_id,
            manuscript_id=request.manuscript_id,
            chapter_id=request.chapter_id,
            input_text=request.text,
            result={
                "recommendations": response.feedback.priorities if response.feedback else [],
                "praise": response.feedback.highlights if response.feedback else [],
                "teaching_points": response.feedback.teaching_moments if response.feedback else [],
                "agent_results": {"unified": True},
                "total_cost": response.cost,
                "total_tokens": response.tokens,
                "execution_time_ms": response.execution_time_ms
            }
        )

        return {
            "success": True,
            "data": response.to_dict(),
            "cost": {
                "total": response.cost,
                "formatted": f"${response.cost:.4f}"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/maxwell/quick-check")
async def maxwell_quick_check(request: MaxwellQuickCheckRequest):
    """
    Quick focused check from Maxwell.

    Uses a single specialized agent based on focus area for fast feedback.
    Ideal for real-time checking while writing.

    Focus areas:
    - style/prose/pacing: Style agent
    - continuity/consistency: Continuity agent
    - structure/plot: Structure agent
    - voice/dialogue: Voice agent
    """
    try:
        from app.agents.orchestrator.maxwell_unified import create_maxwell

        model_config = ModelConfig(
            provider=ModelProvider(request.model_provider),
            model_name=request.model_name,
            temperature=0.7,
            max_tokens=2048
        )

        maxwell = create_maxwell(
            api_key=request.api_key,
            user_id=request.user_id,
            model_config=model_config
        )

        response = await maxwell.quick_check(
            text=request.text,
            focus=request.focus,
            manuscript_id=request.manuscript_id
        )

        return {
            "success": True,
            "data": response.to_dict(),
            "cost": {
                "total": response.cost,
                "formatted": f"${response.cost:.4f}"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/maxwell/explain")
async def maxwell_explain(request: MaxwellExplainRequest):
    """
    Get Maxwell's explanation of a writing concept.

    Maxwell explains craft principles in a warm, educational way,
    with examples and practical application.

    Good for topics like:
    - "show vs tell"
    - "pacing"
    - "dialogue tags"
    - "active voice"
    - "character arc"
    """
    try:
        from app.agents.orchestrator.maxwell_unified import create_maxwell

        model_config = ModelConfig(
            provider=ModelProvider(request.model_provider),
            model_name=request.model_name,
            temperature=0.7,
            max_tokens=1024
        )

        maxwell = create_maxwell(
            api_key=request.api_key,
            user_id=request.user_id,
            model_config=model_config
        )

        response = await maxwell.explain(
            topic=request.topic,
            context=request.context
        )

        return {
            "success": True,
            "data": response.to_dict(),
            "cost": {
                "total": response.cost,
                "formatted": f"${response.cost:.4f}"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Background task helpers

async def _store_analysis(
    user_id: str,
    manuscript_id: str,
    chapter_id: Optional[str],
    input_text: str,
    result: Dict[str, Any]
):
    """Store analysis result in database"""
    db = SessionLocal()
    try:
        import hashlib
        input_hash = hashlib.md5(input_text.encode()).hexdigest()

        analysis = AgentAnalysis(
            user_id=user_id,
            manuscript_id=manuscript_id,
            chapter_id=chapter_id,
            input_text=input_text[:10000],  # Limit stored text
            input_hash=input_hash,
            agent_types=list(result.get("agent_results", {}).keys()),
            recommendations=result.get("recommendations", []),
            issues=result.get("issues", []),
            teaching_points=result.get("teaching_points", []),
            agent_results=result.get("agent_results", {}),
            total_cost=result.get("total_cost", 0),
            total_tokens=result.get("total_tokens", 0),
            execution_time_ms=result.get("execution_time_ms", 0)
        )

        db.add(analysis)
        db.commit()

    except Exception as e:
        print(f"Failed to store analysis: {e}")
    finally:
        db.close()


# ==================== Maxwell Memory & Preferences Endpoints ====================


class UpdatePreferencesRequest(BaseModel):
    """Request to update Maxwell preferences"""
    user_id: str
    preferred_tone: Optional[str] = None  # encouraging, direct, teaching, celebratory, formal, casual
    feedback_depth: Optional[str] = None  # brief, standard, comprehensive
    teaching_mode: Optional[str] = None  # on, off, auto
    priority_focus: Optional[str] = None  # plot, character, prose, pacing, all
    proactive_suggestions: Optional[str] = None  # on, off, minimal


class StoryHealthRequest(BaseModel):
    """Request for story health assessment"""
    api_key: str
    user_id: str
    manuscript_id: str
    text: str
    model_provider: Optional[str] = "anthropic"
    model_name: Optional[str] = "claude-3-haiku-20240307"


@router.get("/maxwell/history")
async def get_conversation_history(
    user_id: str,
    manuscript_id: Optional[str] = None,
    limit: int = 20,
    interaction_type: Optional[str] = None,
):
    """
    Get Maxwell conversation history for a user.

    Returns recent conversations with Maxwell, optionally filtered by manuscript.
    """
    from app.services.maxwell_memory_service import create_maxwell_memory_service

    db = SessionLocal()
    try:
        memory_service = create_maxwell_memory_service(db)
        conversations = memory_service.get_recent_conversations(
            user_id=user_id,
            manuscript_id=manuscript_id,
            limit=limit,
            interaction_type=interaction_type,
        )

        return {
            "success": True,
            "data": [
                {
                    "id": c.id,
                    "interaction_type": c.interaction_type,
                    "user_message": c.user_message,
                    "maxwell_response": c.maxwell_response[:500] if c.maxwell_response else None,
                    "response_type": c.response_type,
                    "focus_area": c.focus_area,
                    "agents_consulted": c.agents_consulted,
                    "cost": c.cost,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
                for c in conversations
            ]
        }
    finally:
        db.close()


@router.get("/maxwell/context")
async def get_conversation_context(
    user_id: str,
    manuscript_id: Optional[str] = None,
    lookback_days: int = 30,
    max_conversations: int = 10,
):
    """
    Get conversation context for Maxwell to reference.

    Returns summaries of recent feedback for "You mentioned before..." references.
    """
    from app.services.maxwell_memory_service import create_maxwell_memory_service

    db = SessionLocal()
    try:
        memory_service = create_maxwell_memory_service(db)
        context = memory_service.get_conversation_context(
            user_id=user_id,
            manuscript_id=manuscript_id,
            lookback_days=lookback_days,
            max_conversations=max_conversations,
        )

        return {
            "success": True,
            "data": context
        }
    finally:
        db.close()


@router.get("/maxwell/insights")
async def get_insights(
    user_id: str,
    manuscript_id: Optional[str] = None,
    category: Optional[str] = None,
    include_resolved: bool = False,
    limit: int = 10,
):
    """
    Get extracted insights from Maxwell conversations.

    Insights are key points extracted from feedback for quick reference.
    """
    from app.services.maxwell_memory_service import create_maxwell_memory_service

    db = SessionLocal()
    try:
        memory_service = create_maxwell_memory_service(db)
        insights = memory_service.get_relevant_insights(
            user_id=user_id,
            manuscript_id=manuscript_id,
            category=category,
            include_resolved=include_resolved,
            limit=limit,
        )

        return {
            "success": True,
            "data": [
                {
                    "id": i.id,
                    "category": i.category,
                    "insight_text": i.insight_text,
                    "subject": i.subject,
                    "sentiment": i.sentiment,
                    "importance": i.importance,
                    "resolved": i.resolved,
                    "created_at": i.created_at.isoformat() if i.created_at else None,
                }
                for i in insights
            ]
        }
    finally:
        db.close()


@router.post("/maxwell/insights/{insight_id}/resolve")
async def resolve_insight(
    insight_id: str,
    resolution: str = "addressed",
):
    """Mark an insight as resolved."""
    from app.services.maxwell_memory_service import create_maxwell_memory_service

    db = SessionLocal()
    try:
        memory_service = create_maxwell_memory_service(db)
        insight = memory_service.mark_insight_resolved(insight_id, resolution)

        if not insight:
            raise HTTPException(status_code=404, detail="Insight not found")

        return {
            "success": True,
            "data": {
                "id": insight.id,
                "resolved": insight.resolved,
            }
        }
    finally:
        db.close()


@router.get("/maxwell/preferences")
async def get_preferences(user_id: str):
    """Get Maxwell preferences for a user."""
    from app.services.maxwell_memory_service import create_maxwell_memory_service

    db = SessionLocal()
    try:
        memory_service = create_maxwell_memory_service(db)
        prefs = memory_service.get_preferences(user_id)

        return {
            "success": True,
            "data": {
                "preferred_tone": prefs.preferred_tone,
                "feedback_depth": prefs.feedback_depth,
                "teaching_mode": prefs.teaching_mode,
                "priority_focus": prefs.priority_focus,
                "proactive_suggestions": prefs.proactive_suggestions,
                "extra_preferences": prefs.extra_preferences,
            }
        }
    finally:
        db.close()


@router.put("/maxwell/preferences")
async def update_preferences(request: UpdatePreferencesRequest):
    """Update Maxwell preferences for a user."""
    from app.services.maxwell_memory_service import create_maxwell_memory_service

    db = SessionLocal()
    try:
        memory_service = create_maxwell_memory_service(db)
        prefs = memory_service.update_preferences(
            user_id=request.user_id,
            preferred_tone=request.preferred_tone,
            feedback_depth=request.feedback_depth,
            teaching_mode=request.teaching_mode,
            priority_focus=request.priority_focus,
            proactive_suggestions=request.proactive_suggestions,
        )

        return {
            "success": True,
            "data": {
                "preferred_tone": prefs.preferred_tone,
                "feedback_depth": prefs.feedback_depth,
                "teaching_mode": prefs.teaching_mode,
                "priority_focus": prefs.priority_focus,
                "proactive_suggestions": prefs.proactive_suggestions,
            }
        }
    finally:
        db.close()


# ==================== Proactive Nudges Endpoints ====================


@router.get("/maxwell/nudges")
async def get_nudges(
    user_id: str,
    manuscript_id: Optional[str] = None,
    limit: int = 10,
    include_viewed: bool = False,
):
    """
    Get pending proactive nudges for a user.

    Nudges are gentle suggestions Maxwell generates based on detected patterns.
    """
    from app.services.proactive_suggestions_service import create_proactive_suggestions_service

    db = SessionLocal()
    try:
        nudge_service = create_proactive_suggestions_service(db)
        nudges = nudge_service.get_pending_nudges(
            user_id=user_id,
            manuscript_id=manuscript_id,
            limit=limit,
            include_viewed=include_viewed,
        )

        return {
            "success": True,
            "data": [
                {
                    "id": n.id,
                    "nudge_type": n.nudge_type,
                    "priority": n.priority,
                    "title": n.title,
                    "message": n.message,
                    "details": n.details,
                    "manuscript_id": n.manuscript_id,
                    "chapter_id": n.chapter_id,
                    "viewed": n.viewed,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                }
                for n in nudges
            ]
        }
    finally:
        db.close()


@router.post("/maxwell/nudges/{nudge_id}/dismiss")
async def dismiss_nudge(nudge_id: str, user_id: str):
    """Dismiss a nudge."""
    from app.services.proactive_suggestions_service import create_proactive_suggestions_service

    db = SessionLocal()
    try:
        nudge_service = create_proactive_suggestions_service(db)
        nudge = nudge_service.dismiss_nudge(nudge_id, user_id)

        if not nudge:
            raise HTTPException(status_code=404, detail="Nudge not found")

        return {"success": True, "data": {"id": nudge.id, "dismissed": True}}
    finally:
        db.close()


@router.post("/maxwell/nudges/{nudge_id}/view")
async def mark_nudge_viewed(nudge_id: str, user_id: str):
    """Mark a nudge as viewed."""
    from app.services.proactive_suggestions_service import create_proactive_suggestions_service

    db = SessionLocal()
    try:
        nudge_service = create_proactive_suggestions_service(db)
        nudge = nudge_service.mark_nudge_viewed(nudge_id, user_id)

        if not nudge:
            raise HTTPException(status_code=404, detail="Nudge not found")

        return {"success": True, "data": {"id": nudge.id, "viewed": True}}
    finally:
        db.close()


@router.get("/maxwell/weekly-insight")
async def get_weekly_insight(
    user_id: str,
    week_offset: int = 0,
):
    """
    Get weekly writing insight summary.

    week_offset: 0 = current week, 1 = last week, etc.
    """
    from app.services.proactive_suggestions_service import create_proactive_suggestions_service

    db = SessionLocal()
    try:
        nudge_service = create_proactive_suggestions_service(db)
        insight = nudge_service.get_weekly_insight(user_id, week_offset)

        if not insight:
            return {"success": True, "data": None}

        return {
            "success": True,
            "data": {
                "id": insight.id,
                "week_start": insight.week_start.isoformat(),
                "week_end": insight.week_end.isoformat(),
                "summary": insight.summary,
                "highlights": insight.highlights,
                "areas_to_improve": insight.areas_to_improve,
                "word_count_total": insight.word_count_total,
                "chapters_worked_on": insight.chapters_worked_on,
                "most_active_day": insight.most_active_day,
                "analyses_run": insight.analyses_run,
                "issues_found": insight.issues_found,
                "issues_addressed": insight.issues_addressed,
            }
        }
    finally:
        db.close()


# ==================== Story Health Endpoint ====================


@router.post("/maxwell/story-health")
async def get_story_health(request: StoryHealthRequest):
    """
    Get unified story health assessment.

    Runs all agents and provides:
    - Health scores per domain (character, plot, prose, pacing, consistency)
    - Detected conflicts between agents with bridge suggestions
    - Top strengths and concerns
    - Primary focus recommendation
    """
    from app.agents.orchestrator import (
        WritingAssistantOrchestrator,
        CrossAgentReasoner,
        create_cross_agent_reasoner,
    )

    try:
        # Create orchestrator and run analysis
        model_config = ModelConfig(
            provider=ModelProvider(request.model_provider),
            model_name=request.model_name,
            temperature=0.3,
            max_tokens=2048
        )

        orchestrator = WritingAssistantOrchestrator(
            api_key=request.api_key,
            default_model_config=model_config
        )

        # Run all agents
        result = await orchestrator.analyze(
            text=request.text,
            user_id=request.user_id,
            manuscript_id=request.manuscript_id,
        )

        # Create reasoner and assess health
        reasoner = create_cross_agent_reasoner()
        health = reasoner.assess_story_health(result.agent_results)

        return {
            "success": True,
            "data": health.to_dict(),
            "cost": {
                "total": result.total_cost,
                "formatted": f"${result.total_cost:.4f}"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

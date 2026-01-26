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

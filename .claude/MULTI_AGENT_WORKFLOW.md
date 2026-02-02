# Multi-Agent Code Review System

This document explains how to use Maxwell's multi-agent code review system for improved code quality.

## Overview

The system uses three specialized agents that work together:

| Agent | Role | When Active |
|-------|------|-------------|
| **Architect** | Design decisions, pattern enforcement | Complex tasks, new features |
| **Developer** | Implementation, testing | All tasks |
| **Reviewer** | Quality assurance, security review | Standard and complex tasks |

## Quick Start

### Option 1: Trigger Automatically

When asking Claude to implement something, add keywords to trigger the appropriate workflow:

```
"Implement [feature] using the multi-agent workflow"
"Add [feature] with architect review"
"Build [feature] with code review"
```

### Option 2: Request Specific Workflow

```
"Use the complex task workflow to add [feature]"
"Run this through architect → developer → reviewer"
```

### Option 3: Manual Orchestration

Read the orchestrator prompt and follow the workflow yourself:
```
cat .claude/prompts/orchestrator.md
```

## Workflows

### Simple Task (Developer Only)
**Best for:** Bug fixes, documentation, config changes

```
User → Developer → Done
```

**Example prompt:**
```
Fix the typo in the chapter title validation
```

### Standard Task (Developer + Reviewer)
**Best for:** Features within existing patterns, refactors

```
User → Developer → Reviewer → [Iterate if needed] → Done
```

**Example prompt:**
```
Add word count display to the chapter editor. Use multi-agent review.
```

### Complex Task (Full Pipeline)
**Best for:** New subsystems, database changes, architectural decisions

```
User → Architect → Developer → Reviewer → [Iterate if needed] → Done
```

**Example prompt:**
```
Design and implement a tagging system for manuscript elements.
This needs architect review for the data model.
```

## How Agents Communicate

### Architect → Developer Handoff
```markdown
## Design Decision
- Context: [what's being built]
- Decision: [architectural approach]
- Patterns to Follow: [from PATTERNS.md]
- Files to Create/Modify: [list]
- Constraints: [limitations]
```

### Developer → Reviewer Handoff
```markdown
## Implementation Summary
- Task: [what was implemented]
- Files Changed: [list]
- Test Results: [pass/fail]
- Areas of Uncertainty: [concerns]
```

### Reviewer → Developer Feedback
```markdown
## Code Review
- Status: [APPROVED | CHANGES REQUESTED]
- Critical Issues: [must fix]
- Important Issues: [should fix]
- Minor Issues: [nice to have]
```

## Configuration

The system is configured in `.claude/multi-agent-config.json`:

```json
{
  "workflow": {
    "simple_task": { "agents": ["developer"], "max_cycles": 1 },
    "standard_task": { "agents": ["developer", "reviewer"], "max_cycles": 2 },
    "complex_task": { "agents": ["architect", "developer", "reviewer"], "max_cycles": 3 }
  }
}
```

## Iteration Limits

| Workflow | Max Cycles | What Happens at Limit |
|----------|------------|----------------------|
| Simple | 1 | Task completes |
| Standard | 2 | Escalate to human if unresolved |
| Complex | 3 | Escalate to human if unresolved |

## Escalation Triggers

The system escalates to human review when:
- Max review cycles exceeded
- Agents have conflicting recommendations
- Security vulnerability detected
- Breaking change to existing API
- Significant deviation from patterns needed

## Agent Prompts

Individual agent prompts are in `.claude/prompts/`:

```
.claude/
├── prompts/
│   ├── architect.md    # Design decision framework
│   ├── developer.md    # Implementation guidelines
│   ├── reviewer.md     # Review criteria
│   └── orchestrator.md # Workflow coordination
└── multi-agent-config.json
```

## Example Session

### User Request
```
Add a feature to track reading time estimates for chapters.
Use the multi-agent workflow.
```

### Orchestrator Classification
```
Complexity: Standard
Reasoning: Feature addition, existing patterns, no schema change
Workflow: Developer → Reviewer
```

### Developer Implementation
```
Files changed:
- backend/app/services/chapter_service.py (added calculate_reading_time)
- backend/app/api/routes/chapters.py (added to response)
- frontend/src/components/Editor/ChapterInfo.tsx (display)

Tests: Passing
```

### Reviewer Feedback
```
Status: APPROVED

What's Good:
- Clean implementation following service pattern
- Good word-per-minute constant (250 WPM)

Minor Suggestions:
- Consider making WPM configurable in future
- Add loading state for large chapters
```

### Result
Feature implemented and approved in 1 cycle.

## Best Practices

1. **Be specific about what you want**
   - Good: "Add user preference for dark mode with persistence"
   - Bad: "Add dark mode"

2. **Mention if you need architect input**
   - "This needs a design decision on where to store preferences"

3. **Let the system iterate**
   - Don't interrupt the workflow unless there's an issue

4. **Trust but verify**
   - Review the final output, especially for complex tasks

5. **Provide feedback**
   - If the system makes poor decisions, note it for improvement

## Customizing the System

### Add New Review Criteria
Edit `.claude/prompts/reviewer.md` to add project-specific checks.

### Change Workflow Thresholds
Modify `.claude/multi-agent-config.json` to adjust when each workflow triggers.

### Add Agent Specialization
Create new prompts in `.claude/prompts/` for specialized review (e.g., security-reviewer.md).

## Troubleshooting

### "Review cycle never completes"
- Check if there's a genuine issue that keeps being found
- Reviewer may be too strict - check review criteria
- Consider escalating to human

### "Architect and reviewer disagree"
- Architect has design authority
- If disagreement persists, human decision needed

### "Simple task getting full review"
- Explicitly mark task as simple: "This is a simple fix, no review needed"
- Check task classification criteria in config

## Related Documentation

- [ARCHITECTURE.md](../ARCHITECTURE.md) - System design
- [PATTERNS.md](../PATTERNS.md) - Code patterns agents enforce
- [WORKFLOW.md](../WORKFLOW.md) - Development workflow

# Maxwell/Codex IDE: API Documentation

**Version**: 1.0.0 (MVP)
**Last Updated**: 2025-12-15
**Base URL**: `http://localhost:8000/api`

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Response Format](#response-format)
4. [Error Handling](#error-handling)
5. [API Endpoints by Module](#api-endpoints-by-module)
6. [OpenAPI Specification](#openapi-specification)
7. [Integration Patterns](#integration-patterns)

---

## Overview

The Maxwell API is a RESTful API that provides access to all manuscript management, knowledge graph, timeline orchestration, and AI generation features. All endpoints return JSON and follow consistent conventions.

### Design Principles

- **RESTful**: Standard HTTP methods (GET, POST, PUT, PATCH, DELETE)
- **Consistent**: Uniform response format across all endpoints
- **Validated**: Input validation using Pydantic (Python) / Joi (TypeScript)
- **Documented**: Auto-generated OpenAPI/Swagger documentation
- **Versioned**: API version in URL path (`/api/v1/...`)

### Technology Stack

- **Backend**: Python 3.11+ with FastAPI
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Validation**: Pydantic models
- **Documentation**: FastAPI auto-docs at `/docs`

---

## Authentication

**MVP**: No authentication (local desktop app)

**Future** (Multi-user cloud version):
```http
Authorization: Bearer <jwt_token>
```

---

## Response Format

### Success Response

```json
{
  "success": true,
  "data": { /* response payload */ },
  "meta": {
    "timestamp": "2025-12-15T10:30:00Z",
    "version": "1.0.0",
    "requestId": "req-uuid-1234"
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "ENTITY_NOT_FOUND",
    "message": "Character with ID char-1234 not found",
    "details": {
      "entityId": "char-1234",
      "entityType": "character"
    },
    "suggestion": "Verify the character ID exists in your Codex"
  },
  "meta": {
    "timestamp": "2025-12-15T10:30:00Z",
    "version": "1.0.0",
    "requestId": "req-uuid-5678"
  }
}
```

### Pagination Format

```json
{
  "success": true,
  "data": {
    "items": [ /* array of results */ ],
    "pagination": {
      "page": 1,
      "perPage": 20,
      "total": 150,
      "totalPages": 8,
      "hasNext": true,
      "hasPrev": false
    }
  }
}
```

---

## Error Handling

### Standard Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `NOT_FOUND` | 404 | Resource not found |
| `ENTITY_NOT_FOUND` | 404 | Specific entity (character, location) not found |
| `CONFLICT` | 409 | Resource already exists |
| `DEPENDENCY_ERROR` | 409 | Cannot delete due to dependencies |
| `TIMELINE_VALIDATION_ERROR` | 422 | Timeline logic violation |
| `INTERNAL_ERROR` | 500 | Server error |
| `LLM_ERROR` | 503 | AI service unavailable |

### Example Error Responses

**Validation Error:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request body",
    "details": {
      "storyDate": ["Invalid date format. Expected ISO 8601"],
      "characterIds": ["Must be array of UUIDs"]
    }
  }
}
```

**Timeline Validation Error:**
```json
{
  "success": false,
  "error": {
    "code": "TIMELINE_VALIDATION_ERROR",
    "message": "Impossible travel detected",
    "details": {
      "issueType": "impossible_travel",
      "severity": "critical",
      "characterId": "char-arya",
      "fromLocation": "King's Landing",
      "toLocation": "Winterfell",
      "distanceKm": 900,
      "daysAvailable": 5,
      "daysRequired": 11
    },
    "suggestion": "Consider: 1) Extend timeline by 6 days, 2) Use faster travel method, 3) Add magic/teleportation explanation"
  }
}
```

---

## API Endpoints by Module

### 1. Manuscript Management

#### Create Manuscript
```http
POST /api/manuscripts
Content-Type: application/json

{
  "title": "The War of Five Kings",
  "genre": "fantasy",
  "targetWordCount": 100000
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "ms-uuid-1234",
    "title": "The War of Five Kings",
    "genre": "fantasy",
    "targetWordCount": 100000,
    "currentWordCount": 0,
    "createdAt": "2025-12-15T10:00:00Z",
    "updatedAt": "2025-12-15T10:00:00Z"
  }
}
```

#### List Manuscripts
```http
GET /api/manuscripts?page=1&perPage=20&sortBy=updatedAt&order=desc
```

#### Get Manuscript
```http
GET /api/manuscripts/{manuscriptId}
```

#### Update Manuscript
```http
PUT /api/manuscripts/{manuscriptId}
Content-Type: application/json

{
  "title": "A Song of Ice and Fire: Book 1",
  "lexicalState": "{ /* Lexical editor state JSON */ }"
}
```

#### Delete Manuscript
```http
DELETE /api/manuscripts/{manuscriptId}
```

---

### 2. Version Control (Time Machine)

#### Get Version History
```http
GET /api/manuscripts/{manuscriptId}/history?limit=50
```

**Response:**
```json
{
  "success": true,
  "data": {
    "snapshots": [
      {
        "id": "snap-uuid-1",
        "manuscriptId": "ms-uuid-1234",
        "gitCommitHash": "abc123def456",
        "label": "Chapter 1 complete",
        "triggerType": "MANUAL",
        "wordCount": 5240,
        "createdAt": "2025-12-15T14:30:00Z"
      },
      {
        "id": "snap-uuid-2",
        "manuscriptId": "ms-uuid-1234",
        "gitCommitHash": "def456abc789",
        "label": "Auto-save",
        "triggerType": "AUTO_SAVE",
        "wordCount": 5180,
        "createdAt": "2025-12-15T14:25:00Z"
      }
    ]
  }
}
```

#### Create Snapshot
```http
POST /api/manuscripts/{manuscriptId}/snapshots
Content-Type: application/json

{
  "label": "Before major revision",
  "triggerType": "MANUAL"
}
```

#### Restore Snapshot
```http
POST /api/snapshots/{snapshotId}/restore
```

#### Get Diff Between Snapshots
```http
GET /api/snapshots/diff?from={snapshotId1}&to={snapshotId2}
```

#### Scene Variants

**Create Variant:**
```http
POST /api/scenes/{sceneId}/variants
Content-Type: application/json

{
  "label": "Alternative ending",
  "content": "{ /* Lexical state */ }"
}
```

**List Variants:**
```http
GET /api/scenes/{sceneId}/variants
```

**Merge Variant to Main:**
```http
PUT /api/variants/{variantId}/merge
```

---

### 3. Codex (Knowledge Graph)

#### Create Entity
```http
POST /api/codex/entities
Content-Type: application/json

{
  "type": "CHARACTER",
  "name": "Arya Stark",
  "aliases": ["Arry", "Cat of the Canals"],
  "attributes": {
    "age": 11,
    "house": "Stark",
    "skills": ["swordfighting", "stealth"],
    "physicalDescription": "Small for her age, lean, brown hair, grey eyes"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "char-uuid-arya",
    "type": "CHARACTER",
    "name": "Arya Stark",
    "aliases": ["Arry", "Cat of the Canals"],
    "attributes": { /* ... */ },
    "createdAt": "2025-12-15T10:00:00Z",
    "updatedAt": "2025-12-15T10:00:00Z"
  }
}
```

#### List Entities
```http
GET /api/codex/entities?type=CHARACTER&search=stark&page=1&perPage=20
```

#### Get Entity
```http
GET /api/codex/entities/{entityId}
```

#### Update Entity
```http
PUT /api/codex/entities/{entityId}
```

#### Delete Entity
```http
DELETE /api/codex/entities/{entityId}
```

#### Get Entity Relationships
```http
GET /api/codex/entities/{entityId}/relationships
```

**Response:**
```json
{
  "success": true,
  "data": {
    "relationships": [
      {
        "id": "rel-uuid-1",
        "sourceEntityId": "char-uuid-arya",
        "targetEntityId": "char-uuid-jon",
        "relationshipType": "SIBLING",
        "strength": 8,
        "context": [
          {
            "sceneId": "scene-uuid-1",
            "description": "Arya says goodbye to Jon at Winterfell"
          }
        ]
      }
    ]
  }
}
```

#### Get Full Knowledge Graph
```http
GET /api/codex/graph?manuscriptId={manuscriptId}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "nodes": [
      {
        "id": "char-uuid-arya",
        "type": "CHARACTER",
        "name": "Arya Stark",
        "attributes": { /* ... */ }
      }
    ],
    "edges": [
      {
        "source": "char-uuid-arya",
        "target": "char-uuid-jon",
        "type": "SIBLING",
        "strength": 8
      }
    ]
  }
}
```

#### Entity Suggestions (NLP-Detected)

**Get Pending Suggestions:**
```http
GET /api/codex/suggestions?manuscriptId={manuscriptId}&status=PENDING
```

**Approve Suggestion:**
```http
POST /api/codex/suggestions/{suggestionId}/approve
```

**Reject Suggestion:**
```http
POST /api/codex/suggestions/{suggestionId}/reject
```

---

### 4. Timeline Orchestrator ⭐ NEW

#### Create Timeline Event
```http
POST /api/timeline/events
Content-Type: application/json

{
  "projectId": "ms-uuid-1234",
  "name": "Robb crowned King in the North",
  "description": "Northern lords declare Robb their king",
  "storyDate": "2024-01-15T00:00:00Z",
  "eventType": "world_event",
  "characterIds": ["char-uuid-robb", "char-uuid-catelyn"],
  "locationId": "loc-uuid-winterfell",
  "prerequisiteIds": [],
  "narrativeImportance": 0.95,
  "notes": "Major turning point in the war"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "evt-uuid-1",
    "projectId": "ms-uuid-1234",
    "name": "Robb crowned King in the North",
    "description": "Northern lords declare Robb their king",
    "storyDate": "2024-01-15T00:00:00Z",
    "eventType": "world_event",
    "characterIds": ["char-uuid-robb", "char-uuid-catelyn"],
    "locationId": "loc-uuid-winterfell",
    "prerequisiteIds": [],
    "narrativeImportance": 0.95,
    "notes": "Major turning point in the war",
    "createdAt": "2025-12-15T10:00:00Z",
    "updatedAt": "2025-12-15T10:00:00Z"
  }
}
```

#### List Timeline Events
```http
GET /api/timeline/events?projectId={projectId}&characterId={characterId}&sortBy=storyDate&order=asc
```

#### Create Location
```http
POST /api/timeline/locations
Content-Type: application/json

{
  "projectId": "ms-uuid-1234",
  "name": "Winterfell",
  "description": "Ancestral seat of House Stark",
  "knownTravelMethods": ["walking", "horse", "carriage"]
}
```

#### Create Travel Leg
```http
POST /api/timeline/travel-legs
Content-Type: application/json

{
  "projectId": "ms-uuid-1234",
  "characterId": "char-uuid-robb",
  "fromLocationId": "loc-uuid-winterfell",
  "toLocationId": "loc-uuid-riverrun",
  "departDate": "2024-01-20T08:00:00Z",
  "arrivalDate": "2024-02-05T18:00:00Z",
  "travelMethod": "horse",
  "estimatedDays": 16,
  "notes": "Took the Kingsroad south, then west to Riverrun"
}
```

#### Validate Timeline
```http
POST /api/timeline/validate
Content-Type: application/json

{
  "projectId": "ms-uuid-1234"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "projectId": "ms-uuid-1234",
    "totalEvents": 47,
    "totalCharacters": 12,
    "validationTime": 342,
    "criticalIssues": 2,
    "majorIssues": 5,
    "minorIssues": 8,
    "issues": [
      {
        "id": "issue-uuid-1",
        "type": "impossible_travel",
        "severity": "critical",
        "character": "Arya Stark",
        "description": "Character appears in two locations 5 days apart. Distance: ~900km. At normal travel speed (80km/day), this requires 11 days.",
        "suggestion": "Options: 1) Extend the timeline by 6 days, 2) Add faster travel method (flying, magic), 3) Explain how character got there quickly, 4) Remove one appearance",
        "teachingPoint": "Fantasy readers subconsciously track travel time and distance. If your character can teleport, readers will wonder why they don't use that method to solve other problems. Either make the travel method consistent or explain the magic rules.",
        "affectedEventIds": ["evt-uuid-42", "evt-uuid-51"]
      },
      {
        "id": "issue-uuid-2",
        "type": "dependency_violation",
        "severity": "critical",
        "description": "Event 'Trial ends' (Day 50) depends on 'Trial begins' (Day 65). But the prerequisite happens AFTER this event.",
        "suggestion": "Reorder these events: the prerequisite must come first",
        "teachingPoint": "Causality is sacred to readers. Cause must precede effect, always. Violating this breaks immersion instantly.",
        "affectedEventIds": ["evt-uuid-33", "evt-uuid-38"]
      }
    ],
    "suggestions": [
      "You have 2 critical timeline issue(s) that break story logic. Fix these first.",
      "Your characters move between locations faster than physically possible 2 times. Consider your world's travel rules or add travel scenes.",
      "5 characters have minimal timeline presence. Consider: are they important to your story?"
    ]
  }
}
```

#### Get Timeline Issues
```http
GET /api/timeline/issues?projectId={projectId}&severity=critical&resolved=false
```

#### Mark Issue Resolved
```http
PATCH /api/timeline/issues/{issueId}
Content-Type: application/json

{
  "isResolved": true,
  "resolutionNotes": "Extended timeline by 7 days to allow realistic travel"
}
```

#### Get/Update Travel Speed Profile
```http
GET /api/timeline/travel-speeds?projectId={projectId}
```

```http
PUT /api/timeline/travel-speeds
Content-Type: application/json

{
  "projectId": "ms-uuid-1234",
  "walking": 40,
  "horse": 80,
  "carriage": 60,
  "sailing": 150,
  "flying": 200,
  "teleportation": 999999,
  "custom1Name": "dragon",
  "custom1Speed": 500,
  "rules": "Dragons need rest every 200km"
}
```

#### Set Location Distance
```http
POST /api/timeline/location-distances
Content-Type: application/json

{
  "projectId": "ms-uuid-1234",
  "fromLocationId": "loc-uuid-winterfell",
  "toLocationId": "loc-uuid-kings-landing",
  "distanceKm": 900,
  "notes": "Via the Kingsroad"
}
```

#### Get Comprehensive Timeline Data
```http
GET /api/timeline/comprehensive?projectId={projectId}
```

**Response:** (All timeline data in one request)
```json
{
  "success": true,
  "data": {
    "events": [ /* all events */ ],
    "locations": [ /* all locations */ ],
    "travelLegs": [ /* all travel legs */ ],
    "issues": [ /* all issues */ ],
    "speedProfile": { /* travel speeds */ },
    "locationDistances": [ /* distance matrix */ ]
  }
}
```

---

### 5. AI Generation (The Muse)

#### Beat Expansion
```http
POST /api/generate/beat-expansion
Content-Type: application/json

{
  "beat": "Arya escapes King's Landing during the chaos",
  "style": "match_manuscript",
  "context": {
    "manuscriptId": "ms-uuid-1234",
    "sceneId": "scene-uuid-42",
    "characterIds": ["char-uuid-arya"],
    "locationId": "loc-uuid-kings-landing"
  },
  "targetLength": 500
}
```

**Response (Streaming via WebSocket):**
```json
{
  "type": "generation_start",
  "requestId": "gen-uuid-1"
}

{
  "type": "token",
  "content": "The"
}

{
  "type": "token",
  "content": " streets"
}

/* ... more tokens ... */

{
  "type": "generation_complete",
  "content": "The streets of King's Landing erupted in chaos...",
  "metadata": {
    "wordCount": 487,
    "modelUsed": "claude-3-5-sonnet",
    "tokensGenerated": 612,
    "inferenceTimeMs": 3450
  }
}
```

#### Rewrite with Style
```http
POST /api/generate/rewrite
Content-Type: application/json

{
  "originalText": "Jon walked to the wall.",
  "styleInstruction": "Make it more descriptive and atmospheric",
  "context": {
    "characterIds": ["char-uuid-jon"],
    "locationId": "loc-uuid-the-wall"
  }
}
```

#### Continue from Cursor
```http
POST /api/generate/continue
Content-Type: application/json

{
  "manuscriptId": "ms-uuid-1234",
  "sceneId": "scene-uuid-42",
  "cursorPosition": 1520,
  "precedingText": "... last 200 chars before cursor ...",
  "targetLength": 300
}
```

---

### 6. The Coach (Learning Agent)

#### Get Feedback
```http
POST /api/coach/analyze
Content-Type: application/json

{
  "manuscriptId": "ms-uuid-1234",
  "sceneId": "scene-uuid-42",
  "analysisType": "comprehensive",
  "includeTimeline": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "feedback": [
      {
        "category": "pacing",
        "severity": "minor",
        "issue": "This scene feels rushed compared to your usual pacing",
        "suggestion": "Consider adding 150-200 words to develop the emotional beat",
        "teachingPoint": "I've noticed you typically spend ~400 words on emotional moments. This one has only 180 words.",
        "learnedPattern": "user_pacing_preference",
        "confidence": 0.85
      },
      {
        "category": "timeline",
        "severity": "critical",
        "issue": "Timeline Orchestrator detected impossible travel",
        "suggestion": "Arya appears 900km away 5 days later. Extend timeline or explain magic travel.",
        "teachingPoint": "Readers track distance subconsciously. Inconsistent travel breaks immersion.",
        "crossReference": {
          "module": "timeline_orchestrator",
          "issueId": "issue-uuid-1"
        }
      }
    ],
    "overallAssessment": "This scene is strong but has one critical timeline issue to address.",
    "writerProfile": {
      "averageSceneLength": 1842,
      "preferredPacing": "moderate",
      "commonPatterns": ["strong_dialogue", "visual_descriptions"],
      "improvementAreas": ["timeline_consistency", "sensory_details"]
    }
  }
}
```

#### Record User Reaction
```http
POST /api/coach/feedback/{feedbackId}/reaction
Content-Type: application/json

{
  "reaction": "helpful",
  "applied": true,
  "notes": "Extended timeline by 7 days"
}
```

#### Get Writer Profile
```http
GET /api/coach/profile?manuscriptId={manuscriptId}
```

---

### 7. Structural Analysis

#### Get Pacing Graph
```http
GET /api/analyze/pacing/{manuscriptId}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "scenes": [
      {
        "sceneId": "scene-uuid-1",
        "position": 0.05,
        "sentiment": 0.3,
        "tension": 0.4,
        "wordCount": 1842
      },
      {
        "sceneId": "scene-uuid-2",
        "position": 0.12,
        "sentiment": -0.2,
        "tension": 0.7,
        "wordCount": 2104
      }
    ],
    "averageSentiment": 0.15,
    "maxTension": 0.95,
    "tensionCurve": "rising_action"
  }
}
```

#### Extract Entities (NLP)
```http
POST /api/analyze/extract-entities
Content-Type: application/json

{
  "manuscriptId": "ms-uuid-1234",
  "sceneId": "scene-uuid-42",
  "text": "Arya Stark walked through the streets of King's Landing..."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "entities": [
      {
        "text": "Arya Stark",
        "type": "PERSON",
        "confidence": 0.95,
        "suggestedCodexId": "char-uuid-arya"
      },
      {
        "text": "King's Landing",
        "type": "LOCATION",
        "confidence": 0.92,
        "suggestedCodexId": "loc-uuid-kings-landing"
      }
    ],
    "relationships": [
      {
        "source": "Arya Stark",
        "target": "King's Landing",
        "type": "LOCATED_IN"
      }
    ]
  }
}
```

#### Check Consistency
```http
GET /api/analyze/consistency?manuscriptId={manuscriptId}
```

---

## OpenAPI Specification

### Complete OpenAPI 3.0 Schema

```yaml
openapi: 3.0.0
info:
  title: Maxwell/Codex IDE API
  version: 1.0.0
  description: |
    RESTful API for Maxwell, a writing IDE with AI assistance, knowledge graphs,
    and timeline orchestration for fiction authors.
  contact:
    name: Maxwell Development Team
    email: dev@maxwell-ide.com

servers:
  - url: http://localhost:8000/api
    description: Local development server
  - url: https://api.maxwell-ide.com/api
    description: Production server (future)

tags:
  - name: Manuscripts
    description: Manuscript CRUD operations
  - name: Versioning
    description: Git-based version control
  - name: Codex
    description: Knowledge graph and entity management
  - name: Timeline
    description: Timeline orchestration and validation
  - name: Generation
    description: AI text generation
  - name: Coach
    description: Learning agent and personalized feedback
  - name: Analysis
    description: Structural analysis and NLP

components:
  schemas:
    Manuscript:
      type: object
      properties:
        id:
          type: string
          format: uuid
          example: ms-uuid-1234
        title:
          type: string
          example: The War of Five Kings
        genre:
          type: string
          example: fantasy
        targetWordCount:
          type: integer
          example: 100000
        currentWordCount:
          type: integer
          example: 25400
        lexicalState:
          type: string
          description: Serialized Lexical editor state (JSON)
        createdAt:
          type: string
          format: date-time
        updatedAt:
          type: string
          format: date-time

    TimelineEvent:
      type: object
      required:
        - projectId
        - name
        - eventType
      properties:
        id:
          type: string
          format: uuid
        projectId:
          type: string
          format: uuid
        name:
          type: string
          example: Robb crowned King in the North
        description:
          type: string
        storyDate:
          type: string
          format: date-time
        eventType:
          type: string
          enum: [character_action, world_event, revelation, travel, meeting]
        characterIds:
          type: array
          items:
            type: string
            format: uuid
        locationId:
          type: string
          format: uuid
        prerequisiteIds:
          type: array
          items:
            type: string
            format: uuid
        narrativeImportance:
          type: number
          minimum: 0
          maximum: 1
          default: 0.5
        notes:
          type: string

    TimelineIssue:
      type: object
      properties:
        id:
          type: string
          format: uuid
        type:
          type: string
          enum: [impossible_travel, dependency_violation, character_presence, timing_gap, paradox]
        severity:
          type: string
          enum: [critical, major, minor]
        character:
          type: string
        location:
          type: string
        description:
          type: string
        suggestion:
          type: string
        teachingPoint:
          type: string
        affectedEventIds:
          type: array
          items:
            type: string
            format: uuid

    ValidationResult:
      type: object
      properties:
        projectId:
          type: string
          format: uuid
        totalEvents:
          type: integer
        totalCharacters:
          type: integer
        validationTime:
          type: integer
          description: Validation time in milliseconds
        criticalIssues:
          type: integer
        majorIssues:
          type: integer
        minorIssues:
          type: integer
        issues:
          type: array
          items:
            $ref: '#/components/schemas/TimelineIssue'
        suggestions:
          type: array
          items:
            type: string

    Entity:
      type: object
      properties:
        id:
          type: string
          format: uuid
        type:
          type: string
          enum: [CHARACTER, LOCATION, ITEM, LORE]
        name:
          type: string
        aliases:
          type: array
          items:
            type: string
        attributes:
          type: object
          additionalProperties: true
        createdAt:
          type: string
          format: date-time
        updatedAt:
          type: string
          format: date-time

    SuccessResponse:
      type: object
      properties:
        success:
          type: boolean
          example: true
        data:
          type: object
        meta:
          type: object
          properties:
            timestamp:
              type: string
              format: date-time
            version:
              type: string
            requestId:
              type: string

    ErrorResponse:
      type: object
      properties:
        success:
          type: boolean
          example: false
        error:
          type: object
          properties:
            code:
              type: string
            message:
              type: string
            details:
              type: object
            suggestion:
              type: string

paths:
  /manuscripts:
    get:
      tags: [Manuscripts]
      summary: List all manuscripts
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: perPage
          in: query
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SuccessResponse'

    post:
      tags: [Manuscripts]
      summary: Create a new manuscript
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [title]
              properties:
                title:
                  type: string
                genre:
                  type: string
                targetWordCount:
                  type: integer
      responses:
        '201':
          description: Manuscript created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SuccessResponse'

  /timeline/validate:
    post:
      tags: [Timeline]
      summary: Validate entire timeline
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [projectId]
              properties:
                projectId:
                  type: string
                  format: uuid
      responses:
        '200':
          description: Validation complete
          content:
            application/json:
              schema:
                allOf:
                  - $ref: '#/components/schemas/SuccessResponse'
                  - type: object
                    properties:
                      data:
                        $ref: '#/components/schemas/ValidationResult'

  /timeline/events:
    get:
      tags: [Timeline]
      summary: List timeline events
      parameters:
        - name: projectId
          in: query
          required: true
          schema:
            type: string
            format: uuid
        - name: characterId
          in: query
          schema:
            type: string
            format: uuid
        - name: sortBy
          in: query
          schema:
            type: string
            enum: [storyDate, createdAt, narrativeImportance]
            default: storyDate
      responses:
        '200':
          description: Events list
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SuccessResponse'

    post:
      tags: [Timeline]
      summary: Create timeline event
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TimelineEvent'
      responses:
        '201':
          description: Event created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SuccessResponse'
```

---

## Integration Patterns

### Pattern 1: Create Event → Validate Timeline

```javascript
// 1. Create a new timeline event
const eventResponse = await fetch('/api/timeline/events', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    projectId: 'ms-uuid-1234',
    name: 'Arya arrives at Vale',
    storyDate: '2024-02-10T00:00:00Z',
    characterIds: ['char-uuid-arya'],
    locationId: 'loc-uuid-vale'
  })
});

// 2. Immediately validate timeline
const validationResponse = await fetch('/api/timeline/validate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    projectId: 'ms-uuid-1234'
  })
});

const validation = await validationResponse.json();

// 3. Display issues to user
if (validation.data.criticalIssues > 0) {
  showTimelineWarning(validation.data.issues);
}
```

### Pattern 2: Codex → Timeline Integration

```javascript
// 1. Create character in Codex
const characterResponse = await fetch('/api/codex/entities', {
  method: 'POST',
  body: JSON.stringify({
    type: 'CHARACTER',
    name: 'Jon Snow'
  })
});

const character = await characterResponse.json();

// 2. Create location in Codex (shared with Timeline)
const locationResponse = await fetch('/api/timeline/locations', {
  method: 'POST',
  body: JSON.stringify({
    projectId: 'ms-uuid-1234',
    name: 'Castle Black'
  })
});

const location = await locationResponse.json();

// 3. Create timeline event using Codex data
await fetch('/api/timeline/events', {
  method: 'POST',
  body: JSON.stringify({
    projectId: 'ms-uuid-1234',
    name: 'Jon takes the black',
    characterIds: [character.data.id],
    locationId: location.data.id,
    storyDate: '2024-01-01T00:00:00Z'
  })
});
```

### Pattern 3: Coach + Timeline Cross-Validation

```javascript
// 1. Get Coach feedback (includes timeline validation)
const coachResponse = await fetch('/api/coach/analyze', {
  method: 'POST',
  body: JSON.stringify({
    manuscriptId: 'ms-uuid-1234',
    sceneId: 'scene-uuid-42',
    includeTimeline: true  // Enable timeline cross-validation
  })
});

const feedback = await coachResponse.json();

// 2. Coach response includes timeline issues
/*
{
  "feedback": [
    {
      "category": "timeline",
      "severity": "critical",
      "issue": "Timeline Orchestrator detected impossible travel",
      "crossReference": {
        "module": "timeline_orchestrator",
        "issueId": "issue-uuid-1"
      }
    }
  ]
}
*/

// 3. User marks timeline issue as resolved
await fetch(`/api/timeline/issues/${issueId}`, {
  method: 'PATCH',
  body: JSON.stringify({
    isResolved: true,
    resolutionNotes: 'Extended timeline'
  })
});

// 4. Record that user found this feedback helpful
await fetch(`/api/coach/feedback/${feedbackId}/reaction`, {
  method: 'POST',
  body: JSON.stringify({
    reaction: 'helpful',
    applied: true
  })
});
```

---

## WebSocket Endpoints

### AI Generation Stream

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/generate');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'beat_expansion',
    beat: 'Arya escapes King\'s Landing',
    context: { manuscriptId: 'ms-uuid-1234' }
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  switch (message.type) {
    case 'generation_start':
      console.log('Generation started:', message.requestId);
      break;

    case 'token':
      // Append token to UI
      appendText(message.content);
      break;

    case 'generation_complete':
      console.log('Complete:', message.content);
      console.log('Metadata:', message.metadata);
      break;

    case 'error':
      console.error('Error:', message.error);
      break;
  }
};
```

---

## Rate Limiting (Future)

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1639584000
```

---

## Testing Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "nlp": "ready",
    "llm": "available"
  }
}
```

### Database Status
```http
GET /debug/db-status
```

---

## Changelog

### Version 1.0.0 (2025-12-15)
- Initial API documentation
- All core endpoints documented
- Timeline Orchestrator API added
- OpenAPI 3.0 schema included
- Integration patterns documented

---

**Next Steps:**
1. Generate Swagger UI documentation
2. Add request/response examples for all endpoints
3. Create Postman collection
4. Add authentication (multi-user version)
5. Implement rate limiting

---

**Maintained By**: Maxwell Development Team
**Last Review**: 2025-12-15

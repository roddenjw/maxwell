# Timeline Orchestrator - API Routes Implementation

## Overview
This guide provides Express routes that expose the Timeline Orchestrator service to the frontend.

## File Creation

**Create**: `backend/src/routes/timeline.ts`

```typescript
import express, { Request, Response } from 'express';
import { PrismaClient } from '@prisma/client';
import { TimelineOrchestratorService } from '../services/analysis/TimelineOrchestratorService';

const router = express.Router();
const prisma = new PrismaClient();
const timelineService = new TimelineOrchestratorService(prisma);

/**
 * POST /api/timeline/validate
 * 
 * Validate a project's entire timeline
 * Returns issues, suggestions, and teaching points
 */
router.post('/validate', async (req: Request, res: Response) => {
  try {
    const { projectId } = req.body;

    if (!projectId) {
      return res.status(400).json({ error: 'projectId is required' });
    }

    const result = await timelineService.validateTimeline(projectId);

    res.json({
      success: true,
      data: result
    });
  } catch (error: any) {
    console.error('Timeline validation failed:', error);
    res.status(500).json({
      error: 'Validation failed',
      message: error.message
    });
  }
});

/**
 * GET /api/timeline/events
 * 
 * Get all timeline events for a project
 * Query params:
 *   - projectId (required): Project to get events from
 *   - characterId (optional): Filter by character
 *   - locationId (optional): Filter by location
 *   - sortBy (optional): 'date' | 'position' | 'name' (default: date)
 */
router.get('/events', async (req: Request, res: Response) => {
  try {
    const { projectId, characterId, locationId, sortBy = 'storyDate' } = req.query;

    if (!projectId || typeof projectId !== 'string') {
      return res.status(400).json({ error: 'projectId query param is required' });
    }

    let where: any = { projectId };

    // Filter by character if provided
    if (characterId && typeof characterId === 'string') {
      where.characterIds = { has: characterId };
    }

    // Filter by location if provided
    if (locationId && typeof locationId === 'string') {
      where.locationId = locationId;
    }

    const events = await prisma.timelineEvent.findMany({
      where,
      include: { location: true },
      orderBy: {
        [sortBy as string]: 'asc'
      }
    });

    res.json({
      success: true,
      count: events.length,
      data: events
    });
  } catch (error: any) {
    console.error('Failed to fetch timeline events:', error);
    res.status(500).json({
      error: 'Failed to fetch events',
      message: error.message
    });
  }
});

/**
 * POST /api/timeline/events
 * 
 * Create a new timeline event
 */
router.post('/events', async (req: Request, res: Response) => {
  try {
    const {
      projectId,
      name,
      description,
      storyDate,
      eventType,
      characterIds = [],
      locationId,
      prerequisiteIds = [],
      narrativeImportance = 0.5,
      notes
    } = req.body;

    if (!projectId || !name || !eventType) {
      return res.status(400).json({
        error: 'projectId, name, and eventType are required'
      });
    }

    // Verify project exists
    const project = await prisma.project.findUnique({
      where: { id: projectId }
    });

    if (!project) {
      return res.status(404).json({ error: 'Project not found' });
    }

    const event = await prisma.timelineEvent.create({
      data: {
        projectId,
        name,
        description,
        storyDate: storyDate ? new Date(storyDate) : null,
        eventType,
        characterIds,
        locationId,
        prerequisiteIds,
        narrativeImportance,
        notes
      },
      include: { location: true }
    });

    res.status(201).json({
      success: true,
      data: event
    });
  } catch (error: any) {
    console.error('Failed to create timeline event:', error);
    res.status(500).json({
      error: 'Failed to create event',
      message: error.message
    });
  }
});

/**
 * PATCH /api/timeline/events/:id
 * 
 * Update an existing timeline event
 */
router.patch('/events/:id', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const updates = req.body;

    // Convert date string to Date if needed
    if (updates.storyDate && typeof updates.storyDate === 'string') {
      updates.storyDate = new Date(updates.storyDate);
    }

    const event = await prisma.timelineEvent.update({
      where: { id },
      data: updates,
      include: { location: true }
    });

    res.json({
      success: true,
      data: event
    });
  } catch (error: any) {
    console.error('Failed to update timeline event:', error);

    if (error.code === 'P2025') {
      return res.status(404).json({ error: 'Event not found' });
    }

    res.status(500).json({
      error: 'Failed to update event',
      message: error.message
    });
  }
});

/**
 * DELETE /api/timeline/events/:id
 * 
 * Delete a timeline event
 */
router.delete('/events/:id', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;

    await prisma.timelineEvent.delete({
      where: { id }
    });

    res.json({
      success: true,
      message: 'Event deleted'
    });
  } catch (error: any) {
    console.error('Failed to delete timeline event:', error);

    if (error.code === 'P2025') {
      return res.status(404).json({ error: 'Event not found' });
    }

    res.status(500).json({
      error: 'Failed to delete event',
      message: error.message
    });
  }
});

/**
 * GET /api/timeline/locations
 * 
 * Get all locations in a project
 */
router.get('/locations', async (req: Request, res: Response) => {
  try {
    const { projectId } = req.query;

    if (!projectId || typeof projectId !== 'string') {
      return res.status(400).json({ error: 'projectId query param is required' });
    }

    const locations = await prisma.location.findMany({
      where: { projectId },
      include: {
        timelineEvents: { select: { id: true, name: true } },
        _count: { select: { timelineEvents: true } }
      }
    });

    res.json({
      success: true,
      count: locations.length,
      data: locations
    });
  } catch (error: any) {
    console.error('Failed to fetch locations:', error);
    res.status(500).json({
      error: 'Failed to fetch locations',
      message: error.message
    });
  }
});

/**
 * POST /api/timeline/locations
 * 
 * Create a new location
 */
router.post('/locations', async (req: Request, res: Response) => {
  try {
    const {
      projectId,
      name,
      description,
      travelDistanceKm,
      knownTravelMethods = []
    } = req.body;

    if (!projectId || !name) {
      return res.status(400).json({
        error: 'projectId and name are required'
      });
    }

    const location = await prisma.location.create({
      data: {
        projectId,
        name,
        description,
        travelDistanceKm,
        knownTravelMethods
      }
    });

    res.status(201).json({
      success: true,
      data: location
    });
  } catch (error: any) {
    console.error('Failed to create location:', error);
    res.status(500).json({
      error: 'Failed to create location',
      message: error.message
    });
  }
});

/**
 * GET /api/timeline/travel-legs
 * 
 * Get all travel records
 * Query params:
 *   - projectId (required)
 *   - characterId (optional): Filter by character
 */
router.get('/travel-legs', async (req: Request, res: Response) => {
  try {
    const { projectId, characterId } = req.query;

    if (!projectId || typeof projectId !== 'string') {
      return res.status(400).json({ error: 'projectId query param is required' });
    }

    let where: any = { projectId };

    if (characterId && typeof characterId === 'string') {
      where.characterId = characterId;
    }

    const travels = await prisma.travelLeg.findMany({
      where,
      include: {
        character: { select: { id: true, name: true } },
        fromLocation: { select: { id: true, name: true } },
        toLocation: { select: { id: true, name: true } }
      },
      orderBy: { departDate: 'asc' }
    });

    res.json({
      success: true,
      count: travels.length,
      data: travels
    });
  } catch (error: any) {
    console.error('Failed to fetch travel legs:', error);
    res.status(500).json({
      error: 'Failed to fetch travel legs',
      message: error.message
    });
  }
});

/**
 * POST /api/timeline/travel-legs
 * 
 * Create a new travel record
 */
router.post('/travel-legs', async (req: Request, res: Response) => {
  try {
    const {
      projectId,
      characterId,
      fromLocationId,
      toLocationId,
      departDate,
      arrivalDate,
      travelMethod,
      estimatedDays,
      notes
    } = req.body;

    if (
      !projectId ||
      !characterId ||
      !fromLocationId ||
      !toLocationId ||
      !departDate ||
      !travelMethod
    ) {
      return res.status(400).json({
        error:
          'projectId, characterId, fromLocationId, toLocationId, departDate, and travelMethod are required'
      });
    }

    const travel = await prisma.travelLeg.create({
      data: {
        projectId,
        characterId,
        fromLocationId,
        toLocationId,
        departDate: new Date(departDate),
        arrivalDate: arrivalDate ? new Date(arrivalDate) : null,
        travelMethod,
        estimatedDays,
        notes
      },
      include: {
        character: { select: { id: true, name: true } },
        fromLocation: { select: { id: true, name: true } },
        toLocation: { select: { id: true, name: true } }
      }
    });

    res.status(201).json({
      success: true,
      data: travel
    });
  } catch (error: any) {
    console.error('Failed to create travel leg:', error);
    res.status(500).json({
      error: 'Failed to create travel leg',
      message: error.message
    });
  }
});

/**
 * GET /api/timeline/issues
 * 
 * Get timeline issues for a project
 * Query params:
 *   - projectId (required)
 *   - severity (optional): 'critical' | 'major' | 'minor'
 *   - resolved (optional): true | false
 */
router.get('/issues', async (req: Request, res: Response) => {
  try {
    const { projectId, severity, resolved } = req.query;

    if (!projectId || typeof projectId !== 'string') {
      return res.status(400).json({ error: 'projectId query param is required' });
    }

    let where: any = { projectId };

    if (severity) {
      where.severity = severity;
    }

    if (resolved !== undefined) {
      where.isResolved = resolved === 'true';
    }

    const issues = await prisma.timelineIssue.findMany({
      where,
      orderBy: { createdAt: 'desc' }
    });

    res.json({
      success: true,
      count: issues.length,
      data: issues
    });
  } catch (error: any) {
    console.error('Failed to fetch timeline issues:', error);
    res.status(500).json({
      error: 'Failed to fetch issues',
      message: error.message
    });
  }
});

/**
 * PATCH /api/timeline/issues/:id
 * 
 * Resolve an issue or add resolution notes
 */
router.patch('/issues/:id', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const { isResolved, resolutionNotes } = req.body;

    const issue = await prisma.timelineIssue.update({
      where: { id },
      data: {
        ...(isResolved !== undefined && { isResolved }),
        ...(resolutionNotes && { resolutionNotes })
      }
    });

    res.json({
      success: true,
      data: issue
    });
  } catch (error: any) {
    console.error('Failed to update timeline issue:', error);

    if (error.code === 'P2025') {
      return res.status(404).json({ error: 'Issue not found' });
    }

    res.status(500).json({
      error: 'Failed to update issue',
      message: error.message
    });
  }
});

/**
 * GET /api/timeline/travel-speeds
 * 
 * Get the project's travel speed profile
 */
router.get('/travel-speeds', async (req: Request, res: Response) => {
  try {
    const { projectId } = req.query;

    if (!projectId || typeof projectId !== 'string') {
      return res.status(400).json({ error: 'projectId query param is required' });
    }

    let profile = await prisma.travelSpeedProfile.findFirst({
      where: { projectId }
    });

    // If no profile exists, return defaults
    if (!profile) {
      profile = {
        id: '',
        projectId: projectId as string,
        walking: 40,
        horse: 80,
        carriage: 60,
        sailing: 150,
        flying: 200,
        teleportation: 999999,
        custom1Name: null,
        custom1Speed: null,
        custom2Name: null,
        custom2Speed: null,
        rules: null,
        createdAt: new Date(),
        updatedAt: new Date()
      };
    }

    res.json({
      success: true,
      data: profile
    });
  } catch (error: any) {
    console.error('Failed to fetch travel speeds:', error);
    res.status(500).json({
      error: 'Failed to fetch travel speeds',
      message: error.message
    });
  }
});

/**
 * PUT /api/timeline/travel-speeds
 * 
 * Update or create the project's travel speed profile
 */
router.put('/travel-speeds', async (req: Request, res: Response) => {
  try {
    const {
      projectId,
      walking,
      horse,
      carriage,
      sailing,
      flying,
      teleportation,
      custom1Name,
      custom1Speed,
      custom2Name,
      custom2Speed,
      rules
    } = req.body;

    if (!projectId) {
      return res.status(400).json({ error: 'projectId is required' });
    }

    const profile = await prisma.travelSpeedProfile.upsert({
      where: { projectId },
      update: {
        ...(walking !== undefined && { walking }),
        ...(horse !== undefined && { horse }),
        ...(carriage !== undefined && { carriage }),
        ...(sailing !== undefined && { sailing }),
        ...(flying !== undefined && { flying }),
        ...(teleportation !== undefined && { teleportation }),
        ...(custom1Name && { custom1Name }),
        ...(custom1Speed !== undefined && { custom1Speed }),
        ...(custom2Name && { custom2Name }),
        ...(custom2Speed !== undefined && { custom2Speed }),
        ...(rules && { rules })
      },
      create: {
        projectId,
        walking: walking ?? 40,
        horse: horse ?? 80,
        carriage: carriage ?? 60,
        sailing: sailing ?? 150,
        flying: flying ?? 200,
        teleportation: teleportation ?? 999999,
        custom1Name,
        custom1Speed,
        custom2Name,
        custom2Speed,
        rules
      }
    });

    res.json({
      success: true,
      data: profile
    });
  } catch (error: any) {
    console.error('Failed to update travel speeds:', error);
    res.status(500).json({
      error: 'Failed to update travel speeds',
      message: error.message
    });
  }
});

/**
 * POST /api/timeline/location-distances
 * 
 * Create or update distance between two locations
 */
router.post('/location-distances', async (req: Request, res: Response) => {
  try {
    const {
      projectId,
      fromLocationId,
      toLocationId,
      distanceKm,
      notes
    } = req.body;

    if (!projectId || !fromLocationId || !toLocationId || !distanceKm) {
      return res.status(400).json({
        error: 'projectId, fromLocationId, toLocationId, and distanceKm are required'
      });
    }

    const distance = await prisma.locationDistance.upsert({
      where: {
        projectId_fromLocationId_toLocationId: {
          projectId,
          fromLocationId,
          toLocationId
        }
      },
      update: {
        distanceKm,
        notes
      },
      create: {
        projectId,
        fromLocationId,
        toLocationId,
        distanceKm,
        notes
      }
    });

    res.json({
      success: true,
      data: distance
    });
  } catch (error: any) {
    console.error('Failed to create location distance:', error);
    res.status(500).json({
      error: 'Failed to create location distance',
      message: error.message
    });
  }
});

/**
 * GET /api/timeline/comprehensive
 * 
 * Get complete timeline data for visualization
 * Returns events, locations, travels, characters, issues, all at once
 */
router.get('/comprehensive', async (req: Request, res: Response) => {
  try {
    const { projectId } = req.query;

    if (!projectId || typeof projectId !== 'string') {
      return res.status(400).json({ error: 'projectId query param is required' });
    }

    const [events, locations, travels, issues, characters, speedProfile] =
      await Promise.all([
        prisma.timelineEvent.findMany({
          where: { projectId },
          include: { location: true }
        }),
        prisma.location.findMany({ where: { projectId } }),
        prisma.travelLeg.findMany({
          where: { projectId },
          include: {
            character: { select: { id: true, name: true } },
            fromLocation: { select: { id: true, name: true } },
            toLocation: { select: { id: true, name: true } }
          }
        }),
        prisma.timelineIssue.findMany({
          where: { projectId, isResolved: false }
        }),
        prisma.character.findMany({ where: { projectId } }),
        prisma.travelSpeedProfile.findFirst({ where: { projectId } })
      ]);

    res.json({
      success: true,
      data: {
        events,
        locations,
        travels,
        issues,
        characters,
        speedProfile,
        summary: {
          totalEvents: events.length,
          totalLocations: locations.length,
          totalTravelLegs: travels.length,
          unresolvedIssues: issues.length,
          criticalIssues: issues.filter(i => i.severity === 'critical').length,
          majorIssues: issues.filter(i => i.severity === 'major').length
        }
      }
    });
  } catch (error: any) {
    console.error('Failed to fetch comprehensive timeline:', error);
    res.status(500).json({
      error: 'Failed to fetch timeline data',
      message: error.message
    });
  }
});

export default router;
```

## Integration

### Add route to main routes file

**File**: `backend/src/routes/index.ts`

```typescript
import express from 'express';
import projectRoutes from './projects';
import aiRoutes from './ai';
import manuscriptRoutes from './manuscripts';
import novelSkeletonRoutes from './novelSkeleton';
import analysisRoutes from './analysis';
import timelineRoutes from './timeline';  // ADD THIS

const router = express.Router();

router.use('/projects', projectRoutes);
router.use('/ai', aiRoutes);
router.use('/manuscripts', manuscriptRoutes);
router.use('/novel-skeleton', novelSkeletonRoutes);
router.use('/analysis', analysisRoutes);
router.use('/timeline', timelineRoutes);  // ADD THIS

export default router;
```

## API Endpoint Summary

### Timeline Events
- `POST /api/timeline/validate` - Validate entire timeline
- `GET /api/timeline/events` - List events (with filters)
- `POST /api/timeline/events` - Create event
- `PATCH /api/timeline/events/:id` - Update event
- `DELETE /api/timeline/events/:id` - Delete event

### Locations
- `GET /api/timeline/locations` - List locations
- `POST /api/timeline/locations` - Create location

### Travel
- `GET /api/timeline/travel-legs` - List travel records
- `POST /api/timeline/travel-legs` - Create travel record
- `GET /api/timeline/travel-speeds` - Get speed profile
- `PUT /api/timeline/travel-speeds` - Update speed profile
- `POST /api/timeline/location-distances` - Set distance

### Issues
- `GET /api/timeline/issues` - List issues (with filters)
- `PATCH /api/timeline/issues/:id` - Resolve issue

### Data Fetching
- `GET /api/timeline/comprehensive` - Get everything at once (for visualization)

## Example Usage

### Validate Timeline
```bash
curl -X POST http://localhost:3001/api/timeline/validate \
  -H "Content-Type: application/json" \
  -d '{"projectId": "project-123"}'
```

Response:
```json
{
  "success": true,
  "data": {
    "projectId": "project-123",
    "totalEvents": 12,
    "totalCharacters": 5,
    "issues": [
      {
        "id": "issue-001",
        "type": "impossible_travel",
        "severity": "critical",
        "character": "Arya",
        "description": "Character appears in two locations 25 days apart. Distance: ~900km...",
        "suggestion": "Options: 1) Extend timeline, 2) Add faster travel...",
        "teachingPoint": "Fantasy readers subconsciously track travel..."
      }
    ],
    "suggestions": [
      "You have 1 critical timeline issue(s)..."
    ]
  }
}
```

### Get Comprehensive Timeline Data
```bash
curl http://localhost:3001/api/timeline/comprehensive?projectId=project-123
```

Returns all events, locations, travels, issues, etc. in one call (perfect for visualizations).

## Error Handling

All endpoints return consistent error format:

```json
{
  "error": "Error title",
  "message": "Detailed error message"
}
```

Common status codes:
- `200` - Success
- `201` - Created
- `400` - Bad request (missing params)
- `404` - Not found (invalid ID)
- `500` - Server error

## Next Steps

1. Build the React components to visualize this data (see 04-FRONTEND-COMPONENTS.md)
2. Add authentication middleware
3. Add request validation middleware
4. Write integration tests
5. Add rate limiting for heavy endpoints

## Summary

You now have complete REST API for timeline management:
- ✅ Create/read/update/delete all timeline entities
- ✅ Validate entire timeline with comprehensive validation service
- ✅ Fetch data in various shapes (single events, comprehensive view)
- ✅ Consistent error handling
- ✅ Well-documented endpoints

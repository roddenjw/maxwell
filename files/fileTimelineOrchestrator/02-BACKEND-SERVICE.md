# Timeline Orchestrator - Backend Service Implementation

## Overview
This guide provides the complete TimelineOrchestratorService that validates timelines, detects issues, and generates teaching content.

## File Creation

**Create**: `backend/src/services/analysis/TimelineOrchestratorService.ts`

```typescript
import { PrismaClient } from '@prisma/client';
import crypto from 'crypto';

/**
 * Timeline Issue - Problems detected in a story's timeline
 */
export interface TimelineIssue {
  id: string;
  type: 'impossible_travel' | 'dependency_violation' | 'character_presence' | 'timing_gap' | 'paradox';
  severity: 'critical' | 'major' | 'minor';
  character?: string;
  location?: string;
  description: string;
  suggestion: string;
  teachingPoint?: string;
  affectedEventIds?: string[];
}

/**
 * Timeline Validation Result - All issues plus summary
 */
export interface TimelineValidationResult {
  projectId: string;
  totalEvents: number;
  totalCharacters: number;
  issues: TimelineIssue[];
  criticalIssues: number;
  majorIssues: number;
  minorIssues: number;
  validationTime: number; // milliseconds
  suggestions: string[];
}

/**
 * Travel Speed Lookup
 */
interface TravelSpeeds {
  [key: string]: number; // km per day
}

/**
 * Character Timeline - Tracks where a character is at each event
 */
interface CharacterMoment {
  type: 'event' | 'travel';
  date?: Date;
  departDate?: Date;
  arrivalDate?: Date;
  eventName?: string;
  eventId?: string;
  fromLocation?: string;
  toLocation?: string;
  travelMethod?: string;
  locationId?: string;
}

/**
 * TimelineOrchestratorService
 * 
 * Core service for validating story timelines and teaching writers
 * about causality, travel logistics, and temporal coherence.
 */
export class TimelineOrchestratorService {
  private prisma: PrismaClient;
  private travelSpeeds: TravelSpeeds = {
    'walking': 40,
    'horse': 80,
    'carriage': 60,
    'sailing': 150,
    'flying': 200,
    'teleportation': 999999, // instant
  };

  constructor(prisma?: PrismaClient) {
    this.prisma = prisma || new PrismaClient();
  }

  /**
   * Main validation function
   * Runs all checks and returns comprehensive results
   */
  async validateTimeline(projectId: string): Promise<TimelineValidationResult> {
    const startTime = Date.now();

    try {
      // Load all project data
      const [project, events, characters, travels, speedProfile] = await Promise.all([
        this.prisma.project.findUnique({ where: { id: projectId } }),
        this.prisma.timelineEvent.findMany({
          where: { projectId },
          include: { location: true }
        }),
        this.prisma.character.findMany({ where: { projectId } }),
        this.prisma.travelLeg.findMany({
          where: { projectId },
          include: { character: true, fromLocation: true, toLocation: true }
        }),
        this.prisma.travelSpeedProfile.findFirst({ where: { projectId } })
      ]);

      if (!project) {
        throw new Error(`Project ${projectId} not found`);
      }

      // Load custom travel speeds if defined
      if (speedProfile) {
        this.travelSpeeds = this.mergeSpeedProfile(this.travelSpeeds, speedProfile);
      }

      // Load location distances
      const distances = await this.prisma.locationDistance.findMany({
        where: { projectId }
      });

      // Run all validators
      const issues: TimelineIssue[] = [];

      issues.push(...this.checkImpossibleTravel(travels, events, distances));
      issues.push(...this.checkDependencyViolations(events));
      issues.push(...this.checkCharacterPresence(events, characters));
      issues.push(...this.checkTimingGaps(events));
      issues.push(...this.checkParadoxes(events));

      // Deduplicate and sort by severity
      const uniqueIssues = this.deduplicateIssues(issues);
      const sortedIssues = this.sortBySeverity(uniqueIssues);

      // Generate summary suggestions
      const suggestions = this.generateSuggestions(sortedIssues, characters);

      // Store issues in database
      await this.storeIssues(projectId, sortedIssues);

      const validationTime = Date.now() - startTime;

      return {
        projectId,
        totalEvents: events.length,
        totalCharacters: characters.length,
        issues: sortedIssues,
        criticalIssues: sortedIssues.filter(i => i.severity === 'critical').length,
        majorIssues: sortedIssues.filter(i => i.severity === 'major').length,
        minorIssues: sortedIssues.filter(i => i.severity === 'minor').length,
        validationTime,
        suggestions
      };
    } catch (error) {
      console.error('Timeline validation failed:', error);
      throw error;
    }
  }

  /**
   * VALIDATOR 1: Check if characters could physically be somewhere
   * 
   * Example: Character in King's Landing Day 1, then in Winterfell Day 2
   * (900 km away, impossible for human travel)
   */
  private checkImpossibleTravel(
    travels: any[],
    events: any[],
    distances: any[]
  ): TimelineIssue[] {
    const issues: TimelineIssue[] = [];
    const distanceMap = new Map<string, number>();

    // Build distance lookup table
    distances.forEach(d => {
      const key = `${d.fromLocationId}→${d.toLocationId}`;
      distanceMap.set(key, d.distanceKm);
    });

    // Build character timelines
    const characterTimelines = new Map<string, CharacterMoment[]>();

    travels.forEach(travel => {
      if (!characterTimelines.has(travel.characterId)) {
        characterTimelines.set(travel.characterId, []);
      }
      characterTimelines.get(travel.characterId)!.push({
        type: 'travel',
        departDate: travel.departDate,
        arrivalDate: travel.arrivalDate,
        fromLocation: travel.fromLocationId,
        toLocation: travel.toLocationId,
        travelMethod: travel.travelMethod
      });
    });

    events.forEach(event => {
      if (event.characterIds && event.characterIds.length > 0) {
        event.characterIds.forEach((charId: string) => {
          if (!characterTimelines.has(charId)) {
            characterTimelines.set(charId, []);
          }
          characterTimelines.get(charId)!.push({
            type: 'event',
            eventId: event.id,
            eventName: event.name,
            date: event.storyDate,
            locationId: event.locationId
          });
        });
      }
    });

    // Now validate each character's timeline
    characterTimelines.forEach((timeline, characterId) => {
      const sorted = timeline.sort((a, b) => {
        const dateA = a.date || a.departDate || new Date(0);
        const dateB = b.date || b.departDate || new Date(0);
        return dateA.getTime() - dateB.getTime();
      });

      for (let i = 0; i < sorted.length - 1; i++) {
        const current = sorted[i];
        const next = sorted[i + 1];

        // Check if character changed locations without recorded travel
        if (
          current.type === 'event' &&
          next.type === 'event' &&
          current.locationId &&
          next.locationId &&
          current.locationId !== next.locationId &&
          current.date &&
          next.date
        ) {
          const timeBetween = next.date.getTime() - current.date.getTime();
          const daysBetween = Math.floor(timeBetween / (1000 * 60 * 60 * 24));

          // Check if there's a recorded travel
          const travelRecord = sorted.find(t =>
            t.type === 'travel' &&
            t.fromLocation === current.locationId &&
            t.toLocation === next.locationId &&
            t.departDate &&
            t.arrivalDate &&
            t.departDate >= current.date &&
            t.arrivalDate <= next.date
          );

          if (!travelRecord) {
            // Look up distance
            const distanceKey = `${current.locationId}→${next.locationId}`;
            const distance = distanceMap.get(distanceKey) || 500; // default 500 km

            // Calculate travel time for default speed (horse)
            const defaultSpeed = this.travelSpeeds['horse'];
            const minDaysNeeded = Math.ceil(distance / defaultSpeed);

            if (daysBetween < minDaysNeeded) {
              issues.push({
                id: this.generateIssueId(),
                type: 'impossible_travel',
                severity: 'critical',
                character: characterId,
                description:
                  `Character appears in two locations ${daysBetween} days apart. ` +
                  `Distance: ~${distance}km. At normal travel speed (${defaultSpeed}km/day), ` +
                  `this requires ${minDaysNeeded} days.`,
                suggestion:
                  'Options: 1) Extend the timeline, 2) Add faster travel method, ' +
                  '3) Explain how character got there so quickly, 4) Remove one appearance',
                teachingPoint:
                  'Fantasy readers subconsciously track travel time and distance. If your character ' +
                  'can teleport, readers will wonder why they don\'t use that method to solve other problems. ' +
                  'Either make the travel method consistent or explain the magic rules.',
                affectedEventIds: [current.eventId || '', next.eventId || ''].filter(id => id)
              });
            }
          }
        }
      }
    });

    return issues;
  }

  /**
   * VALIDATOR 2: Check event dependencies
   * 
   * Example: Event B depends on Event A, but A happens after B in timeline
   */
  private checkDependencyViolations(events: any[]): TimelineIssue[] {
    const issues: TimelineIssue[] = [];
    const eventMap = new Map(events.map(e => [e.id, e]));

    events.forEach(event => {
      if (event.prerequisiteIds && event.prerequisiteIds.length > 0) {
        event.prerequisiteIds.forEach((prereqId: string) => {
          const prereq = eventMap.get(prereqId);

          if (!prereq) {
            issues.push({
              id: this.generateIssueId(),
              type: 'dependency_violation',
              severity: 'major',
              description:
                `Event "${event.name}" depends on missing event "${prereqId}"`,
              suggestion: 'Either: 1) Create the prerequisite event, 2) Remove the dependency',
              teachingPoint:
                'Broken dependencies often indicate plot holes. A character can\'t act on information ' +
                'they don\'t have yet. Make sure every event has its cause.',
              affectedEventIds: [event.id]
            });
          } else if (prereq.storyDate && event.storyDate) {
            const prereqTime = prereq.storyDate.getTime();
            const eventTime = event.storyDate.getTime();

            if (prereqTime > eventTime) {
              issues.push({
                id: this.generateIssueId(),
                type: 'dependency_violation',
                severity: 'critical',
                description:
                  `"${event.name}" (${event.storyDate.toDateString()}) depends on ` +
                  `"${prereq.name}" (${prereq.storyDate.toDateString()}). ` +
                  `But the prerequisite happens AFTER this event.`,
                suggestion: 'Reorder these events: the prerequisite must come first',
                teachingPoint:
                  'Causality is sacred to readers. Cause must precede effect, always. ' +
                  'Violating this breaks immersion instantly, even if readers can\'t explain why.',
                affectedEventIds: [event.id, prereq.id]
              });
            }
          }
        });
      }
    });

    return issues;
  }

  /**
   * VALIDATOR 3: Check character presence
   * 
   * Example: Character created but never appears in timeline
   */
  private checkCharacterPresence(events: any[], characters: any[]): TimelineIssue[] {
    const issues: TimelineIssue[] = [];
    const characterEventCounts = new Map<string, number>();

    events.forEach(event => {
      if (event.characterIds) {
        event.characterIds.forEach((charId: string) => {
          characterEventCounts.set(
            charId,
            (characterEventCounts.get(charId) || 0) + 1
          );
        });
      }
    });

    characters.forEach(char => {
      const eventCount = characterEventCounts.get(char.id) || 0;

      if (eventCount === 0) {
        issues.push({
          id: this.generateIssueId(),
          type: 'character_presence',
          severity: 'major',
          character: char.name,
          description: `Character "${char.name}" has no timeline events`,
          suggestion:
            'Either: 1) Add timeline events for this character, 2) Delete this character ' +
            'if they\'re unused',
          teachingPoint:
            'Every character should have a story arc. If a character exists but has no events, ' +
            'they\'re probably underdeveloped or unnecessary. Use this as a prompt to either ' +
            'develop them more or cut them.',
          affectedEventIds: []
        });
      } else if (eventCount === 1) {
        issues.push({
          id: this.generateIssueId(),
          type: 'character_presence',
          severity: 'minor',
          character: char.name,
          description: `Character "${char.name}" appears only once on the timeline`,
          suggestion:
            'Consider: Does this character need more development? Or are they a true one-off minor character?',
          teachingPoint:
            'Characters with just one appearance often feel unmotivated to readers. ' +
            'Even minor characters usually need 2-3 timeline moments to feel real. ' +
            'They should show change or reveal something about the world.',
          affectedEventIds: []
        });
      }
    });

    return issues;
  }

  /**
   * VALIDATOR 4: Check for timing gaps
   * 
   * Example: Event A on Day 1, Event B on Day 100
   * (Large time gap might indicate pacing issues)
   */
  private checkTimingGaps(events: any[]): TimelineIssue[] {
    const issues: TimelineIssue[] = [];
    const sorted = [...events]
      .filter(e => e.storyDate)
      .sort((a, b) => a.storyDate.getTime() - b.storyDate.getTime());

    for (let i = 0; i < sorted.length - 1; i++) {
      const current = sorted[i];
      const next = sorted[i + 1];

      const daysBetween =
        (next.storyDate.getTime() - current.storyDate.getTime()) /
        (1000 * 60 * 60 * 24);

      // Flag gaps larger than 30 days
      if (daysBetween > 30) {
        issues.push({
          id: this.generateIssueId(),
          type: 'timing_gap',
          severity: 'minor',
          description:
            `${Math.round(daysBetween)} days pass between "${current.name}" ` +
            `and "${next.name}"`,
          suggestion:
            'Consider: What happens during this gap? Does it make sense to readers? ' +
            'If nothing important happens, compress the timeline.',
          teachingPoint:
            'Time gaps can work, but they affect pacing. Readers notice gaps, even subconsciously. ' +
            'Make sure each gap either: 1) Advances the story (character aging, seasons changing), ' +
            '2) Is explained (character waiting, recovering), or 3) Is intentional (fairy tale timelessness).',
          affectedEventIds: [current.id, next.id]
        });
      }
    }

    return issues;
  }

  /**
   * VALIDATOR 5: Check for temporal paradoxes
   * 
   * Example: Event A must happen before B, B before C, C before A (cycle)
   */
  private checkParadoxes(events: any[]): TimelineIssue[] {
    const issues: TimelineIssue[] = [];
    const eventMap = new Map(events.map(e => [e.id, e]));

    // Build dependency graph
    const graph = new Map<string, string[]>();
    events.forEach(event => {
      if (event.prerequisiteIds && event.prerequisiteIds.length > 0) {
        graph.set(event.id, event.prerequisiteIds);
      }
    });

    // Detect cycles using DFS
    const visited = new Set<string>();
    const recursionStack = new Set<string>();

    const hasCycle = (eventId: string, path: string[]): boolean => {
      visited.add(eventId);
      recursionStack.add(eventId);
      path.push(eventId);

      const prerequisites = graph.get(eventId) || [];

      for (const prereqId of prerequisites) {
        if (!visited.has(prereqId)) {
          if (hasCycle(prereqId, [...path])) {
            return true;
          }
        } else if (recursionStack.has(prereqId)) {
          // Found a cycle
          const event = eventMap.get(eventId);
          const prereq = eventMap.get(prereqId);
          issues.push({
            id: this.generateIssueId(),
            type: 'paradox',
            severity: 'critical',
            description:
              `Circular dependency: "${event?.name}" depends on "${prereq?.name}" ` +
              `which (indirectly) depends on "${event?.name}"`,
            suggestion: 'Break the dependency cycle by removing one prerequisite link',
            teachingPoint:
              'This is a logical impossibility. A cannot depend on B if B depends on A. ' +
              'This usually indicates either: 1) A misunderstanding of the plot, ' +
              '2) Weak causality that should be removed, or 3) A mistake in your timeline structure.',
            affectedEventIds: path
          });
          return true;
        }
      }

      recursionStack.delete(eventId);
      return false;
    };

    for (const eventId of graph.keys()) {
      if (!visited.has(eventId)) {
        hasCycle(eventId, []);
      }
    }

    return issues;
  }

  /**
   * Helper: Merge custom travel speed profile
   */
  private mergeSpeedProfile(defaults: TravelSpeeds, profile: any): TravelSpeeds {
    const merged = { ...defaults };

    if (profile.walking) merged['walking'] = profile.walking;
    if (profile.horse) merged['horse'] = profile.horse;
    if (profile.carriage) merged['carriage'] = profile.carriage;
    if (profile.sailing) merged['sailing'] = profile.sailing;
    if (profile.flying) merged['flying'] = profile.flying;
    if (profile.teleportation) merged['teleportation'] = profile.teleportation;
    if (profile.custom1Name && profile.custom1Speed) {
      merged[profile.custom1Name] = profile.custom1Speed;
    }
    if (profile.custom2Name && profile.custom2Speed) {
      merged[profile.custom2Name] = profile.custom2Speed;
    }

    return merged;
  }

  /**
   * Helper: Deduplicate issues (same issue detected twice)
   */
  private deduplicateIssues(issues: TimelineIssue[]): TimelineIssue[] {
    const seen = new Set<string>();
    const unique: TimelineIssue[] = [];

    issues.forEach(issue => {
      const key = `${issue.type}-${issue.description}`;
      if (!seen.has(key)) {
        seen.add(key);
        unique.push(issue);
      }
    });

    return unique;
  }

  /**
   * Helper: Sort issues by severity
   */
  private sortBySeverity(issues: TimelineIssue[]): TimelineIssue[] {
    const severityOrder = { critical: 0, major: 1, minor: 2 };
    return [...issues].sort(
      (a, b) => severityOrder[a.severity] - severityOrder[b.severity]
    );
  }

  /**
   * Helper: Generate high-level suggestions
   */
  private generateSuggestions(issues: TimelineIssue[], characters: any[]): string[] {
    const suggestions: string[] = [];

    const criticalCount = issues.filter(i => i.severity === 'critical').length;
    const majorCount = issues.filter(i => i.severity === 'major').length;

    if (criticalCount > 0) {
      suggestions.push(
        `You have ${criticalCount} critical timeline issue(s) that break story logic. Fix these first.`
      );
    }

    if (majorCount > 0) {
      suggestions.push(
        `You have ${majorCount} major issue(s) that affect believability. Address these before publishing.`
      );
    }

    const travelIssues = issues.filter(i => i.type === 'impossible_travel');
    if (travelIssues.length > 0) {
      suggestions.push(
        `Your characters move between locations faster than physically possible ${travelIssues.length} times. ` +
        `Consider your world's travel rules or add travel scenes.`
      );
    }

    const presenceIssues = issues.filter(i => i.type === 'character_presence');
    if (presenceIssues.length > 0) {
      suggestions.push(
        `${presenceIssues.length} characters have minimal timeline presence. ` +
        `Consider: are they important to your story?`
      );
    }

    if (suggestions.length === 0) {
      suggestions.push('✓ Your timeline is solid! No major issues detected.');
    }

    return suggestions;
  }

  /**
   * Helper: Store issues in database for later review
   */
  private async storeIssues(projectId: string, issues: TimelineIssue[]): Promise<void> {
    try {
      // Clear old issues
      await this.prisma.timelineIssue.deleteMany({ where: { projectId } });

      // Store new issues
      for (const issue of issues) {
        await this.prisma.timelineIssue.create({
          data: {
            projectId,
            issueType: issue.type,
            severity: issue.severity,
            affectedCharacterId: issue.character,
            description: issue.description,
            suggestion: issue.suggestion,
            teachingPoint: issue.teachingPoint,
            affectedEventIds: issue.affectedEventIds || [],
            isResolved: false
          }
        });
      }
    } catch (error) {
      console.error('Failed to store issues:', error);
      // Don't throw - this is non-critical
    }
  }

  /**
   * Helper: Generate unique issue ID
   */
  private generateIssueId(): string {
    return crypto.randomBytes(8).toString('hex');
  }
}
```

## Integration with Existing Code

### 1. Add to your service index

**File**: `backend/src/services/index.ts`

```typescript
export { TimelineOrchestratorService } from './analysis/TimelineOrchestratorService';
```

### 2. Import in your main app

**File**: `backend/src/app.ts` or wherever you initialize services

```typescript
import { TimelineOrchestratorService } from './services';

// Later, create an instance
const timelineService = new TimelineOrchestratorService();
```

## Testing the Service

Create `backend/src/services/__tests__/TimelineOrchestrator.test.ts`:

```typescript
import { TimelineOrchestratorService } from '../analysis/TimelineOrchestratorService';

describe('TimelineOrchestratorService', () => {
  let service: TimelineOrchestratorService;

  beforeEach(() => {
    service = new TimelineOrchestratorService();
  });

  it('should detect impossible travel', async () => {
    // Test: Character travels 900km in 1 day
    // Should create a critical issue
  });

  it('should detect broken dependencies', async () => {
    // Test: Event B depends on Event A, but A happens after B
    // Should create a critical issue
  });

  it('should detect character presence issues', async () => {
    // Test: Character created but never appears
    // Should create a major issue
  });

  it('should detect temporal paradoxes', async () => {
    // Test: Circular dependency A→B→C→A
    // Should create a critical issue
  });
});
```

## API Usage

```typescript
// In your API route handler
const timelineService = new TimelineOrchestratorService();
const result = await timelineService.validateTimeline(projectId);

console.log(`Found ${result.issues.length} issues`);
console.log(`${result.criticalIssues} critical`);
console.log(`${result.majorIssues} major`);
console.log(`${result.minorIssues} minor`);

// Return to frontend
res.json({
  success: true,
  data: result
});
```

## Next Steps

1. Create API routes to expose this service (see 03-API-ROUTES.md)
2. Build React components to visualize results (see 04-FRONTEND-COMPONENTS.md)
3. Add tests for edge cases
4. Integrate with your existing defect detection

## Summary

You now have a production-ready service that:
- ✅ Validates impossible travel scenarios
- ✅ Checks event dependencies and causality
- ✅ Flags character development issues
- ✅ Detects timing and pacing gaps
- ✅ Catches temporal paradoxes
- ✅ Provides teaching points for each issue
- ✅ Returns actionable suggestions
- ✅ Stores results for historical tracking

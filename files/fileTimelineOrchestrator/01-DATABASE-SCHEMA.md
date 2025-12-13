# Timeline Orchestrator - Database Schema Implementation

## Overview
This guide covers the Prisma schema additions needed for the Timeline Orchestrator feature. These models track story events, character movements, and timeline validations for fantasy/sci-fi novels.

## Implementation Steps

### Step 1: Update Prisma Schema

**File**: `backend/prisma/schema.prisma`

**Add these models to the end of your existing schema.prisma file:**

```prisma
// TIMELINE EVENT MODEL - Tracks story events with dates and dependencies
model TimelineEvent {
  id              String    @id @default(uuid())
  projectId       String
  name            String    // "Robb crowned king", "Arya escapes King's Landing"
  description     String?
  
  // WHEN it happens
  storyDate       DateTime? // Actual date in story world (Jan 15, Year 298)
  position        Float?    // 0-1 (where in manuscript it appears, if known)
  
  // WHAT it is
  eventType       String    // "character_action", "world_event", "revelation", "travel", "meeting"
  
  // WHO is involved (JSON array of character IDs)
  characterIds    String[]  @default([])
  
  // WHERE it happens
  locationId      String?
  
  // STORY DEPENDENCIES - Events that must happen before this one
  prerequisiteIds String[]  @default([])
  
  // TEACHING DATA
  narrativeImportance Float @default(0.5) // 0-1 scale for teaching priority
  notes           String?   // Writer's notes for why this event exists
  
  createdAt       DateTime  @default(now())
  updatedAt       DateTime  @updatedAt
  
  // Relations
  project         Project   @relation(fields: [projectId], references: [id], onDelete: Cascade)
  location        Location? @relation(fields: [locationId], references: [id])
}

// LOCATION MODEL - Physical places in the world
model Location {
  id              String    @id @default(uuid())
  projectId       String
  name            String    // "King's Landing", "Winterfell", "The Wall"
  description     String?
  
  // For travel time calculations
  travelDistanceKm Float?   // You can create a location-to-location distance table later
  knownTravelMethods String[] @default([]) // ["horse", "carriage", "magic_portal", "flight"]
  
  createdAt       DateTime  @default(now())
  updatedAt       DateTime  @updatedAt
  
  // Relations
  project         Project   @relation(fields: [projectId], references: [id], onDelete: Cascade)
  timelineEvents  TimelineEvent[]
  travelLegsFrom  TravelLeg[] @relation("FromLocation")
  travelLegsTo    TravelLeg[] @relation("ToLocation")
}

// TRAVEL LEG MODEL - Tracks character movement between locations
model TravelLeg {
  id              String    @id @default(uuid())
  projectId       String
  characterId     String
  
  // Route
  fromLocationId  String
  toLocationId    String
  
  // Timing
  departDate      DateTime
  arrivalDate     DateTime?
  
  // HOW they traveled
  travelMethod    String    // "horse", "carriage", "sailing", "flying", "teleportation"
  estimatedDays   Int?      // How many days should this take?
  
  // WHY (teaching purposes)
  notes           String?   // "Took scenic route to avoid patrol", etc.
  
  createdAt       DateTime  @default(now())
  updatedAt       DateTime  @updatedAt
  
  // Relations
  project         Project   @relation(fields: [projectId], references: [id], onDelete: Cascade)
  character       Character @relation(fields: [characterId], references: [id], onDelete: Cascade)
  fromLocation    Location  @relation("FromLocation", fields: [fromLocationId], references: [id])
  toLocation      Location  @relation("ToLocation", fields: [toLocationId], references: [id])
}

// TIMELINE ISSUE MODEL - Problems detected in timeline
model TimelineIssue {
  id              String    @id @default(uuid())
  projectId       String
  
  // WHAT'S WRONG
  issueType       String    // "impossible_travel", "dependency_violation", "character_presence", "timing_gap", "paradox"
  severity        String    // "critical", "major", "minor"
  
  // WHERE THE PROBLEM IS
  affectedEventIds String[] @default([])
  affectedCharacterId String?
  
  // THE ISSUE
  description     String    // What the problem is
  suggestion      String    // How to fix it
  teachingPoint   String?   // Why it matters
  
  // RESOLUTION
  isResolved      Boolean   @default(false)
  resolutionNotes String?
  
  createdAt       DateTime  @default(now())
  updatedAt       DateTime  @updatedAt
  
  // Relations
  project         Project   @relation(fields: [projectId], references: [id], onDelete: Cascade)
}

// TRAVEL SPEED PROFILE MODEL - World-specific travel speeds
model TravelSpeedProfile {
  id              String    @id @default(uuid())
  projectId       String
  
  // Travel method speeds (km per day)
  walking         Float     @default(40)
  horse           Float     @default(80)
  carriage        Float     @default(60)
  sailing         Float     @default(150)
  flying          Float     @default(200)
  teleportation   Float     @default(999999) // instant
  custom1Name     String?
  custom1Speed    Float?
  custom2Name     String?
  custom2Speed    Float?
  
  // Notes on how travel works in this world
  rules           String?   // "Horses need 8 hours rest per day", etc.
  
  createdAt       DateTime  @default(now())
  updatedAt       DateTime  @updatedAt
  
  // Relations
  project         Project   @relation(fields: [projectId], references: [id], onDelete: Cascade)
}

// LOCATION DISTANCE TABLE - Pre-calculated distances between locations
model LocationDistance {
  id              String    @id @default(uuid())
  projectId       String
  fromLocationId  String
  toLocationId    String
  
  distanceKm      Float
  notes           String?   // "Mountain pass, longer but safer"
  
  createdAt       DateTime  @default(now())
  
  // Relations
  project         Project   @relation(fields: [projectId], references: [id], onDelete: Cascade)
  
  @@unique([projectId, fromLocationId, toLocationId])
}

// Update the existing Project model - add relations
// (ADD THESE TO YOUR EXISTING PROJECT MODEL)
// timelineEvents  TimelineEvent[]
// locations       Location[]
// travelLegs      TravelLeg[]
// timelineIssues  TimelineIssue[]
// travelSpeeds    TravelSpeedProfile[]
// locationDistances LocationDistance[]

// Update the existing Character model - add relations
// (ADD THESE TO YOUR EXISTING CHARACTER MODEL)
// travelLegs      TravelLeg[]
```

### Step 2: Update Existing Models

**In your existing `backend/prisma/schema.prisma`, find the `Project` model and add:**

```prisma
model Project {
  // ... existing fields ...
  
  // TIMELINE RELATIONS
  timelineEvents    TimelineEvent[]
  locations         Location[]
  travelLegs        TravelLeg[]
  timelineIssues    TimelineIssue[]
  travelSpeeds      TravelSpeedProfile[]
  locationDistances LocationDistance[]
  
  // ... rest of model ...
}
```

**In your existing `Character` model, add:**

```prisma
model Character {
  // ... existing fields ...
  
  // TIMELINE RELATIONS
  travelLegs      TravelLeg[]
  
  // ... rest of model ...
}
```

### Step 3: Run Database Migration

```bash
cd backend

# Create the migration
npx prisma migrate dev --name add_timeline_orchestrator

# Generate updated client types
npx prisma generate

# Verify migration
npx prisma studio
# You should see the new tables in the browser interface
```

### Step 4: Checkpoint

Verify all tables were created:

```bash
npx prisma db execute --stdin < <(echo "
SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%Timeline%' OR name LIKE '%Location%' OR name LIKE '%Travel%';
")
```

You should see:
- `TimelineEvent`
- `Location`
- `TravelLeg`
- `TimelineIssue`
- `TravelSpeedProfile`
- `LocationDistance`

## Key Design Decisions

### 1. **Why JSON arrays for IDs instead of junction tables?**
- Trade-off: Simpler queries for small-to-medium projects
- For MVP, avoids over-normalization
- If you hit 10,000+ events, refactor to junction tables
- Alternative approach shown in comments if needed

### 2. **Why separate TravelLeg from TimelineEvent?**
- Travel is different from events (it has duration, route)
- Allows validation: "Is character here? Check travel records"
- Makes timeline queries more efficient
- Enables teaching: "You have character movement data"

### 3. **TravelSpeedProfile per project**
- Different worlds have different travel rules
- One project: horses are slow, magic is fast
- Another project: all travel is fast (space opera)
- Allows teaching: "Your world's travel rules are..."

### 4. **LocationDistance table**
- Pre-calculated distances (not computed each time)
- Allows for terrain (mountain routes are longer)
- Enables validation: "Distance is 500km, but you've allocated 5 days"

## Data Relationships Diagram

```
Project
  ├── TimelineEvent (many)
  │   ├── Location (one)
  │   ├── Character[] (many through characterIds)
  │   └── TimelineEvent[] (prerequisiteIds - self-reference)
  │
  ├── Location (many)
  │   ├── TimelineEvent (many)
  │   ├── TravelLeg (many as from/to)
  │   └── LocationDistance (many)
  │
  ├── TravelLeg (many)
  │   ├── Character (one)
  │   ├── Location (from)
  │   ├── Location (to)
  │   └── validates against TravelSpeedProfile
  │
  ├── TimelineIssue (many)
  │   └── TimelineEvent[] (affected events)
  │
  ├── TravelSpeedProfile (one, per project)
  │   └── defines speeds used in TravelLeg validation
  │
  └── LocationDistance (many)
      └── from Location to Location
```

## Example Data Structure

Here's what data looks like after a writer creates a fantasy timeline:

```
PROJECT: "The War of Five Kings"
├── TravelSpeedProfile:
│   └── horse: 80 km/day
│       carriage: 60 km/day
│       sailing: 150 km/day
│
├── Locations:
│   ├── Winterfell
│   ├── King's Landing (900 km south)
│   ├── Casterly Rock
│   └── The Wall
│
├── LocationDistances:
│   ├── Winterfell → King's Landing: 900 km
│   ├── Winterfell → Casterly Rock: 1200 km
│   └── King's Landing → Casterly Rock: 400 km
│
├── Characters:
│   ├── Robb Stark
│   ├── Arya Stark
│   └── Tyrion Lannister
│
├── TimelineEvents:
│   ├── Event: "Robb crowned king" (Day 1)
│   │   └── Characters: [Robb]
│   │   └── Location: Winterfell
│   │
│   ├── Event: "Robb marches south" (Day 15)
│   │   └── Characters: [Robb, 500 soldiers]
│   │   └── Location: Winterfell → marching
│   │   └── Prerequisite: "Robb crowned king"
│   │
│   ├── Event: "Arya escapes King's Landing" (Day 40)
│   │   └── Characters: [Arya]
│   │   └── Location: King's Landing
│   │
│   └── Event: "Battle of Whispering Wood" (Day 50)
│       └── Characters: [Robb, Catelyn, Roose Bolton]
│       └── Location: Battle site
│       └── Prerequisites: ["Robb marches south"]
│
└── TravelLegs:
    ├── Robb: Winterfell → South (Day 15-40)
    │   └── method: horse, 1200 km, ~15 days
    │
    └── Arya: (hidden escape, no record)
        └── but if added: King's Landing → (unknown)
```

## Next Steps

Once migrations are complete:
1. Create the TimelineOrchestratorService (see 02-BACKEND-SERVICE.md)
2. Build the API routes (see 03-API-ROUTES.md)
3. Create the React components (see 04-FRONTEND-COMPONENTS.md)

## Troubleshooting

### "Error: Foreign key constraint failed"
- Make sure Project exists before creating TimelineEvent
- Check that characterId references valid Character
- In tests, use cascading deletes

### "UUID generation failed"
- Ensure `@default(uuid())` is only used for String @id fields
- Check Prisma version is updated

### "relationMode = 'prisma'" issues
- Some database setups need explicit relation mode
- Add to your datasource block if needed:
  ```prisma
  datasource db {
    provider = "sqlite"
    url      = env("DATABASE_URL")
    relationMode = "prisma"  // Add this if foreign keys fail
  }
  ```

## Summary

You now have a comprehensive schema that:
- ✅ Tracks story events with dates and dependencies
- ✅ Models character movements and travel logistics
- ✅ Stores world-specific travel rules
- ✅ Records detected timeline issues and teaching points
- ✅ Maintains relationships between all elements

This is the foundation for validating timelines and teaching writers about causality, logistics, and story structure.

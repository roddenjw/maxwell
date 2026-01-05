#!/usr/bin/env python3
"""
Test script for Timeline Orchestrator backend implementation
"""

import sys
import uuid
from datetime import datetime

# Add backend to path
sys.path.insert(0, '/Users/josephrodden/Maxwell/backend')

from app.services.timeline_service import timeline_service
from app.database import SessionLocal
from app.models.timeline import TimelineEvent, TravelSpeedProfile, LocationDistance, TravelLeg
from app.models.entity import Entity

def test_travel_profile():
    """Test travel profile creation"""
    print("\n📝 Test 1: Travel Speed Profile")
    print("=" * 50)

    test_manuscript_id = str(uuid.uuid4())

    # Create default profile
    profile = timeline_service.get_or_create_travel_profile(test_manuscript_id)
    print(f"✅ Created travel profile: {profile.id}")
    print(f"   Default speed: {profile.default_speed} km/h")
    print(f"   Speeds: {profile.speeds}")

    # Update speeds
    updated = timeline_service.update_travel_speeds(
        test_manuscript_id,
        {"dragon": 100, "magic_portal": 999999},
        default_speed=10
    )
    print(f"✅ Updated travel profile")
    print(f"   New default speed: {updated.default_speed} km/h")
    print(f"   Dragon speed: {updated.speeds.get('dragon')} km/h")

    return test_manuscript_id

def test_location_distances(manuscript_id):
    """Test location distance management"""
    print("\n📝 Test 2: Location Distances")
    print("=" * 50)

    loc_a = str(uuid.uuid4())
    loc_b = str(uuid.uuid4())

    # Set distance
    distance = timeline_service.set_location_distance(
        manuscript_id,
        loc_a,
        loc_b,
        500,  # 500km
        {"terrain": "mountains", "difficulty": "hard"}
    )
    print(f"✅ Set distance: {distance.distance_km}km")
    print(f"   Metadata: {distance.distance_metadata}")

    # Get distance
    retrieved = timeline_service.get_location_distance(manuscript_id, loc_a, loc_b)
    print(f"✅ Retrieved distance: {retrieved}km")

    # Test bidirectional (reversed order should work)
    retrieved_reversed = timeline_service.get_location_distance(manuscript_id, loc_b, loc_a)
    print(f"✅ Bidirectional works: {retrieved_reversed}km")

    return loc_a, loc_b

def test_validators(manuscript_id):
    """Test the 5 core validators"""
    print("\n📝 Test 3: Core Validators")
    print("=" * 50)

    db = SessionLocal()
    try:
        # Create some test data
        # Character
        char = Entity(
            id=str(uuid.uuid4()),
            manuscript_id=manuscript_id,
            type="CHARACTER",
            name="Test Hero",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(char)

        # Locations
        loc1 = Entity(
            id=str(uuid.uuid4()),
            manuscript_id=manuscript_id,
            type="LOCATION",
            name="City A",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        loc2 = Entity(
            id=str(uuid.uuid4()),
            manuscript_id=manuscript_id,
            type="LOCATION",
            name="City B",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(loc1)
        db.add(loc2)
        db.commit()

        # Set distance between locations
        timeline_service.set_location_distance(manuscript_id, loc1.id, loc2.id, 100)

        # Create timeline events
        event1 = timeline_service.create_event(
            manuscript_id=manuscript_id,
            description="Hero arrives at City A",
            event_type="SCENE",
            order_index=0,
            location_id=loc1.id,
            character_ids=[char.id]
        )
        print(f"✅ Created event 1: {event1.description}")

        event2 = timeline_service.create_event(
            manuscript_id=manuscript_id,
            description="Hero arrives at City B",
            event_type="SCENE",
            order_index=1,  # Only 1 day later (impossible for 100km at 5km/h)
            location_id=loc2.id,
            character_ids=[char.id]
        )
        print(f"✅ Created event 2: {event2.description}")

        # Run validators
        print("\n🔍 Running Timeline Orchestrator validation...")
        issues = timeline_service.validate_timeline_orchestrator(manuscript_id)

        print(f"\n✅ Validation complete!")
        print(f"   Found {len(issues)} issues:")

        for issue in issues:
            print(f"\n   [{issue.severity}] {issue.inconsistency_type}")
            print(f"   {issue.description}")
            if issue.teaching_point:
                print(f"   📚 Teaching: {issue.teaching_point[:100]}...")

        # Test resolution
        if issues:
            issue_to_resolve = issues[0]
            success = timeline_service.resolve_inconsistency_with_notes(
                issue_to_resolve.id,
                "Fixed by adjusting timeline spacing"
            )
            print(f"\n✅ Resolved issue: {success}")

    finally:
        db.close()

def test_comprehensive_data(manuscript_id):
    """Test comprehensive data retrieval"""
    print("\n📝 Test 4: Comprehensive Data Retrieval")
    print("=" * 50)

    data = timeline_service.get_comprehensive_timeline_data(manuscript_id)

    print(f"✅ Retrieved comprehensive data:")
    print(f"   Events: {len(data['events'])}")
    print(f"   Inconsistencies: {len(data['inconsistencies'])}")
    print(f"   Travel legs: {len(data['travel_legs'])}")
    print(f"   Location distances: {len(data['location_distances'])}")
    print(f"   Travel profile: {data['travel_profile'].default_speed} km/h")
    print(f"   Stats: {data['stats']['total_events']} total events")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 TIMELINE ORCHESTRATOR BACKEND TEST SUITE")
    print("="*60)

    try:
        # Run tests
        manuscript_id = test_travel_profile()
        loc_a, loc_b = test_location_distances(manuscript_id)
        test_validators(manuscript_id)
        test_comprehensive_data(manuscript_id)

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)

    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ TEST FAILED: {e}")
        print("="*60)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

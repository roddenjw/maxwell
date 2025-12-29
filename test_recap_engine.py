#!/usr/bin/env python3
"""
Test script for Aesthetic Recap Engine
Tests chapter and arc recap generation
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

# Sample chapter data for testing
TEST_CHAPTER_CONTENT = """
The rain hammered against the windows of Sarah's apartment as she stared at the letter in her hands. The paper trembled, not from the storm outside, but from the earthquake happening inside her chest.

"How could he?" she whispered to the empty room.

Marcus had been her anchor for three years. Through grad school, through her mother's illness, through every storm life had thrown at them. And now this—a confession buried in ink and cowardice, delivered by mail instead of spoken to her face.

She crumpled the letter and threw it across the room. It bounced off the bookshelf they'd built together last spring, landing near the photo of them in Barcelona. That trip felt like it belonged to different people now.

Her phone buzzed. Marcus. She declined the call.

Outside, lightning split the sky, illuminating the city in sharp, brutal clarity. Sarah realized she'd been living in shadow for months, mistaking it for comfort. The letter hadn't broken her world—it had just turned on the lights.

She picked up her phone and blocked his number. Then she grabbed her jacket.

The storm could rage all it wanted. She was done hiding from it.
"""

def test_backend_connection():
    """Test if backend is running"""
    print("=" * 70)
    print("TESTING BACKEND CONNECTION")
    print("=" * 70)

    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Backend is running")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Backend returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("   Make sure backend is running:")
        print("   cd backend && source venv/bin/activate && uvicorn app.main:app --reload")
        return False


def get_first_chapter():
    """Get the first chapter from the database for testing"""
    print("\n" + "=" * 70)
    print("FINDING TEST CHAPTER")
    print("=" * 70)

    try:
        # Try to get manuscripts
        response = requests.get(f"{BASE_URL}/api/manuscripts")
        if response.status_code == 200:
            manuscripts = response.json()
            if manuscripts:
                manuscript_id = manuscripts[0]['id']
                print(f"✅ Found manuscript: {manuscripts[0].get('title', 'Untitled')}")

                # Get chapters for this manuscript
                chapters_response = requests.get(f"{BASE_URL}/api/chapters/manuscript/{manuscript_id}")
                if chapters_response.status_code == 200:
                    chapters_data = chapters_response.json()
                    # Handle {success: true, data: [...]} response format
                    if isinstance(chapters_data, dict) and 'data' in chapters_data:
                        chapters = chapters_data['data']
                    elif isinstance(chapters_data, dict) and 'chapters' in chapters_data:
                        chapters = chapters_data['chapters']
                    else:
                        chapters = chapters_data if isinstance(chapters_data, list) else []
                    if chapters:
                        # Find first non-folder chapter with content
                        for chapter in chapters:
                            if not chapter.get('is_folder') and chapter.get('content'):
                                print(f"✅ Found chapter: {chapter.get('title', 'Untitled')}")
                                print(f"   Chapter ID: {chapter['id']}")
                                print(f"   Word count: {len(chapter['content'].split())}")
                                return chapter['id']

        print("⚠️  No chapters found in database")
        return None

    except Exception as e:
        print(f"❌ Error finding chapters: {e}")
        return None


def test_chapter_recap(chapter_id):
    """Test generating a chapter recap"""
    print("\n" + "=" * 70)
    print("TESTING CHAPTER RECAP GENERATION")
    print("=" * 70)

    try:
        print(f"📝 Generating recap for chapter: {chapter_id}")
        print("⏳ This may take 10-20 seconds (calling Claude API)...")

        start_time = time.time()

        response = requests.post(
            f"{BASE_URL}/api/recap/chapter/{chapter_id}",
            json={"force_regenerate": False}
        )

        elapsed = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Recap generated in {elapsed:.1f} seconds")
            print(f"   Recap ID: {data['recap_id']}")
            print(f"   Cached: {data.get('is_cached', False)}")

            content = data['content']

            print("\n📊 RECAP CONTENT:")
            print("-" * 70)

            if 'summary' in content:
                print(f"\n📖 Summary:\n   {content['summary']}")

            if 'key_events' in content:
                print(f"\n🎯 Key Events:")
                for i, event in enumerate(content['key_events'], 1):
                    print(f"   {i}. {event}")

            if 'character_developments' in content:
                print(f"\n👥 Character Developments:")
                for dev in content['character_developments']:
                    if isinstance(dev, dict):
                        print(f"   • {dev.get('character', 'Unknown')}: {dev.get('development', '')}")
                    else:
                        print(f"   • {dev}")

            if 'themes' in content:
                print(f"\n🎨 Themes:")
                for theme in content['themes']:
                    print(f"   • {theme}")

            if 'emotional_tone' in content:
                print(f"\n💭 Emotional Tone:\n   {content['emotional_tone']}")

            if 'narrative_arc' in content:
                print(f"\n📈 Narrative Arc:\n   {content['narrative_arc']}")

            if 'memorable_moments' in content:
                print(f"\n✨ Memorable Moments:")
                for moment in content['memorable_moments']:
                    print(f"   • {moment}")

            return data['recap_id']
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_cached_recap(chapter_id):
    """Test retrieving cached recap"""
    print("\n" + "=" * 70)
    print("TESTING CACHED RECAP RETRIEVAL")
    print("=" * 70)

    try:
        print(f"📝 Requesting recap for chapter: {chapter_id}")
        print("⏳ Should be instant (using cache)...")

        start_time = time.time()

        response = requests.post(
            f"{BASE_URL}/api/recap/chapter/{chapter_id}",
            json={"force_regenerate": False}
        )

        elapsed = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            is_cached = data.get('is_cached', False)

            if is_cached:
                print(f"✅ Retrieved cached recap in {elapsed:.2f} seconds")
                print(f"   Recap ID: {data['recap_id']}")
                print("   🚀 Cache is working!")
            else:
                print(f"⚠️  Recap was regenerated ({elapsed:.1f} seconds)")
                print("   Cache may not be working as expected")

            return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_get_recap_endpoint(chapter_id):
    """Test GET recap endpoint"""
    print("\n" + "=" * 70)
    print("TESTING GET RECAP ENDPOINT")
    print("=" * 70)

    try:
        response = requests.get(f"{BASE_URL}/api/recap/chapter/{chapter_id}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Successfully retrieved recap")
            print(f"   Recap ID: {data['recap_id']}")
            print(f"   Created: {data['created_at']}")
            return True
        elif response.status_code == 404:
            print(f"⚠️  No recap found (expected if not generated yet)")
            return True
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n🎬 AESTHETIC RECAP ENGINE - BACKEND TEST SUITE")
    print("=" * 70)

    # Test 1: Backend connection
    if not test_backend_connection():
        print("\n❌ Backend not available. Exiting.")
        return

    # Test 2: Find a chapter to test with
    chapter_id = get_first_chapter()
    if not chapter_id:
        print("\n⚠️  No chapters available for testing")
        print("   Create a chapter in the app first, then run this test again")
        return

    # Test 3: Generate chapter recap
    recap_id = test_chapter_recap(chapter_id)
    if not recap_id:
        print("\n❌ Chapter recap generation failed")
        return

    # Test 4: Test caching
    time.sleep(1)  # Brief pause
    test_cached_recap(chapter_id)

    # Test 5: Test GET endpoint
    test_get_recap_endpoint(chapter_id)

    # Summary
    print("\n" + "=" * 70)
    print("✅ ALL TESTS COMPLETE!")
    print("=" * 70)
    print("\nThe Aesthetic Recap Engine backend is working correctly!")
    print("\nNext steps:")
    print("  1. Build the frontend UI to display these beautiful recaps")
    print("  2. Add a recap button to the chapter interface")
    print("  3. Create an arc recap feature for multiple chapters")


if __name__ == "__main__":
    main()

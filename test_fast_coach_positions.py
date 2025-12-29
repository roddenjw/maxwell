#!/usr/bin/env python3
"""
Test script for Fast Coach position data
Verifies that all analyzers properly set start_char and end_char
"""

import requests
import json

# Test text with repetition and long paragraph
TEST_TEXT_REPETITION = """
The character walked down the street. The character looked around nervously.
The character wondered where everyone had gone. The character felt alone.
"""

TEST_TEXT_LONG_PARAGRAPH = """This is an extremely long paragraph that contains more than 200 words and should trigger the long paragraph detector. """ + (
    "The story continues with many details about the character's journey through the vast landscape. " * 20
) + """This paragraph just keeps going and going without any breaks, making it difficult for readers to maintain focus and engagement with the narrative content."""

def test_fast_coach_positions():
    """Test that analyzers properly set position data"""

    url = "http://localhost:8000/api/fast-coach/analyze"

    print("Testing Fast Coach Position Data...")
    print("=" * 70)

    # Test 1: Repetition detector
    print("\n1. Testing REPETITION detector")
    print("-" * 70)

    response = requests.post(url, json={
        "text": TEST_TEXT_REPETITION,
        "manuscript_id": None,
        "check_consistency": False
    })

    if response.status_code == 200:
        data = response.json()
        repetition_suggestions = [s for s in data['suggestions'] if s['type'] == 'REPETITION']

        print(f"Found {len(repetition_suggestions)} repetition suggestion(s)")

        for i, sug in enumerate(repetition_suggestions, 1):
            print(f"\n  Suggestion {i}:")
            print(f"    Message: {sug['message']}")
            print(f"    Highlight: {sug.get('highlight_word', 'N/A')}")
            print(f"    start_char: {sug.get('start_char', 'MISSING')}")
            print(f"    end_char: {sug.get('end_char', 'MISSING')}")

            # Verify position data
            if sug.get('start_char') is not None and sug.get('end_char') is not None:
                start = sug['start_char']
                end = sug['end_char']
                highlighted_text = TEST_TEXT_REPETITION[start:end]
                print(f"    ✅ Position data present")
                print(f"    Highlighted text: '{highlighted_text}'")

                # Verify it's not just jumping to position 0
                if start == 0 and end == 0:
                    print(f"    ❌ ERROR: Positions are both 0!")
                elif start >= 0 and end > start:
                    print(f"    ✅ Valid position range: {start} to {end}")
                else:
                    print(f"    ❌ ERROR: Invalid position range!")
            else:
                print(f"    ❌ MISSING position data!")
    else:
        print(f"❌ Request failed: {response.status_code}")

    # Test 2: Long paragraph detector
    print("\n\n2. Testing LONG PARAGRAPH detector")
    print("-" * 70)

    response = requests.post(url, json={
        "text": TEST_TEXT_LONG_PARAGRAPH,
        "manuscript_id": None,
        "check_consistency": False
    })

    if response.status_code == 200:
        data = response.json()
        style_suggestions = [s for s in data['suggestions'] if s['type'] == 'STYLE' and 'paragraph' in s['message'].lower()]

        print(f"Found {len(style_suggestions)} long paragraph suggestion(s)")

        for i, sug in enumerate(style_suggestions, 1):
            print(f"\n  Suggestion {i}:")
            print(f"    Message: {sug['message']}")
            print(f"    start_char: {sug.get('start_char', 'MISSING')}")
            print(f"    end_char: {sug.get('end_char', 'MISSING')}")

            # Verify position data
            if sug.get('start_char') is not None and sug.get('end_char') is not None:
                start = sug['start_char']
                end = sug['end_char']
                highlighted_text = TEST_TEXT_LONG_PARAGRAPH[start:end]
                print(f"    ✅ Position data present")
                print(f"    Highlighted text preview: '{highlighted_text[:60]}...'")

                # Verify it's not just jumping to position 0
                if start == 0 and end == 0:
                    print(f"    ❌ ERROR: Positions are both 0!")
                elif start >= 0 and end > start:
                    print(f"    ✅ Valid position range: {start} to {end}")
                else:
                    print(f"    ❌ ERROR: Invalid position range!")
            else:
                print(f"    ❌ MISSING position data!")
    else:
        print(f"❌ Request failed: {response.status_code}")

    # Test 3: All analyzer types with position validation
    print("\n\n3. Testing ALL suggestions for position data validity")
    print("-" * 70)

    combined_text = TEST_TEXT_REPETITION + "\n\n" + TEST_TEXT_LONG_PARAGRAPH

    response = requests.post(url, json={
        "text": combined_text,
        "manuscript_id": None,
        "check_consistency": False
    })

    if response.status_code == 200:
        data = response.json()
        all_suggestions = data['suggestions']

        print(f"\nTotal suggestions: {len(all_suggestions)}")

        has_position = 0
        missing_position = 0
        invalid_position = 0

        for sug in all_suggestions:
            start = sug.get('start_char')
            end = sug.get('end_char')

            if start is not None and end is not None:
                if start >= 0 and end > start:
                    has_position += 1
                else:
                    invalid_position += 1
                    print(f"  ⚠️  {sug['type']}: Invalid position ({start}, {end}) - {sug['message']}")
            else:
                missing_position += 1
                print(f"  ℹ️  {sug['type']}: No position data - {sug['message']}")

        print(f"\n📊 Summary:")
        print(f"  ✅ With valid positions: {has_position}")
        print(f"  ℹ️  Without positions: {missing_position}")
        print(f"  ❌ Invalid positions: {invalid_position}")

        if invalid_position > 0:
            print(f"\n⚠️  WARNING: {invalid_position} suggestions have invalid position data!")
        else:
            print(f"\n✅ All suggestions with position data have valid ranges!")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        test_fast_coach_positions()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend. Make sure the server is running.")
        print("   Run: cd backend && source venv/bin/activate && uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

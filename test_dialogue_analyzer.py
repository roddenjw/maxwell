#!/usr/bin/env python3
"""
Test script for Fast Coach Dialogue Analyzer
Tests various dialogue patterns and edge cases
"""

import requests
import json

# Sample text with various dialogue issues
TEST_TEXT = """
"Hello!" she exclaimed excitedly. "How are you doing today?"

"I'm, um, doing okay," he said nervously. "I mean, you know, just kind of dealing with stuff."

"You seem distracted," she opined dramatically.

"Well, uh, it's just that..." he trailed off.

"What is it?" she asked.

"I don't know!" he shouted!

"Calm down!" she yelled!

"I'm sorry," he muttered quietly. "I just... I really... you know..."

"You're using a lot of ellipses," she said. "And you keep saying 'you know' and 'I mean'."

"I know, I know!" he exclaimed! "I'm just... uh... well..."

"Let's talk about this later," she said angrily.
"""

def test_dialogue_analyzer():
    """Test the dialogue analyzer endpoint"""

    url = "http://localhost:8000/api/fast-coach/analyze"

    payload = {
        "text": TEST_TEXT,
        "manuscript_id": None,
        "check_consistency": False
    }

    print("Testing Fast Coach Dialogue Analyzer...")
    print("=" * 60)

    try:
        response = requests.post(url, json=payload)

        if response.status_code == 200:
            data = response.json()
            suggestions = data.get("suggestions", [])
            stats = data.get("stats", {})

            print(f"\n✅ Request successful!")
            print(f"\nTotal suggestions: {stats.get('total_suggestions', 0)}")

            # Group suggestions by type
            dialogue_suggestions = [s for s in suggestions if s.get("type") == "DIALOGUE"]
            pacing_suggestions = [s for s in suggestions if s.get("type") == "PACING"]

            print(f"\nDialogue suggestions: {len(dialogue_suggestions)}")
            print(f"Pacing suggestions: {len(pacing_suggestions)}")

            print("\n" + "=" * 60)
            print("DIALOGUE SUGGESTIONS:")
            print("=" * 60)

            for i, suggestion in enumerate(dialogue_suggestions, 1):
                print(f"\n{i}. {suggestion.get('message')}")
                print(f"   Severity: {suggestion.get('severity')}")
                print(f"   Suggestion: {suggestion.get('suggestion')}")
                if suggestion.get('highlight_word'):
                    print(f"   Highlighted: '{suggestion.get('highlight_word')}'")
                if suggestion.get('metadata'):
                    print(f"   Metadata: {suggestion.get('metadata')}")

            if pacing_suggestions:
                print("\n" + "=" * 60)
                print("PACING SUGGESTIONS:")
                print("=" * 60)

                for i, suggestion in enumerate(pacing_suggestions, 1):
                    print(f"\n{i}. {suggestion.get('message')}")
                    print(f"   Severity: {suggestion.get('severity')}")
                    print(f"   Suggestion: {suggestion.get('suggestion')}")

            # Verify expected checks
            print("\n" + "=" * 60)
            print("VERIFICATION:")
            print("=" * 60)

            messages = [s.get('message', '') for s in suggestions]

            checks = {
                "Fancy dialogue tag detected": any('Fancy dialogue tag' in m for m in messages),
                "Adverb + tag detected": any('adverb' in m.lower() for m in messages),
                "Dialogue crutches detected": any('crutch' in m.lower() for m in messages),
                "Exclamation overuse detected": any('exclamation' in m.lower() for m in messages),
                "Ellipsis overuse detected": any('ellipses' in m.lower() for m in messages),
            }

            for check, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"{status} {check}")

            print("\n" + "=" * 60)
            print("Stats by Type:")
            print("=" * 60)
            for type_name, count in stats.get('by_type', {}).items():
                print(f"  {type_name}: {count}")

            print("\n" + "=" * 60)
            print("Stats by Severity:")
            print("=" * 60)
            for severity, count in stats.get('by_severity', {}).items():
                print(f"  {severity}: {count}")

        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend. Make sure the server is running.")
        print("   Run: cd backend && source venv/bin/activate && uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_dialogue_analyzer()

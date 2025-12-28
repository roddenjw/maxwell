#!/usr/bin/env python3
"""
Test timeline improvements:
1. Flashback detection (conservative)
2. Character detection with NER fallback
3. Dialogue filtering
"""
import sys
sys.path.insert(0, '/Users/josephrodden/Maxwell/backend')

from app.services.nlp_service import nlp_service

def test_flashback_detection():
    """Test conservative flashback detection"""
    print("\n" + "="*60)
    print("🧪 Testing Flashback Detection")
    print("="*60)

    test_cases = [
        # Should detect (multiple indicators)
        ("She remembered the day years ago when they first met.", True),
        ("Looking back, he remembered those years ago clearly.", True),
        ("Years ago, he remembered being a soldier in the king's army.", True),

        # Should NOT detect (dialogue)
        ('"And what is it exactly that you seek to do?" asked the wizard.', False),
        ('"I had been walking for hours," he said.', False),

        # Should NOT detect (single indicator) - conservative approach
        ("He had been walking for hours through the dark forest.", False),
        ("The soldier used to train every morning.", False),
        ("Years ago, he had been a soldier in the king's army.", False),  # Only 1 pattern
    ]

    passed = 0
    failed = 0

    for text, expected in test_cases:
        is_flashback = nlp_service._detect_flashback_conservative(text)
        status = "✅" if is_flashback == expected else "❌"

        if is_flashback == expected:
            passed += 1
        else:
            failed += 1

        print(f"\n{status} Text: {text[:60]}...")
        print(f"   Expected: {expected}, Got: {is_flashback}")

    print(f"\n📊 Results: {passed} passed, {failed} failed")
    return failed == 0


def test_character_detection():
    """Test NER character detection with fallback"""
    print("\n" + "="*60)
    print("🧪 Testing Character Detection (NER Fallback)")
    print("="*60)

    # Sample text with characters
    test_text = '''
    "Will you join me, Farid Sa Garai Fol Jahan?" asked the warrior.
    Jarn stepped forward, his eyes gleaming. The young soldier watched nervously.
    Captain Marcus and Lord Blackwood discussed strategy in the Dark Forest.
    '''

    # Process with spaCy
    doc = nlp_service.nlp(test_text)

    # No pre-registered entities
    entity_lookup = {}

    registered_chars, detected_persons = nlp_service._detect_characters_with_ner(
        doc, entity_lookup
    )

    print(f"\n📝 Test text:\n{test_text}\n")
    print(f"✨ Detected persons: {detected_persons}")
    print(f"📊 Count: {len(detected_persons)}")

    # Check quality
    expected_chars = ['Farid Sa Garai Fol Jahan', 'Jarn', 'Marcus', 'Blackwood']
    should_filter = ['You', 'young', 'Captain', 'Lord']  # Common words/titles

    print("\n🔍 Quality checks:")
    for name in expected_chars:
        found = any(name in detected for detected in detected_persons)
        status = "✅" if found else "⚠️"
        print(f"  {status} Expected '{name}': {'Found' if found else 'Not found'}")

    for word in should_filter:
        found = word in detected_persons
        status = "❌" if found else "✅"
        print(f"  {status} Should filter '{word}': {'Failed (detected)' if found else 'Correctly filtered'}")

    return len(detected_persons) > 0


def test_dialogue_detection():
    """Test dialogue detection"""
    print("\n" + "="*60)
    print("🧪 Testing Dialogue Detection")
    print("="*60)

    test_cases = [
        ('"Hello, world!" he said.', True),
        ('"And what is it exactly that you seek to do?"', True),
        ('He walked through the forest.', False),
        ('"She remembered those years ago," she whispered.', True),
        ('The man spoke quietly about his past.', False),
    ]

    passed = 0
    for text, expected in test_cases:
        is_dialogue = nlp_service._is_dialogue(text)
        status = "✅" if is_dialogue == expected else "❌"

        if is_dialogue == expected:
            passed += 1

        print(f"{status} Text: {text[:50]}...")
        print(f"   Expected: {expected}, Got: {is_dialogue}")

    print(f"\n📊 Results: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


def test_timeline_extraction():
    """Test full timeline extraction with improvements"""
    print("\n" + "="*60)
    print("🧪 Testing Timeline Extraction (End-to-End)")
    print("="*60)

    test_manuscript = '''
    Chapter 1

    "Will you join me, Farid Sa Garai Fol Jahan? Will you help me free the ant?"

    The man, Jarn he had named himself. A squat fellow, not a dwarf.
    Young soldiers marched through the Dark Forest.

    Years ago, Jarn had been a scholar. He remembered those days fondly.

    "And what is it exactly that you seek to do?" asked Farid, his voice steady.
    '''

    events = nlp_service.extract_events(test_manuscript, known_entities=[])

    print(f"\n✨ Extracted {len(events)} events\n")

    for i, event in enumerate(events, 1):
        print(f"Event {i}:")
        print(f"  Type: {event['event_type']}")
        print(f"  Description: {event['description'][:60]}...")
        print(f"  Characters: {event['characters']}")

        detected = event['metadata'].get('detected_persons', [])
        if detected:
            print(f"  🔍 Auto-detected: {detected}")

        print()

    # Check for detected persons
    all_detected = []
    for event in events:
        all_detected.extend(event['metadata'].get('detected_persons', []))

    unique_detected = list(set(all_detected))
    print(f"📊 Unique auto-detected characters: {unique_detected}")

    # Check flashback detection
    flashback_events = [e for e in events if e['event_type'] == 'FLASHBACK']
    dialogue_flagged = any(
        '"And what is it exactly' in e['description'] and e['event_type'] == 'FLASHBACK'
        for e in events
    )

    print(f"\n✅ Flashback events: {len(flashback_events)}")
    print(f"{'❌' if dialogue_flagged else '✅'} Dialogue correctly excluded from flashbacks")

    return len(events) > 0 and len(unique_detected) > 0


if __name__ == "__main__":
    print("\n🚀 Timeline Improvements Test Suite")
    print("Testing NLP service enhancements\n")

    results = []

    # Run all tests
    results.append(("Dialogue Detection", test_dialogue_detection()))
    results.append(("Flashback Detection", test_flashback_detection()))
    results.append(("Character Detection", test_character_detection()))
    results.append(("Timeline Extraction", test_timeline_extraction()))

    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    total_passed = sum(1 for _, passed in results if passed)
    print(f"\n{total_passed}/{len(results)} tests passed")

    if total_passed == len(results):
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed")
        sys.exit(1)

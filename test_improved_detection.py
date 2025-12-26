#!/usr/bin/env python3
"""
Test improved entity detection with user's sample text
"""
import asyncio
import websockets
import json

async def test_user_text():
    uri = "ws://localhost:8000/api/realtime/nlp/ms-1765811186812"

    async with websockets.connect(uri) as websocket:
        print("✅ Connected to WebSocket")

        # Sample text from user with Farid and Jarn
        test_text = '''
        "Will you join me, Farid Sa Garai Fol Jahan? Will you help me free the ant?"
        I nodded again, of course I would. The man, Jarn he had named himself. A squat fellow, not a dwarf, but barely up to my shoulders.
        Young and old. soldier and scribe. A man of many faces and lives.
        The ants were well fed and for an ant, I imagine, happy.
        '''

        message = {"text_delta": test_text}
        await websocket.send(json.dumps(message))
        print(f"📤 Sent test text")

        # Wait for response
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)

            print(f"\n📥 Received response:")
            print(json.dumps(data, indent=2))

            if 'new_entities' in data:
                print(f"\n✨ Detected {len(data['new_entities'])} entities:")
                for entity in data['new_entities']:
                    print(f"  - {entity['type']}: {entity['name']} (via {entity['confidence']})")

                # Check for expected results
                entity_names = [e['name'] for e in data['new_entities']]
                print("\n📊 Analysis:")
                print(f"  ✓ Should detect: Farid - {'✅ FOUND' if 'Farid' in entity_names else '❌ MISSED'}")
                print(f"  ✓ Should detect: Jarn - {'✅ FOUND' if 'Jarn' in entity_names else '❌ MISSED'}")
                print(f"  ✗ Should NOT detect: Young - {'❌ FOUND' if 'Young' in entity_names else '✅ FILTERED'}")
                print(f"  ✗ Should NOT detect: fed - {'❌ FOUND' if 'fed' in entity_names else '✅ FILTERED'}")
        except asyncio.TimeoutError:
            print("⏱️  No response received (still processing or debouncing)")

if __name__ == "__main__":
    asyncio.run(test_user_text())

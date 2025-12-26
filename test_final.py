#!/usr/bin/env python3
"""
Final test with unique manuscript ID
"""
import asyncio
import websockets
import json

async def test_final():
    # Use unique manuscript ID to avoid connection limit
    uri = "ws://localhost:8000/api/realtime/nlp/test-final-12345"

    async with websockets.connect(uri) as websocket:
        print("✅ Connected to WebSocket")

        # Test text with characters
        test_text = '''
        "Will you join me, Farid Sa Garai Fol Jahan? Will you help me free the ant?"
        The man, Jarn he had named himself. A squat fellow, not a dwarf.
        Young soldiers marched through the Dark Forest.
        The creature fed upon the remains.
        '''

        message = {"text_delta": test_text}
        await websocket.send(json.dumps(message))
        print(f"📤 Sent test text")

        # Wait for response
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)

            print(f"\n📥 Response received:")
            if 'new_entities' in data:
                print(f"\n✨ Detected {len(data['new_entities'])} entities:")
                for entity in data['new_entities']:
                    print(f"  - {entity['type']}: {entity['name']}")

                entity_names = [e['name'] for e in data['new_entities']]
                print("\n📊 Quality Check:")
                print(f"  {'✅' if 'Jarn' in entity_names else '❌'} Jarn detected")
                print(f"  {'✅' if 'Farid Sa Garai Fol Jahan' in entity_names else '❌'} Farid detected")
                print(f"  {'✅' if 'Dark Forest' in entity_names else '❌'} Dark Forest detected")
                print(f"  {'✅' if 'Young' not in entity_names else '❌'} Young filtered (should be filtered)")
                print(f"  {'✅' if 'fed' not in entity_names else '❌'} fed filtered (should be filtered)")
        except asyncio.TimeoutError:
            print("⏱️  No response (still processing)")

if __name__ == "__main__":
    asyncio.run(test_final())

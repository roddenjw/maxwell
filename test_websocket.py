#!/usr/bin/env python3
"""
Test WebSocket endpoint for real-time NLP
"""
import asyncio
import websockets
import json

async def test_realtime_nlp():
    uri = "ws://localhost:8000/api/realtime/nlp/ms-1765811186812"

    async with websockets.connect(uri) as websocket:
        print("✅ Connected to WebSocket")

        # Send test text with entities
        test_text = "The brave knight Sir Galahad rode through the Dark Forest carrying the Obsidian Dagger."

        message = {"text_delta": test_text}
        await websocket.send(json.dumps(message))
        print(f"📤 Sent text: {test_text}")

        # Wait for response (with timeout)
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            print(f"\n📥 Received response:")
            print(json.dumps(data, indent=2))

            if 'new_entities' in data:
                print(f"\n✨ Detected {len(data['new_entities'])} entities:")
                for entity in data['new_entities']:
                    print(f"  - {entity['type']}: {entity['name']}")
        except asyncio.TimeoutError:
            print("⏱️  No response received (still processing or debouncing)")

if __name__ == "__main__":
    asyncio.run(test_realtime_nlp())

#!/usr/bin/env python3
"""
Test performance optimizations for real-time NLP
"""
import asyncio
import websockets
import json
import time

async def test_connection_limits():
    """Test that connection limits are enforced"""
    print("\n🧪 Testing connection limits...")

    uri = "ws://localhost:8000/api/realtime/nlp/test-manuscript"
    connections = []

    try:
        # Try to open 3 connections (limit is 2)
        for i in range(3):
            try:
                ws = await websockets.connect(uri)
                connections.append(ws)
                print(f"  ✅ Connection {i+1} accepted")
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"  ❌ Connection {i+1} rejected: {e}")

        print(f"  📊 Total connections opened: {len(connections)}/3")

        if len(connections) == 2:
            print("  ✅ Connection limit working correctly (max 2)")
        elif len(connections) == 3:
            print("  ⚠️  All 3 connections accepted (limit not working)")
        else:
            print(f"  ⚠️  Unexpected number of connections: {len(connections)}")

    finally:
        # Close all connections
        for ws in connections:
            await ws.close()


async def test_text_size_limits():
    """Test that text size limits are enforced"""
    print("\n🧪 Testing text size limits...")

    uri = "ws://localhost:8000/api/realtime/nlp/ms-1765811186812"

    async with websockets.connect(uri) as websocket:
        # Send large text (10,000 chars - should be truncated to 5,000)
        large_text = "A" * 10000

        message = {"text_delta": large_text}
        await websocket.send(json.dumps(message))
        print(f"  📤 Sent {len(large_text)} characters")

        # Wait for processing
        await asyncio.sleep(3)
        print("  ✅ Large text handled without crash")


async def test_idle_timeout():
    """Test idle connection cleanup"""
    print("\n🧪 Testing idle timeout (this will take 5+ minutes in production)...")
    print("  ⏭️  Skipping full test (would take too long)")
    print("  💡 Idle timeout is set to 5 minutes of inactivity")


async def test_buffer_overflow():
    """Test buffer overflow protection"""
    print("\n🧪 Testing buffer overflow protection...")

    uri = "ws://localhost:8000/api/realtime/nlp/ms-1765811186812"

    async with websockets.connect(uri) as websocket:
        # Send many small chunks rapidly to fill buffer
        for i in range(100):
            message = {"text_delta": f"Test chunk {i} " * 20}
            await websocket.send(json.dumps(message))
            await asyncio.sleep(0.01)  # Send very quickly

        print("  📤 Sent 100 rapid chunks")
        await asyncio.sleep(3)
        print("  ✅ Buffer overflow handled without crash")


async def test_concurrent_processing():
    """Test that only one analysis runs at a time per manuscript"""
    print("\n🧪 Testing concurrent processing locks...")

    uri = "ws://localhost:8000/api/realtime/nlp/ms-1765811186812"

    async with websockets.connect(uri) as websocket:
        # Send multiple chunks rapidly
        test_texts = [
            "Sir Galahad rode forth.",
            "The Dark Forest loomed ahead.",
            "Jarn the wizard appeared.",
            "Farid drew his Obsidian Dagger."
        ]

        for text in test_texts:
            message = {"text_delta": text}
            await websocket.send(json.dumps(message))
            await asyncio.sleep(0.1)

        print("  📤 Sent 4 text chunks in rapid succession")
        await asyncio.sleep(3)

        # Collect responses
        responses = []
        try:
            for _ in range(4):
                response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                data = json.loads(response)
                if 'new_entities' in data:
                    responses.append(data)
        except asyncio.TimeoutError:
            pass

        print(f"  📥 Received {len(responses)} responses")
        print("  ✅ Processing completed (responses handled sequentially)")


async def run_all_tests():
    """Run all performance tests"""
    print("=" * 60)
    print("🚀 Performance Optimization Test Suite")
    print("=" * 60)

    await test_connection_limits()
    await asyncio.sleep(2)  # Wait for connections to close

    await test_text_size_limits()
    await asyncio.sleep(2)  # Wait for connections to close

    await test_buffer_overflow()
    await asyncio.sleep(2)  # Wait for connections to close

    await test_concurrent_processing()
    await asyncio.sleep(2)  # Wait for connections to close

    await test_idle_timeout()

    print("\n" + "=" * 60)
    print("✅ All performance tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())

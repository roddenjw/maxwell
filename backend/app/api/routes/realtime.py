"""
Real-time API Routes (WebSocket)
Live entity detection and suggestions
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
import json

from app.database import get_db
from app.services.realtime_nlp_service import realtime_nlp_service
from app.models.entity import Entity

router = APIRouter(prefix="/api/realtime", tags=["realtime"])


@router.websocket("/nlp/{manuscript_id}")
async def websocket_nlp_endpoint(
    websocket: WebSocket,
    manuscript_id: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time entity detection

    Client sends: {"text_delta": "newly typed text"}
    Server sends: {"new_entities": [...], "timestamp": "..."}
    """
    # Check connection limit
    if not realtime_nlp_service.can_accept_connection(manuscript_id):
        await websocket.close(code=1008, reason="Too many connections for this manuscript")
        print(f"❌ Connection rejected for {manuscript_id}: too many connections")
        return

    await websocket.accept()
    realtime_nlp_service.register_connection(manuscript_id)
    print(f"✨ WebSocket connected for manuscript: {manuscript_id} ({realtime_nlp_service.active_connections.get(manuscript_id, 0)} active)")

    try:
        # Get existing entities from database (cached per connection)
        existing_entities = db.query(Entity).filter_by(
            manuscript_id=manuscript_id
        ).all()
        existing_names = [e.name for e in existing_entities]

        # Close database session early to free connection
        db.close()

        # Create a queue for incoming text
        import asyncio
        text_queue = asyncio.Queue()

        # Start background processor
        async def receive_text():
            """Receive text deltas from client and add to queue"""
            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)

                    if 'text_delta' in message:
                        await text_queue.put(message['text_delta'])
                    elif message.get('type') == 'ping':
                        # Respond to keep-alive pings
                        await websocket.send_json({"type": "pong"})
            except WebSocketDisconnect:
                print(f"❌ WebSocket disconnected: {manuscript_id}")
            except Exception as e:
                print(f"Error receiving text: {e}")

        async def process_and_send():
            """Process text queue and send entity suggestions"""
            try:
                async for result in realtime_nlp_service.process_text_stream(
                    manuscript_id,
                    existing_names,
                    text_queue
                ):
                    # Send detected entities to client
                    await websocket.send_json(result)
                    print(f"📤 Sent {len(result['new_entities'])} entity suggestions")

                    # Update existing entities list to avoid duplicates
                    for entity in result['new_entities']:
                        existing_names.append(entity['name'])
            except Exception as e:
                print(f"Error processing text: {e}")

        # Run both tasks concurrently
        await asyncio.gather(
            receive_text(),
            process_and_send()
        )

    except WebSocketDisconnect:
        print(f"❌ Client disconnected: {manuscript_id}")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        realtime_nlp_service.unregister_connection(manuscript_id)
        remaining = realtime_nlp_service.active_connections.get(manuscript_id, 0)
        print(f"🔌 WebSocket closed for manuscript: {manuscript_id} ({remaining} remaining)")

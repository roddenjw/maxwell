"""
Real-time API Routes (WebSocket)
Live entity detection and suggestions with database persistence
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
import json
import asyncio

from app.database import get_db, SessionLocal
from app.services.realtime_nlp_service import realtime_nlp_service
from app.services.codex_service import codex_service
from app.models.entity import Entity, EntitySuggestion

router = APIRouter(prefix="/api/realtime", tags=["realtime"])


def persist_entity_suggestion(manuscript_id: str, entity_data: dict) -> dict:
    """
    Persist a detected entity to the database as a suggestion.
    Returns the entity data with suggestion_id added.
    """
    db = SessionLocal()
    try:
        # Check for existing pending suggestion with same name
        existing = db.query(EntitySuggestion).filter(
            EntitySuggestion.manuscript_id == manuscript_id,
            EntitySuggestion.name == entity_data['name'],
            EntitySuggestion.status == "PENDING"
        ).first()

        if existing:
            # Return existing suggestion ID
            entity_data['suggestion_id'] = existing.id
            entity_data['is_new'] = False
            return entity_data

        # Also check if entity already exists in codex
        existing_entity = db.query(Entity).filter(
            Entity.manuscript_id == manuscript_id,
            Entity.name == entity_data['name']
        ).first()

        if existing_entity:
            # Skip - entity already in codex
            entity_data['suggestion_id'] = None
            entity_data['is_new'] = False
            entity_data['already_in_codex'] = True
            return entity_data

        # Create new suggestion
        suggestion = EntitySuggestion(
            manuscript_id=manuscript_id,
            name=entity_data['name'],
            type=entity_data['type'],
            context=entity_data.get('context', ''),
            status="PENDING"
        )
        db.add(suggestion)
        db.commit()
        db.refresh(suggestion)

        entity_data['suggestion_id'] = suggestion.id
        entity_data['is_new'] = True

        print(f"💾 Persisted entity suggestion: {entity_data['name']} (ID: {suggestion.id})")
        return entity_data
    except Exception as e:
        print(f"Error persisting entity suggestion: {e}")
        db.rollback()
        entity_data['suggestion_id'] = None
        entity_data['is_new'] = False
        return entity_data
    finally:
        db.close()


@router.websocket("/nlp/{manuscript_id}")
async def websocket_nlp_endpoint(
    websocket: WebSocket,
    manuscript_id: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time entity detection

    Client sends: {"text_delta": "newly typed text"}
    Client sends: {"type": "config", "settings": {...}} for extraction settings
    Server sends: {"new_entities": [...], "timestamp": "...", "type": "entities"}
    Server sends: {"type": "pong"} for keep-alive
    """
    # Check connection limit
    if not realtime_nlp_service.can_accept_connection(manuscript_id):
        await websocket.close(code=1008, reason="Too many connections for this manuscript")
        print(f"❌ Connection rejected for {manuscript_id}: too many connections")
        return

    await websocket.accept()
    realtime_nlp_service.register_connection(manuscript_id)
    print(f"✨ WebSocket connected for manuscript: {manuscript_id} ({realtime_nlp_service.active_connections.get(manuscript_id, 0)} active)")

    # Client-specific settings (can be updated via config messages)
    client_settings = {
        'enabled': True,
        'debounce_delay': 2.0,  # seconds
        'confidence_threshold': 'medium',  # low, medium, high
        'entity_types': ['CHARACTER', 'LOCATION', 'ITEM', 'LORE']  # types to detect
    }

    try:
        # Get existing entities from database (cached per connection)
        existing_entities = db.query(Entity).filter_by(
            manuscript_id=manuscript_id
        ).all()
        existing_names = [e.name for e in existing_entities]

        # Also get pending suggestions to avoid duplicates
        pending_suggestions = db.query(EntitySuggestion).filter_by(
            manuscript_id=manuscript_id,
            status="PENDING"
        ).all()
        existing_names.extend([s.name for s in pending_suggestions])

        # Close database session early to free connection
        db.close()

        # Create a queue for incoming text
        text_queue = asyncio.Queue()

        # Start background processor
        async def receive_text():
            """Receive text deltas from client and add to queue"""
            nonlocal client_settings
            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)

                    if 'text_delta' in message:
                        if client_settings['enabled']:
                            await text_queue.put(message['text_delta'])
                    elif message.get('type') == 'ping':
                        # Respond to keep-alive pings
                        await websocket.send_json({"type": "pong"})
                    elif message.get('type') == 'config':
                        # Update client settings
                        settings = message.get('settings', {})
                        if 'enabled' in settings:
                            client_settings['enabled'] = settings['enabled']
                        if 'debounce_delay' in settings:
                            client_settings['debounce_delay'] = float(settings['debounce_delay'])
                        if 'confidence_threshold' in settings:
                            client_settings['confidence_threshold'] = settings['confidence_threshold']
                        if 'entity_types' in settings:
                            client_settings['entity_types'] = settings['entity_types']

                        # Update service debounce delay
                        realtime_nlp_service.debounce_delay = client_settings['debounce_delay']

                        await websocket.send_json({
                            "type": "config_ack",
                            "settings": client_settings
                        })
                        print(f"⚙️ Updated extraction settings: {client_settings}")
            except WebSocketDisconnect:
                print(f"❌ WebSocket disconnected: {manuscript_id}")
            except Exception as e:
                print(f"Error receiving text: {e}")

        async def process_and_send():
            """Process text queue and send entity suggestions"""
            nonlocal existing_names
            try:
                async for result in realtime_nlp_service.process_text_stream(
                    manuscript_id,
                    existing_names,
                    text_queue
                ):
                    # Filter by configured entity types
                    filtered_entities = [
                        e for e in result['new_entities']
                        if e['type'] in client_settings['entity_types']
                    ]

                    if not filtered_entities:
                        continue

                    # Persist each entity to database and get suggestion IDs
                    persisted_entities = []
                    for entity in filtered_entities:
                        persisted = persist_entity_suggestion(manuscript_id, entity)
                        # Only include new suggestions (not duplicates or already in codex)
                        if persisted.get('is_new') or persisted.get('suggestion_id'):
                            if not persisted.get('already_in_codex'):
                                persisted_entities.append(persisted)

                    if persisted_entities:
                        # Send detected entities to client with suggestion IDs
                        response = {
                            "type": "entities",
                            "new_entities": persisted_entities,
                            "timestamp": result['timestamp']
                        }
                        await websocket.send_json(response)
                        print(f"📤 Sent {len(persisted_entities)} entity suggestions (persisted)")

                        # Update existing entities list to avoid duplicates
                        for entity in persisted_entities:
                            if entity['name'] not in existing_names:
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

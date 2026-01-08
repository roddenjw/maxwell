"""
Test script to verify manuscript context retrieval for AI analysis
"""
import sys
sys.path.append('/Users/josephrodden/Maxwell/backend')

from app.database import SessionLocal
from app.models.outline import Outline
from app.services.ai_outline_service import _get_manuscript_context

# Test with Testing SciFi manuscript
outline_id = "23402690-44ac-49d5-9965-0284b8415753"

db = SessionLocal()
try:
    outline = db.query(Outline).filter(Outline.id == outline_id).first()

    if not outline:
        print(f"❌ Outline not found: {outline_id}")
        sys.exit(1)

    print(f"✅ Found outline: {outline.structure_type}")
    print(f"📄 Manuscript ID: {outline.manuscript_id}")
    print(f"📝 Premise: {outline.premise[:100]}..." if outline.premise else "No premise")
    print()

    # Call the context function
    print("🔍 Retrieving manuscript context...")
    context = _get_manuscript_context(db, outline)

    print()
    print("="*80)
    print("MANUSCRIPT CONTEXT RESULT:")
    print("="*80)
    print(f"Total length: {len(context)} characters")
    print()
    print("First 1000 characters:")
    print(context[:1000])
    print()
    print("="*80)

    if context == "No chapters written yet.":
        print("❌ No chapters found!")
    else:
        print(f"✅ Successfully retrieved {len(context)} characters of manuscript context")

        # Check if it includes chapter markers
        if "## Hook [LINKED TO BEAT]" in context:
            print("✅ Linked chapter 'Hook' is included")
        else:
            print("⚠️  Linked chapter 'Hook' not found in context")

finally:
    db.close()

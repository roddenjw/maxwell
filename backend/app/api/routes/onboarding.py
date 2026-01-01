"""
Onboarding API Routes
Handles new user onboarding and sample content creation
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app.database import get_db
from app.models.manuscript import Manuscript, Chapter

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


@router.post("/create-sample-manuscript")
async def create_sample_manuscript(
    db: Session = Depends(get_db)
):
    """
    Create a sample manuscript for new users to explore

    Returns:
        Created manuscript with sample chapters
    """
    try:
        # Create sample manuscript
        manuscript = Manuscript(
            title="Welcome to Maxwell - Sample Novel",
            author="Maxwell Demo",
            description="A sample manuscript to help you explore Maxwell's features",
            word_count=0,
            lexical_state="",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(manuscript)
        db.flush()

        # Sample chapter content
        chapters_data = [
            {
                "title": "Chapter 1: The Beginning",
                "content": """The old library stood at the edge of town, its weathered stone walls whispering secrets to anyone who would listen.

Sarah pushed through the heavy oak door, the familiar scent of aged paper and leather welcoming her like an old friend. This place had been her sanctuary for three years now, ever since she'd discovered the truth about her grandmother's past.

"You're late," Marcus called from behind the reference desk. His green eyes sparkled with amusement as he shelved a stack of books. "I was beginning to think you'd forgotten about me."

She smiled, shaking raindrops from her umbrella. "Never. Just got caught up researching the Obsidian Dagger legend. I think I found something."

Marcus straightened, suddenly serious. "The dagger that supposedly grants its wielder the power to see the future?"

"The very one." Sarah pulled a leather journal from her bag, its pages yellowed with age. "My grandmother's diary. She mentions it on page forty-seven."

They huddled together over the ancient book, unaware that in the shadows, someone was watching. Someone who had been searching for that diary for a very long time.""",
                "order_index": 0
            },
            {
                "title": "Chapter 2: The Discovery",
                "content": """The diary's pages crackled as Sarah turned them carefully. Her grandmother's elegant handwriting filled every line, chronicling adventures that seemed impossible.

"Listen to this," she whispered, reading aloud. "'The Obsidian Dagger lies beneath the city, in the catacombs where light fears to tread. Only those with the Sight can find it, and only the pure of heart can wield it without losing themselves to its power.'"

Marcus leaned closer, his shoulder brushing hers. "The catacombs? Those have been sealed for over a century."

"Not all of them." Sarah's finger traced a map sketched in the margin. "This shows an entrance I've never seen before. Behind the old cathedral, in the cemetery."

A floorboard creaked in the distance. Both of them froze.

"Did you hear that?" Marcus asked, his voice barely audible.

Before Sarah could answer, the lights flickered and went out, plunging them into darkness. In the silence that followed, they heard footsteps approaching—slow, deliberate, purposeful.

Sarah's hand found Marcus's in the dark. Whatever was coming, they would face it together.""",
                "order_index": 1
            },
            {
                "title": "Chapter 3: The Choice",
                "content": """The footsteps stopped just outside their hiding place behind the ancient atlas section.

Sarah held her breath, clutching the diary against her chest. Marcus's hand tightened around hers, steady and reassuring despite the danger.

"I know you're here, Sarah Chen." The voice was familiar—too familiar. Professor Elara Blackwood, the literature department head. But something was different about her tone. Harder. Colder.

"Your grandmother made a choice twenty years ago," Professor Blackwood continued, her footsteps resuming. "She chose to hide the dagger rather than use it. I won't make that mistake."

Sarah's mind raced. Professor Blackwood had been her mentor, her guide through the labyrinth of ancient texts and forgotten languages. How long had she been searching for this?

"We need to move," Marcus breathed into her ear. "There's a service exit behind the periodicals."

Sarah nodded, making her decision. They couldn't let Blackwood find the dagger first. Whatever power it held, it wasn't meant for someone who saw it as merely a tool for personal gain.

As they crept through the shadows, Sarah realized this was just the beginning. The library that had been her refuge was now the starting point of an adventure she couldn't have imagined. And somewhere in the catacombs beneath the city, the Obsidian Dagger waited.""",
                "order_index": 2
            }
        ]

        # Create chapters with proper Lexical state
        for i, chapter_data in enumerate(chapters_data):
            # Convert plain text to Lexical format
            paragraphs = chapter_data["content"].split('\n\n')

            # Create Lexical nodes for each paragraph
            children = []
            for para_text in paragraphs:
                if para_text.strip():
                    children.append({
                        "children": [
                            {
                                "detail": 0,
                                "format": 0,
                                "mode": "normal",
                                "style": "",
                                "text": para_text.strip(),
                                "type": "text",
                                "version": 1
                            }
                        ],
                        "direction": "ltr",
                        "format": "",
                        "indent": 0,
                        "type": "paragraph",
                        "version": 1
                    })

            # Create Lexical state
            lexical_state = {
                "root": {
                    "children": children,
                    "direction": "ltr",
                    "format": "",
                    "indent": 0,
                    "type": "root",
                    "version": 1
                }
            }

            # Count words
            word_count = len(chapter_data["content"].split())

            chapter = Chapter(
                manuscript_id=manuscript.id,
                parent_id=None,
                title=chapter_data["title"],
                is_folder=False,
                order_index=chapter_data["order_index"],
                lexical_state=json.dumps(lexical_state),
                content=chapter_data["content"],
                word_count=word_count,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(chapter)

        # Update manuscript word count
        manuscript.word_count = sum(len(ch["content"].split()) for ch in chapters_data)

        db.commit()
        db.refresh(manuscript)

        return {
            "success": True,
            "data": {
                "manuscript_id": manuscript.id,
                "title": manuscript.title,
                "chapters_created": len(chapters_data),
                "total_words": manuscript.word_count
            }
        }

    except Exception as e:
        db.rollback()
        print(f"Sample manuscript creation error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create sample manuscript: {str(e)}")

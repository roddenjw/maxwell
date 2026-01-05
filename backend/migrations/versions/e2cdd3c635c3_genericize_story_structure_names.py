"""genericize_story_structure_names

Revision ID: e2cdd3c635c3
Revises: b0adcf561edc
Create Date: 2026-01-05 14:34:38.423664

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2cdd3c635c3'
down_revision: Union[str, Sequence[str], None] = 'b0adcf561edc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Genericize story structure names to remove trademark issues."""

    # Update outlines.structure_type to new generic names
    op.execute("UPDATE outlines SET structure_type = 'story-arc-9' WHERE structure_type = 'km-weiland'")
    op.execute("UPDATE outlines SET structure_type = 'screenplay-15' WHERE structure_type = 'save-the-cat'")
    op.execute("UPDATE outlines SET structure_type = 'mythic-quest' WHERE structure_type = 'heros-journey'")

    # Update plot_beats for 9-Beat Story Arc (formerly KM Weiland)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'first-pressure-point', beat_label = 'First Pressure Point'
        WHERE beat_name = 'first-pinch-point'
    """)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'second-pressure-point', beat_label = 'Second Pressure Point'
        WHERE beat_name = 'second-pinch-point'
    """)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'second-turning-point', beat_label = 'Second Turning Point'
        WHERE beat_name = 'third-plot-point'
    """)

    # Update plot_beats for 15-Beat Screenplay (formerly Save the Cat)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'story-opening', beat_label = 'Story Opening'
        WHERE beat_name = 'opening-image'
    """)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'story-closing', beat_label = 'Story Closing'
        WHERE beat_name = 'final-image'
    """)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'commitment-point', beat_label = 'Commitment Point'
        WHERE beat_name = 'break-into-two'
    """)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'rising-opposition', beat_label = 'Rising Opposition'
        WHERE beat_name = 'bad-guys-close-in'
    """)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'lowest-point', beat_label = 'Lowest Point'
        WHERE beat_name = 'all-is-lost'
    """)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'moment-of-despair', beat_label = 'Moment of Despair'
        WHERE beat_name = 'dark-night-of-soul'
    """)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'resolution-decision', beat_label = 'Resolution Decision'
        WHERE beat_name = 'break-into-three'
    """)

    # Update plot_beats for Mythic Quest (formerly Hero's Journey)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'invitation-to-change', beat_label = 'Invitation to Change'
        WHERE beat_name = 'call-to-adventure'
    """)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'hesitation', beat_label = 'Hesitation'
        WHERE beat_name = 'refusal-of-call'
    """)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'preparation', beat_label = 'Preparation for Crisis'
        WHERE beat_name = 'approach-innermost-cave'
    """)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'victory', beat_label = 'Victory and Gain'
        WHERE beat_name = 'reward'
    """)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'triumphant-return', beat_label = 'Triumphant Return'
        WHERE beat_name = 'return-with-elixir'
    """)


def downgrade() -> None:
    """Downgrade schema - Restore original trademarked names (for rollback only)."""

    # Restore outlines.structure_type to original names
    op.execute("UPDATE outlines SET structure_type = 'km-weiland' WHERE structure_type = 'story-arc-9'")
    op.execute("UPDATE outlines SET structure_type = 'save-the-cat' WHERE structure_type = 'screenplay-15'")
    op.execute("UPDATE outlines SET structure_type = 'heros-journey' WHERE structure_type = 'mythic-quest'")

    # Restore plot_beats for KM Weiland structure
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'first-pinch-point', beat_label = 'First Pinch Point'
        WHERE beat_name = 'first-pressure-point'
    """)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'second-pinch-point', beat_label = 'Second Pinch Point'
        WHERE beat_name = 'second-pressure-point'
    """)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'third-plot-point', beat_label = 'Third Plot Point'
        WHERE beat_name = 'second-turning-point'
    """)

    # Restore plot_beats for Save the Cat structure
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'opening-image', beat_label = 'Opening Image'
        WHERE beat_name = 'story-opening'
    """)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'final-image', beat_label = 'Final Image'
        WHERE beat_name = 'story-closing'
    """)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'break-into-two', beat_label = 'Break Into Two'
        WHERE beat_name = 'commitment-point'
    """)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'bad-guys-close-in', beat_label = 'Bad Guys Close In'
        WHERE beat_name = 'rising-opposition'
    """)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'all-is-lost', beat_label = 'All Is Lost'
        WHERE beat_name = 'lowest-point'
    """)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'dark-night-of-soul', beat_label = 'Dark Night of the Soul'
        WHERE beat_name = 'moment-of-despair'
    """)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'break-into-three', beat_label = 'Break Into Three'
        WHERE beat_name = 'resolution-decision'
    """)

    # Restore plot_beats for Hero's Journey structure
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'call-to-adventure', beat_label = 'Call to Adventure'
        WHERE beat_name = 'invitation-to-change'
    """)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'refusal-of-call', beat_label = 'Refusal of the Call'
        WHERE beat_name = 'hesitation'
    """)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'approach-innermost-cave', beat_label = 'Approach to the Inmost Cave'
        WHERE beat_name = 'preparation'
    """)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'reward', beat_label = 'Reward (Seizing the Sword)'
        WHERE beat_name = 'victory'
    """)
    op.execute("""
        UPDATE plot_beats
        SET beat_name = 'return-with-elixir', beat_label = 'Return with the Elixir'
        WHERE beat_name = 'triumphant-return'
    """)


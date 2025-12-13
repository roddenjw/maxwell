"""
Knowledge graph service using KuzuDB
Stores entity relationships and story structure
"""

import kuzu
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Initialize data directory
DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
GRAPH_DIR = DATA_DIR / "graph"
GRAPH_DIR.mkdir(parents=True, exist_ok=True)


class GraphService:
    """Service for managing knowledge graph"""

    def __init__(self):
        # Initialize KuzuDB
        self.db = kuzu.Database(str(GRAPH_DIR))
        self.conn = kuzu.Connection(self.db)

        # Initialize schema
        self._init_schema()

    def _init_schema(self):
        """Initialize graph schema if not exists"""
        try:
            # Create Entity node table
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS Entity(
                    entity_id STRING,
                    manuscript_id STRING,
                    type STRING,
                    name STRING,
                    PRIMARY KEY (entity_id)
                )
            """)

            # Create Scene node table
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS Scene(
                    scene_id STRING,
                    manuscript_id STRING,
                    position INT64,
                    PRIMARY KEY (scene_id)
                )
            """)

            # Create APPEARS_IN relationship (Entity -> Scene)
            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS APPEARS_IN(
                    FROM Entity TO Scene,
                    description STRING
                )
            """)

            # Create RELATES_TO relationship (Entity -> Entity)
            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS RELATES_TO(
                    FROM Entity TO Entity,
                    relationship_type STRING,
                    strength INT64
                )
            """)

            # Create FOLLOWS relationship (Scene -> Scene)
            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS FOLLOWS(
                    FROM Scene TO Scene
                )
            """)

        except Exception as e:
            # Schema might already exist
            print(f"Schema initialization note: {e}")

    def add_entity_node(
        self,
        entity_id: str,
        manuscript_id: str,
        entity_type: str,
        name: str
    ):
        """Add or update entity node"""
        # Delete if exists (upsert pattern)
        try:
            self.conn.execute(f"""
                MATCH (e:Entity {{entity_id: '{entity_id}'}})
                DELETE e
            """)
        except Exception:
            pass  # Node doesn't exist yet

        # Create node
        self.conn.execute(f"""
            CREATE (:Entity {{
                entity_id: '{entity_id}',
                manuscript_id: '{manuscript_id}',
                type: '{entity_type}',
                name: '{name}'
            }})
        """)

    def add_scene_node(
        self,
        scene_id: str,
        manuscript_id: str,
        position: int
    ):
        """Add or update scene node"""
        # Delete if exists
        try:
            self.conn.execute(f"""
                MATCH (s:Scene {{scene_id: '{scene_id}'}})
                DELETE s
            """)
        except Exception:
            pass

        # Create node
        self.conn.execute(f"""
            CREATE (:Scene {{
                scene_id: '{scene_id}',
                manuscript_id: '{manuscript_id}',
                position: {position}
            }})
        """)

    def add_entity_appearance(
        self,
        entity_id: str,
        scene_id: str,
        description: str = ""
    ):
        """Record entity appearing in a scene"""
        self.conn.execute(f"""
            MATCH (e:Entity {{entity_id: '{entity_id}'}}),
                  (s:Scene {{scene_id: '{scene_id}'}})
            CREATE (e)-[:APPEARS_IN {{description: '{description}'}}]->(s)
        """)

    def add_entity_relationship(
        self,
        source_entity_id: str,
        target_entity_id: str,
        relationship_type: str,
        strength: int = 1
    ):
        """Add or update relationship between entities"""
        # Check if relationship exists
        result = self.conn.execute(f"""
            MATCH (e1:Entity {{entity_id: '{source_entity_id}'}})-[r:RELATES_TO]->(e2:Entity {{entity_id: '{target_entity_id}'}})
            RETURN r.strength as strength
        """)

        rows = result.get_as_df() if result else None

        if rows is not None and len(rows) > 0:
            # Update existing relationship
            old_strength = rows.iloc[0]['strength']
            new_strength = old_strength + strength

            self.conn.execute(f"""
                MATCH (e1:Entity {{entity_id: '{source_entity_id}'}})-[r:RELATES_TO]->(e2:Entity {{entity_id: '{target_entity_id}'}})
                SET r.strength = {new_strength}
            """)
        else:
            # Create new relationship
            self.conn.execute(f"""
                MATCH (e1:Entity {{entity_id: '{source_entity_id}'}}),
                      (e2:Entity {{entity_id: '{target_entity_id}'}})
                CREATE (e1)-[:RELATES_TO {{
                    relationship_type: '{relationship_type}',
                    strength: {strength}
                }}]->(e2)
            """)

    def link_scenes(self, from_scene_id: str, to_scene_id: str):
        """Link consecutive scenes"""
        self.conn.execute(f"""
            MATCH (s1:Scene {{scene_id: '{from_scene_id}'}}),
                  (s2:Scene {{scene_id: '{to_scene_id}'}})
            CREATE (s1)-[:FOLLOWS]->(s2)
        """)

    def get_entity_appearances(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get all scenes where an entity appears"""
        result = self.conn.execute(f"""
            MATCH (e:Entity {{entity_id: '{entity_id}'}})-[a:APPEARS_IN]->(s:Scene)
            RETURN s.scene_id as scene_id,
                   s.position as position,
                   a.description as description
            ORDER BY s.position
        """)

        df = result.get_as_df()
        return df.to_dict('records') if df is not None else []

    def get_entity_relationships(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get all relationships for an entity"""
        result = self.conn.execute(f"""
            MATCH (e1:Entity {{entity_id: '{entity_id}'}})-[r:RELATES_TO]-(e2:Entity)
            RETURN e2.entity_id as related_entity_id,
                   e2.name as related_entity_name,
                   e2.type as related_entity_type,
                   r.relationship_type as relationship_type,
                   r.strength as strength
        """)

        df = result.get_as_df()
        return df.to_dict('records') if df is not None else []

    def get_manuscript_graph(self, manuscript_id: str) -> Dict[str, Any]:
        """Get complete graph data for a manuscript"""
        # Get all entities
        entities_result = self.conn.execute(f"""
            MATCH (e:Entity {{manuscript_id: '{manuscript_id}'}})
            RETURN e.entity_id as id,
                   e.name as name,
                   e.type as type
        """)

        # Get all relationships
        relationships_result = self.conn.execute(f"""
            MATCH (e1:Entity {{manuscript_id: '{manuscript_id}'}})-[r:RELATES_TO]->(e2:Entity)
            RETURN e1.entity_id as source,
                   e2.entity_id as target,
                   r.relationship_type as type,
                   r.strength as strength
        """)

        entities_df = entities_result.get_as_df() if entities_result else None
        relationships_df = relationships_result.get_as_df() if relationships_result else None

        return {
            "entities": entities_df.to_dict('records') if entities_df is not None else [],
            "relationships": relationships_df.to_dict('records') if relationships_df is not None else []
        }

    def delete_entity(self, entity_id: str):
        """Delete entity and all its relationships"""
        self.conn.execute(f"""
            MATCH (e:Entity {{entity_id: '{entity_id}'}})
            DETACH DELETE e
        """)

    def delete_scene(self, scene_id: str):
        """Delete scene and all its relationships"""
        self.conn.execute(f"""
            MATCH (s:Scene {{scene_id: '{scene_id}'}})
            DETACH DELETE s
        """)

    def delete_manuscript_graph(self, manuscript_id: str):
        """Delete all graph data for a manuscript"""
        # Delete entities
        self.conn.execute(f"""
            MATCH (e:Entity {{manuscript_id: '{manuscript_id}'}})
            DETACH DELETE e
        """)

        # Delete scenes
        self.conn.execute(f"""
            MATCH (s:Scene {{manuscript_id: '{manuscript_id}'}})
            DETACH DELETE s
        """)


# Global instance
graph_service = GraphService()

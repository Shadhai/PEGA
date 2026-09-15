"""
CINT-70 Graph Database Schema
Models physical constraints as a knowledge graph
"""
import kuzu
import json
import os

class ConstraintGraph:
    def __init__(self, db_path="data/graph_db"):
        os.makedirs(db_path, exist_ok=True)
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self._create_schema()
        self._load_data()
    
    def _create_schema(self):
        """Create graph schema"""
        try:
            self.conn.execute("CREATE NODE TABLE Component(name STRING, type STRING, PRIMARY KEY(name))")
        except:
            pass  # Already exists
        
        try:
            self.conn.execute("CREATE NODE TABLE Constraint(id SERIAL, type STRING, value DOUBLE, unit STRING, description STRING, PRIMARY KEY(id))")
        except:
            pass
        
        try:
            self.conn.execute("CREATE REL TABLE HAS_LIMIT(FROM Component TO Constraint)")
        except:
            pass
        
        try:
            self.conn.execute("CREATE REL TABLE OBSTRUCTS(FROM Component TO Component, distance_m DOUBLE)")
        except:
            pass
    
    def _load_data(self):
        """Load constraint data into graph"""
        # Load joints
        import csv
        joints_file = "data/raw/spdm_joint_limits.csv"
        if os.path.exists(joints_file):
            with open(joints_file) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        self.conn.execute(
                            f"MERGE (c:Component {{name: '{row['joint_name']}', type: 'joint'}})"
                        )
                        # Add min limit
                        self.conn.execute(
                            f"CREATE (l:Constraint {{type: 'joint_limit_min', value: {row['min_deg']}, unit: 'degrees', description: 'Minimum angle'}})"
                        )
                        self.conn.execute(
                            f"MATCH (c:Component {{name: '{row['joint_name']}'}}), (l:Constraint) "
                            f"WHERE l.type = 'joint_limit_min' AND l.value = {row['min_deg']} "
                            f"CREATE (c)-[:HAS_LIMIT]->(l)"
                        )
                        # Add max limit
                        self.conn.execute(
                            f"CREATE (m:Constraint {{type: 'joint_limit_max', value: {row['max_deg']}, unit: 'degrees', description: 'Maximum angle'}})"
                        )
                        self.conn.execute(
                            f"MATCH (c:Component {{name: '{row['joint_name']}'}}), (m:Constraint) "
                            f"WHERE m.type = 'joint_limit_max' AND m.value = {row['max_deg']} "
                            f"CREATE (c)-[:HAS_LIMIT]->(m)"
                        )
                    except Exception as e:
                        print(f"  Graph load note: {e}")
        
        # Add obstacles
        obstacles = [
            ("solar_panel", "obstacle"),
            ("antenna_array", "obstacle"),
            ("rover_body", "obstacle"),
            ("tool_holster", "equipment"),
            ("workbench", "equipment"),
        ]
        for name, otype in obstacles:
            try:
                self.conn.execute(
                    f"MERGE (c:Component {{name: '{name}', type: '{otype}'}})"
                )
            except:
                pass
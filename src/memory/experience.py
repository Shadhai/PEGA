# ============================================================
# src/memory/experience.py  (Thread‑safe)
# ============================================================

import sqlite3
import json
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer

class ExperienceMemory:
    def __init__(self, db_path: str = "data/experience.db"):
        self.db_path = db_path
        self.embedder = SentenceTransformer("./models/minilm")
        self._init_tables()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_tables(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS experiences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT,
                command TEXT,
                plan_json TEXT,
                outcome TEXT,
                trust_score REAL,
                violations TEXT,
                recovery_count INTEGER,
                safe_coordinates TEXT,
                embedding BLOB,
                timestamp TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS failure_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                obstacle_name TEXT,
                collision_point TEXT,
                safe_alternatives TEXT,
                frequency INTEGER DEFAULT 1
            )
        """)
        conn.commit()
        conn.close()

    def store_experience(self, command: str, plan: List[Dict], outcome: str,
                         trust_score: float, violations: List[Dict],
                         recovery_count: int, safe_coords: Optional[List] = None):
        task_type = self._classify_task(command)
        embedding = self.embedder.encode([command])[0]
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO experiences
               (task_type, command, plan_json, outcome, trust_score,
                violations, recovery_count, safe_coordinates, embedding, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                task_type,
                command,
                json.dumps(plan),
                outcome,
                trust_score,
                json.dumps(violations),
                recovery_count,
                json.dumps(safe_coords) if safe_coords else None,
                embedding.tobytes(),
                datetime.now().isoformat()
            )
        )
        conn.commit()
        conn.close()

    def get_similar_experiences(self, command: str, top_k: int = 3) -> List[Dict]:
        query_embedding = self.embedder.encode([command])[0]
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM experiences ORDER BY id DESC LIMIT 50")
        rows = cursor.fetchall()
        conn.close()
        if not rows:
            return []

        similarities = []
        for row in rows:
            stored_embedding = row[10]
            if not isinstance(stored_embedding, bytes):
                continue

            stored_embedding = np.frombuffer(stored_embedding, dtype=np.float32)
            similarity = np.dot(query_embedding, stored_embedding)
            similarities.append((similarity, row))

        similarities.sort(key=lambda x: x[0], reverse=True)

        results = []
        for sim, row in similarities[:top_k]:
            if sim > 0.3:
                results.append({
                    "similarity": float(sim),
                    "task_type": row[1],
                    "command": row[2],
                    "plan": json.loads(row[3]),
                    "outcome": row[4],
                    "trust_score": row[5],
                    "safe_coordinates": json.loads(row[8]) if row[8] else None,
                    "recovery_count": row[7]
                })
            return results
        query_embedding = self.embedder.encode([command])[0]
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM experiences ORDER BY id DESC LIMIT 50")
        rows = cursor.fetchall()
        conn.close()
        if not rows:
            return []
        similarities = []
        for row in rows:
            stored_embedding = np.frombuffer(row[10], dtype=np.float32)
            similarity = np.dot(query_embedding, stored_embedding)
            similarities.append((similarity, row))
        similarities.sort(key=lambda x: x[0], reverse=True)
        results = []
        for sim, row in similarities[:top_k]:
            if sim > 0.3:
                results.append({
                    "similarity": float(sim),
                    "task_type": row[1],
                    "command": row[2],
                    "plan": json.loads(row[3]),
                    "outcome": row[4],
                    "trust_score": row[5],
                    "safe_coordinates": json.loads(row[8]) if row[8] else None,
                    "recovery_count": row[7]
                })
        return results

    def get_successful_strategies(self, task_type: str) -> List[Dict]:
        conn = self._get_conn()
        cursor = conn.execute(
            """SELECT * FROM experiences
               WHERE task_type = ? AND outcome = 'APPROVED'
               ORDER BY trust_score DESC LIMIT 5""",
            (task_type,)
        )
        rows = cursor.fetchall()
        conn.close()
        results = []
        for row in rows:
            results.append({
                "command": row[2],
                "plan": json.loads(row[3]),
                "trust_score": row[5],
                "safe_coordinates": json.loads(row[8]) if row[8] else None,
                "recovery_count": row[7]
            })
        return results

    def store_failure_pattern(self, obstacle: str, collision_point: List[float],
                              safe_alternative: List[float]):
        collision_str = json.dumps(collision_point)
        safe_str = json.dumps(safe_alternative)
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT id, frequency FROM failure_patterns WHERE obstacle_name = ?",
            (obstacle,)
        )
        row = cursor.fetchone()
        if row:
            conn.execute(
                "UPDATE failure_patterns SET frequency = frequency + 1, safe_alternatives = ? WHERE id = ?",
                (safe_str, row[0])
            )
        else:
            conn.execute(
                "INSERT INTO failure_patterns (obstacle_name, collision_point, safe_alternatives) VALUES (?, ?, ?)",
                (obstacle, collision_str, safe_str)
            )
        conn.commit()
        conn.close()

    def get_failure_patterns(self) -> List[Dict]:
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM failure_patterns ORDER BY frequency DESC LIMIT 10")
        rows = cursor.fetchall()
        conn.close()
        results = []
        for row in rows:
            results.append({
                "obstacle": row[1],
                "collision_point": json.loads(row[2]),
                "safe_alternatives": json.loads(row[3]),
                "frequency": row[4]
            })
        return results

    def get_stats(self) -> Dict:
        conn = self._get_conn()
        total = conn.execute("SELECT COUNT(*) FROM experiences").fetchone()[0]
        approved = conn.execute(
            "SELECT COUNT(*) FROM experiences WHERE outcome = 'APPROVED'"
        ).fetchone()[0]
        rejected = conn.execute(
            "SELECT COUNT(*) FROM experiences WHERE outcome = 'REJECTED'"
        ).fetchone()[0]
        failures = conn.execute("SELECT COUNT(*) FROM failure_patterns").fetchone()[0]
        conn.close()
        return {
            "total_experiences": total,
            "approved": approved,
            "rejected": rejected,
            "failure_patterns": failures,
            "approval_rate": f"{(approved/total*100):.1f}%" if total > 0 else "N/A"
        }

    def _classify_task(self, command: str) -> str:
        command_lower = command.lower()
        if any(w in command_lower for w in ["repair", "thermal", "shield"]):
            return "repair"
        elif any(w in command_lower for w in ["inspect", "camera", "antenna"]):
            return "inspect"
        elif any(w in command_lower for w in ["replace", "wrench", "remove"]):
            return "replace"
        elif any(w in command_lower for w in ["sample", "scoop", "regolith"]):
            return "sample"
        elif any(w in command_lower for w in ["leak", "detector", "ammonia"]):
            return "leak_check"
        return "general"
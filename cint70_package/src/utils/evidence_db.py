"""
Queryable evidence database for CINT-70.

Stores every validation run and its violations in SQLite,
so they can be searched, aggregated, and joined with task metadata.

Schema:
    runs              - one row per execution
    violations        - one row per violation found in a run
    evidence_entries  - one row per source cited in a run
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


DB_PATH = Path("data/evidence.db")


class EvidenceDB:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    # ------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------
    def _init_schema(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id           INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp        TEXT NOT NULL,
                task_id          TEXT,
                command          TEXT,
                expected_safe    INTEGER,   -- 1 = safe, 0 = unsafe
                approved         INTEGER,   -- 1 = approved, 0 = rejected
                trust_score      REAL,
                num_steps        INTEGER,
                num_violations   INTEGER,
                recovery_count   INTEGER,
                stage            TEXT,
                plan_json        TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS violations (
                violation_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id           INTEGER NOT NULL,
                step_id          INTEGER,
                violation_type   TEXT,
                severity         REAL,
                message          TEXT,
                evidence_source  TEXT,
                FOREIGN KEY (run_id) REFERENCES runs(run_id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS evidence_entries (
                entry_id         INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id           INTEGER NOT NULL,
                source           TEXT,
                doc_or_node      TEXT,
                citation         TEXT,
                FOREIGN KEY (run_id) REFERENCES runs(run_id)
            )
        """)

        # Indexes for the queries we will run most often
        cur.execute("CREATE INDEX IF NOT EXISTS idx_runs_task ON runs(task_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_runs_approved ON runs(approved)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_violations_type ON violations(violation_type)")

        conn.commit()
        conn.close()

    # ------------------------------------------------------------
    # Write
    # ------------------------------------------------------------
    def log_run(
        self,
        task_id: str,
        command: str,
        expected_safe: bool,
        approved: bool,
        trust_score: float,
        plan: List[Dict[str, Any]],
        violations: List[Dict[str, Any]],
        recovery_count: int,
        stage: str,
        evidence_log: Optional[List[Dict[str, Any]]] = None,
    ) -> int:
        """Insert a full run and its violations. Returns run_id."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO runs (
                timestamp, task_id, command, expected_safe, approved,
                trust_score, num_steps, num_violations, recovery_count,
                stage, plan_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            task_id,
            command,
            int(expected_safe),
            int(approved),
            float(trust_score),
            len(plan),
            len(violations),
            int(recovery_count),
            stage,
            json.dumps(plan),
        ))

        run_id = cur.lastrowid

        # Violations
        for v in violations:
            cur.execute("""
                INSERT INTO violations (
                    run_id, step_id, violation_type, severity,
                    message, evidence_source
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                v.get("step_id"),
                v.get("type"),
                float(v.get("severity", 0.0)),
                v.get("message", ""),
                v.get("evidence", ""),
            ))

        # Evidence entries (citations)
        if evidence_log:
            for e in evidence_log:
                cur.execute("""
                    INSERT INTO evidence_entries (
                        run_id, source, doc_or_node, citation
                    ) VALUES (?, ?, ?, ?)
                """, (
                    run_id,
                    e.get("source", ""),
                    e.get("doc_or_node", ""),
                    e.get("citation", ""),
                ))

        conn.commit()
        conn.close()
        return run_id

    # ------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------
    def summary(self) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        total = cur.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        approved = cur.execute("SELECT COUNT(*) FROM runs WHERE approved=1").fetchone()[0]
        rejected = total - approved

        avg_trust = cur.execute("SELECT AVG(trust_score) FROM runs").fetchone()[0] or 0.0
        total_violations = cur.execute("SELECT COUNT(*) FROM violations").fetchone()[0]

        conn.close()
        return {
            "total_runs": total,
            "approved": approved,
            "rejected": rejected,
            "avg_trust": avg_trust,
            "total_violations": total_violations,
        }

    def violations_by_type(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT violation_type, COUNT(*) AS n
            FROM violations
            GROUP BY violation_type
            ORDER BY n DESC
        """)
        rows = [{"type": r[0], "count": r[1]} for r in cur.fetchall()]
        conn.close()
        return rows

    def worst_obstacles(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Which obstacles caused the most collisions?"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT message, COUNT(*) AS n
            FROM violations
            WHERE violation_type = 'collision'
            GROUP BY message
            ORDER BY n DESC
            LIMIT ?
        """, (top_n,))
        rows = [{"obstacle_msg": r[0], "count": r[1]} for r in cur.fetchall()]
        conn.close()
        return rows

    def task_pass_rates(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT task_id,
                   COUNT(*) AS total,
                   SUM(approved) AS approved,
                   ROUND(AVG(trust_score), 3) AS avg_trust
            FROM runs
            GROUP BY task_id
            ORDER BY task_id
        """)
        rows = [
            {
                "task_id": r[0],
                "total": r[1],
                "approved": r[2],
                "pass_rate": r[2] / r[1] if r[1] else 0.0,
                "avg_trust": r[3],
            }
            for r in cur.fetchall()
        ]
        conn.close()
        return rows

    def rejected_plans(self, limit: int = 20) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT run_id, task_id, command, trust_score, num_violations
            FROM runs
            WHERE approved = 0
            ORDER BY run_id DESC
            LIMIT ?
        """, (limit,))
        rows = [
            {
                "run_id": r[0],
                "task_id": r[1],
                "command": r[2][:80],
                "trust_score": r[3],
                "violations": r[4],
            }
            for r in cur.fetchall()
        ]
        conn.close()
        return rows


# ------------------------------------------------------------
# Standalone CLI for quick queries
# ------------------------------------------------------------
if __name__ == "__main__":
    import sys
    db = EvidenceDB()

    cmd = sys.argv[1] if len(sys.argv) > 1 else "summary"

    if cmd == "summary":
        print(json.dumps(db.summary(), indent=2))
    elif cmd == "violations":
        print(json.dumps(db.violations_by_type(), indent=2))
    elif cmd == "obstacles":
        print(json.dumps(db.worst_obstacles(), indent=2))
    elif cmd == "tasks":
        for r in db.task_pass_rates():
            print(r)
    elif cmd == "rejected":
        for r in db.rejected_plans():
            print(r)
    else:
        print(f"Unknown command: {cmd}")
        print("Usage: python -m src.utils.evidence_db [summary|violations|obstacles|tasks|rejected]")
"""
One-time migration of JSON evidence files into data/evidence.db.

JSON evidence remains available as the raw audit backup. Historical files
created before task metadata was added are migrated with task_id=unknown and
expected_safe=True when those fields are absent.
"""

import json
from pathlib import Path

from src.utils.evidence_db import EvidenceDB


def main() -> None:
    db = EvidenceDB()
    count = 0
    skipped = 0

    for path in sorted(Path("logs/evidence").glob("*.json")):
        try:
            with path.open(encoding="utf-8") as file:
                data = json.load(file)

            db.log_run(
                task_id=data.get("task_id", "unknown"),
                command=data.get("command", ""),
                expected_safe=data.get("expected_safe", True),
                approved=data.get("stage") == "approved",
                trust_score=data.get("trust_score", 0.0),
                plan=data.get("plan", []),
                violations=data.get("violations", []),
                recovery_count=data.get("recovery_count", 0),
                stage=data.get("stage", ""),
                evidence_log=data.get("evidence_log", []),
            )
            count += 1
        except Exception as error:
            skipped += 1
            print(f"  Skip {path.name}: {error}")

    print(f"\nMigrated {count} evidence files; skipped {skipped}.")
    print(json.dumps(db.summary(), indent=2))


if __name__ == "__main__":
    main()

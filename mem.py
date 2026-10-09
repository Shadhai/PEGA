import sqlite3
conn = sqlite3.connect("data/experience.db")

# How many experiences stored
total = conn.execute("SELECT COUNT(*) FROM experiences").fetchone()[0]
print(f"Total experiences: {total}")

# How many distinct safe coordinates were discovered
coords = conn.execute("""
    SELECT DISTINCT safe_coordinates
    FROM experiences
    WHERE outcome='APPROVED' AND safe_coordinates IS NOT NULL
""").fetchall()
print(f"Distinct safe coordinates learned: {len(coords)}")
for c in coords:
    print(f"  {c[0]}")

# Which task types have been learned
task_types = conn.execute("""
    SELECT task_type, COUNT(*)
    FROM experiences
    WHERE outcome='APPROVED'
    GROUP BY task_type
""").fetchall()
print(f"\nTask types learned:")
for t, n in task_types:
    print(f"  {t}: {n} entries")

conn.close()
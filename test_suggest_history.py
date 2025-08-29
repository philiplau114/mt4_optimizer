import sqlite3
import os

def build_ancestry_chain(conn, start_set_file_name):
    # Step 1: Build a mapping from set_file_name to input_set_file for all rows
    cur = conn.cursor()
    cur.execute("SELECT set_file_name, input_set_file FROM test_metrics")
    file_map = {}
    for row in cur.fetchall():
        file_map[row[0]] = row[1]

    # Step 2: Recursively walk ancestors
    ancestry = []
    current = start_set_file_name
    while current and current not in ancestry:
        ancestry.append(current)
        input_file = file_map.get(current)
        if input_file:
            parent = os.path.basename(input_file)
            if parent == current:  # avoid infinite loop if data is bad
                break
            current = parent
        else:
            break
    return ancestry

def fetch_suggestions_for_ancestry(conn, ancestry):
    print(ancestry)
    placeholders = ','.join(['?'] * len(ancestry))
    sql = f"""
    SELECT 
      s.id AS step_id,
      sug.id AS suggestion_id,
      sug.mode,
      sec.section_name,
      sec.explanation,
      p.parameter_name,
      p.start,
      p.end,
      p.step,
      p.reason,
      sug.created_at,
      tm.set_file_name,
      tm.input_set_file
    FROM set_file_steps AS s
    JOIN optimization_suggestion AS sug ON s.id = sug.step_id
    JOIN optimization_section AS sec ON sug.id = sec.suggestion_id
    JOIN optimization_parameter AS p ON sug.id = p.suggestion_id
    JOIN test_metrics AS tm ON tm.step_id = s.id
    WHERE tm.set_file_name IN ({placeholders})
    ORDER BY sug.created_at ASC, p.parameter_name;
    """
    cur = conn.cursor()
    cur.execute(sql, ancestry)
    return cur.fetchall()

# Usage:
conn = sqlite3.connect(r"C:\Users\Philip\Documents\GitHub\EA_Automation\EA_Automation.db")
start_set_file_name = "PX3.71_EURJPY_M30_1500_P529_DD443_20220822-20250820_SL500_WR80.05_PF1.64_T426_M504935252_V1_S257.set"
ancestry = build_ancestry_chain(conn, start_set_file_name)
rows = fetch_suggestions_for_ancestry(conn, ancestry)

# Now you can analyze `rows` for suggestion history, etc.
for row in rows:
    print(row)

from collections import Counter

param_names = [row[5] for row in rows]  # assuming 'parameter_name' is at index 5
param_counter = Counter(param_names)

history_block = [
    {"name": name, "times_suggested": count}
    for name, count in param_counter.items()
]
print(history_block)
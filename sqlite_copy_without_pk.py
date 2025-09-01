import sqlite3
import argparse
import sys
from collections import defaultdict, deque

# --- CONFIGURATION FOR FK RELATIONSHIPS IN YOUR SCHEMA ---
# Each entry: child_table: { fk_column: referenced_table }
FK_MAP = {
    "set_file_steps": {"job_id": "set_file_jobs"},
    "strategy_dashboard": {"job_id": "set_file_jobs"},
    "lot_analysis": {"step_id": "set_file_steps"},
    "trades": {"step_id": "set_file_steps"},
    "test_metrics": {"step_id": "set_file_steps"},
    "set_file_artifacts": {"step_id": "set_file_steps"},
    "optimization_reports": {"step_id": "set_file_steps"},
    "optimization_suggestion": {"step_id": "set_file_steps"},
    "optimization_passes": {"report_id": "optimization_reports"},
    "optimization_parameter": {"suggestion_id": "optimization_suggestion"},
    "optimization_section": {"suggestion_id": "optimization_suggestion"},
}

# All tables with auto-increment id PK
ALL_TABLES_ORDERED = [
    "set_file_jobs",
    "set_file_steps",
    "strategy_dashboard",
    "lot_analysis",
    "trades",
    "test_metrics",
    "set_file_artifacts",
    "optimization_reports",
    "optimization_suggestion",
    "optimization_passes",
    "optimization_parameter",
    "optimization_section",
]

def get_table_schema(conn, table):
    rows = conn.execute(f"PRAGMA table_info('{table}')").fetchall()
    # Each row: (cid, name, type, notnull, dflt_value, pk)
    return [dict(
        name=row[1],
        type=row[2],
        notnull=row[3],
        dflt_value=row[4],
        pk=row[5]
    ) for row in rows]

def validate_schema(conn1, conn2):
    for table in ALL_TABLES_ORDERED:
        schema1 = get_table_schema(conn1, table)
        schema2 = get_table_schema(conn2, table)
        if schema1 != schema2:
            print(f"Schema mismatch in table {table}:\n{schema1}\n{schema2}")
            return False
    print("Schema validation passed.")
    return True

def topological_sort_tables():
    # Build FK dependency graph
    deps = defaultdict(set)
    for child, mapping in FK_MAP.items():
        for fk_col, parent in mapping.items():
            deps[child].add(parent)
    all_tables = set(ALL_TABLES_ORDERED)
    incoming = defaultdict(int)
    for t in all_tables:
        for dep in deps[t]:
            incoming[dep] += 1
    queue = deque([t for t in ALL_TABLES_ORDERED if incoming[t] == 0])
    order = []
    seen = set()
    while queue:
        t = queue.popleft()
        if t in seen: continue
        order.append(t)
        seen.add(t)
        for dep in deps[t]:
            incoming[dep] -= 1
            if incoming[dep] == 0:
                queue.append(dep)
    # If not all tables are included, fallback to ALL_TABLES_ORDERED
    if len(order) != len(all_tables):
        print("Warning: Could not resolve all dependencies, using default order.")
        return ALL_TABLES_ORDERED
    return order

def copy_with_fk_remap(orig_conn, tgt_conn):
    # For each table, store {old_id: new_id}
    id_map = {table: dict() for table in ALL_TABLES_ORDERED}

    # Work in dependency order
    table_order = topological_sort_tables()
    for table in table_order:
        print(f"Copying table {table} with FK remapping...")
        schema = get_table_schema(orig_conn, table)
        pk_col = None
        col_names = [col['name'] for col in schema]
        for col in schema:
            if col['pk']:
                pk_col = col['name']
                break
        # Columns to insert (omit PK)
        cols_to_insert = [c for c in col_names if c != pk_col]
        col_str = ', '.join(cols_to_insert)
        placeholders = ', '.join(['?'] * len(cols_to_insert))
        # Select all columns to get PK and all FKs
        select_sql = f"SELECT * FROM {table}"
        rows = orig_conn.execute(select_sql).fetchall()
        if not rows:
            print(f"  No rows in table {table}")
            continue
        # For each row, remap FKs as needed
        mapping = FK_MAP.get(table, {})
        inserted = 0
        for row in rows:
            asdict = dict(zip(col_names, row))
            old_id = asdict[pk_col] if pk_col else None
            # Remap all FK columns in mapping
            for fk_col, parent_table in mapping.items():
                if asdict[fk_col] is not None:
                    old_fk = asdict[fk_col]
                    new_fk = id_map[parent_table].get(old_fk)
                    if new_fk is None and old_fk is not None:
                        raise Exception(f"Missing FK mapping for {parent_table}.{old_fk} referenced in {table}.{fk_col}")
                    asdict[fk_col] = new_fk
            # Prepare insert values (omit PK col if any)
            values = [asdict[c] for c in cols_to_insert]
            cur = tgt_conn.execute(
                f"INSERT INTO {table} ({col_str}) VALUES ({placeholders})",
                values
            )
            new_id = cur.lastrowid
            if pk_col:
                id_map[table][old_id] = new_id
            inserted += 1
        print(f"  Inserted {inserted} rows into {table}")
        tgt_conn.commit()
    print("Data copy complete with FK remapping.")

def main():
    parser = argparse.ArgumentParser(description="Copy SQLite DB with FK remapping for auto-increment keys.")
    parser.add_argument("original_db_path", help="Path to source/original SQLite database")
    parser.add_argument("target_db_path", help="Path to target SQLite database")
    args = parser.parse_args()

    with sqlite3.connect(args.original_db_path) as orig_conn, sqlite3.connect(args.target_db_path) as tgt_conn:
        if not validate_schema(orig_conn, tgt_conn):
            print("Schema mismatch. Aborting copy.")
            sys.exit(1)
        copy_with_fk_remap(orig_conn, tgt_conn)

if __name__ == "__main__":
    main()
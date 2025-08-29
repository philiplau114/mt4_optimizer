import sqlite3
import sys
import json

def run_sqlite_query(db_path, sql, params=None):
    result = {}
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, json.loads(params))
        else:
            cursor.execute(sql)
        # For SELECT statements
        if sql.strip().lower().startswith("select"):
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            result['data'] = [dict(zip(columns, row)) for row in rows]
        else:
            conn.commit()
            result['rowcount'] = cursor.rowcount
            # Return lastrowid for INSERT
            if sql.strip().lower().startswith("insert"):
                result['lastrowid'] = cursor.lastrowid
        cursor.close()
        conn.close()
        result['success'] = True
    except Exception as e:
        result['success'] = False
        result['error'] = str(e)
    return json.dumps(result)

if __name__ == "__main__":
    db_path = sys.argv[1]
    sql = sys.argv[2]
    params = sys.argv[3] if len(sys.argv) > 3 else None
    print(run_sqlite_query(db_path, sql, params))
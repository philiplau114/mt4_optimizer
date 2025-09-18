import sqlite3
import sys
import json

def run_sqlite_query(db_path, sql, params=None):
    result = {}
    try:
        conn = sqlite3.connect(db_path)
        #conn.execute("PRAGMA key = 'Kh78784bt!'")

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

# if __name__ == "__main__":
#     db_path = sys.argv[1]
#     sql = sys.argv[2]
#     params = sys.argv[3] if len(sys.argv) > 3 else None
#     print(run_sqlite_query(db_path, sql, params))

# New Main to output JSON with success/error/data and prepare for pyinstall packaging for integration with uipath
if __name__ == "__main__":
    import sys
    import json
    output = {}
    # print("DEBUG sys.argv:", repr(sys.argv), file=sys.stderr)
    # for idx, arg in enumerate(sys.argv):
    #     print(f"DEBUG sys.argv[{idx}]: {repr(arg)}", file=sys.stderr)

    try:
        db_path = sys.argv[1]
        sql = sys.argv[2]
        params = sys.argv[3] if len(sys.argv) > 3 else None
        result = json.loads(run_sqlite_query(db_path, sql, params))
        output["success"] = result.get("success", False)
        output["error"] = result.get("error", "")
        # Flatten all remaining keys from result (except success/error)
        for key in result:
            if key not in ["success", "error"]:
                output[key] = result[key]
    except Exception as e:
        output["success"] = False
        output["error"] = str(e)
    print(json.dumps(output))
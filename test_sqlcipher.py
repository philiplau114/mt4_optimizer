import os
# Add the directory containing sqlcipher.dll
os.add_dll_directory(r"C:\Program Files\DB Browser for SQLite")
from pysqlcipher3 import dbapi2 as sqlite3

db_path = "C:/Users/Philip/Documents/GitHub/EA_Automation/EA_Automation.db"
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA key = 'Kh78784bt!'")
# conn.execute("PRAGMA cipher_compatibility = 3")
# conn.execute("PRAGMA cipher_page_size = 1024")
# conn.execute("PRAGMA kdf_iter = 64000")
# conn.execute("PRAGMA cipher_hmac_algorithm = 'SHA1'")
# conn.execute("PRAGMA cipher_kdf_algorithm = 'SHA1'")

cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cursor.fetchall())
cursor.close()
conn.close()
import mysql.connector
from config import Config

try:
    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )
    print("✅ Database connection SUCCESSFUL!")
    print("✅ You're ready to build your rental system!")
    conn.close()
except mysql.connector.Error as e:
    print(f"❌ Database connection failed: {e}")
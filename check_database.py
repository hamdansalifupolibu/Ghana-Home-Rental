import mysql.connector
from config import Config


def check_database():
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print("📊 **YOUR CURRENT TABLES:**")
        for table in tables:
            print(f"✅ {table[0]}")

        # Count records in each table
        print("\n📈 **RECORD COUNTS:**")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"📁 {table[0]}: {count} records")

        # Show sample data from houses table (if exists)
        if any('house' in table[0].lower() for table in tables):
            print("\n🏠 **SAMPLE HOUSE DATA:**")
            cursor.execute("SELECT * FROM houses LIMIT 3")
            houses = cursor.fetchall()
            for house in houses:
                print(house)

        cursor.close()
        conn.close()

    except mysql.connector.Error as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    check_database()
import mysql.connector
import os

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('MYSQL_HOST', 'localhost'),
            user=os.environ.get('MYSQL_USER', 'root'),
            password=os.environ.get('MYSQL_PASSWORD', ''),
            database=os.environ.get('MYSQL_DB', 'rental_service'),
            port=os.environ.get('MYSQL_PORT', 3306),
            # Aiven requires SSL but we'll let the connector handle it automatically
            use_pure=True
        )
        return conn
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        raise

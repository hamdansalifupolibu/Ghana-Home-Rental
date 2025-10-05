import mysql.connector
from flask import current_app

def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='rental_service'
    )
    return conn
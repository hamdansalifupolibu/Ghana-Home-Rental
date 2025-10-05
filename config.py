import os


class Config:
    # Use the key you just generated
    SECRET_KEY = 'e3741741d2525b1db3f79a38893e7248b3c245b8d23c126b'  # ← PASTE YOUR KEY HERE

    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'rental_service'
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
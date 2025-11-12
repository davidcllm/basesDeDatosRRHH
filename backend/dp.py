import pymysql
import os

def get_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASS", "admin123"),
        database=os.getenv("DB_NAME", "mydb"),
        cursorclass=pymysql.cursors.DictCursor
    )

import mysql.connector

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",   # Change this to your DB host (e.g., "localhost")
            user="root",   # Change this to your DB username
            password="mrunal",  # Change this to your DB password
            database="voxify_db"  # Change this to your actual database name
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Database Connection Error: {err}")
        return None

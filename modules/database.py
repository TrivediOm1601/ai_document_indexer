import sqlite3
from datetime import datetime
from flask import current_app
import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'app.db')

def get_db_connection():
    # Ensure instance directory exists
    instance_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)

    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT CHECK(role IN ('admin', 'hr', 'finance')) NOT NULL
        )
    ''')

    # documents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            upload_date DATETIME NOT NULL,
            uploaded_by INTEGER NOT NULL,
            category TEXT,
            title TEXT,
            author TEXT,
            date_created TEXT,
            summary TEXT,
            FOREIGN KEY(uploaded_by) REFERENCES users(id)
        )
    ''')

    # After updating the documents table
    

    # access_logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            document_id INTEGER,
            action TEXT CHECK(action IN ('view', 'download', 'search')),
            timestamp DATETIME NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(document_id) REFERENCES documents(id)
        )
    ''')

    conn.commit()
    conn.close()

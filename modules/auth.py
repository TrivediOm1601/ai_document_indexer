# modules/auth.py
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from modules.database import get_db_connection

def hash_password(password):
    return generate_password_hash(password)

def verify_password(hashed_password, password):
    return check_password_hash(hashed_password, password)

def get_user_by_username(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(username, password, role):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_pw = hash_password(password)
    try:
        cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                       (username, hashed_pw, role))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False  # Username already exists
    conn.close()
    return True

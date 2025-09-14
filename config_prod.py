# config_prod.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-secret-key')
    DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///instance/app.db')
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
    MODEL_PATH = os.environ.get('MODEL_PATH', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'models', 'distilbert-base-uncased'))
    EMBEDDING_MODEL_NAME = os.environ.get('EMBEDDING_MODEL_NAME', 'sentence-transformers/all-MiniLM-L6-v2')
    DEBUG = False

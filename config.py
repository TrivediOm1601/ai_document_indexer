import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'this-is-a-very-secret-key'
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
    DATABASE_URI = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'app.db')
    MODEL_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'models', 'distilbert-base-uncased')
    EMBEDDING_MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'

# scripts/monitor.py
import logging
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

log_path = os.path.join(LOG_DIR, 'app.log')

logger = logging.getLogger('docindexer')
logger.setLevel(logging.INFO)

handler = RotatingFileHandler(log_path, maxBytes=10*1024*1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
handler.setFormatter(formatter)
logger.addHandler(handler)

def log_failed_login(username, ip):
    logger.warning(f"Failed login attempt for username={username} from IP={ip}")

def log_processing_error(document_id, error):
    logger.error(f"Error processing document {document_id}: {error}")

def log_info(message):
    logger.info(message)

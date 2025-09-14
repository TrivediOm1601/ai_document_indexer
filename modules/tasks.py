# modules/tasks.py
from celery_worker import celery_app
from modules import database, document_processor, semantic_search
from datetime import datetime

@celery_app.task
def process_document_async(document_id):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM documents WHERE id = ?', (document_id,))
    doc = cursor.fetchone()
    if not doc:
        conn.close()
        return f"Document {document_id} not found."

    file_path = doc['file_path']
    file_type = doc['file_type']

    # Extract text
    text = document_processor.extract_text(file_path, file_type)

    # Classify document
    category = document_processor.classify_document(text)

    # Extract metadata
    metadata = document_processor.extract_metadata(text)

    # Generate abstractive summary
    summary = document_processor.generate_abstractive_summary(text)

    # Update document with extracted info
    cursor.execute('''
        UPDATE documents SET category=?, title=?, author=?, date_created=?, summary=?
        WHERE id=?
    ''', (category, metadata.get('title'), metadata.get('author'), metadata.get('date_created'), summary, document_id))
    conn.commit()

    # Generate embedding & update FAISS index
    model = semantic_search.get_embedding_model()
    embedding = semantic_search.generate_embedding(text, model)
    semantic_search.update_index(document_id, embedding)

    # Log processing completion as 'process' action
    cursor.execute('''
        INSERT INTO access_logs (user_id, document_id, action, timestamp)
        VALUES (?, ?, 'process', ?)
    ''', (doc['uploaded_by'], document_id, datetime.now()))
    conn.commit()

    conn.close()
    return f"Processed document {document_id}."

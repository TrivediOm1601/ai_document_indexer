import os
from datetime import datetime
from modules import document_processor, database
from modules.tasks import process_document_async
from docx import Document
import os


def handle_file_upload(uploaded_file, upload_folder, user_id):
    filename = uploaded_file.filename
    allowed_ext = {'.pdf': 'pdf', '.docx': 'docx', '.txt': 'txt'}
    file_ext = os.path.splitext(filename)[1].lower()

    if file_ext not in allowed_ext:
        raise ValueError("Unsupported file type.")

    file_type = allowed_ext[file_ext]
    os.makedirs(upload_folder, exist_ok=True)
    save_path = os.path.join(upload_folder, filename)
    uploaded_file.save(save_path)

    # Extract text for DOCX separately to get full content
    if file_type == 'docx':
        extracted_text = extract_docx_text(save_path)
    else:
        # For PDF or TXT, use your existing processor function
        extracted_text = None

    processed = document_processor.process_document_file(save_path, file_type)

    # If DOCX, override or append summary with extracted text
    if file_type == 'docx' and extracted_text:
        processed['summary'] = extracted_text  # or combine with existing summary

    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO documents (filename, original_filename, file_path, file_type, upload_date, uploaded_by, category, title, author, date_created, summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        filename,
        filename,
        save_path,
        file_type,
        datetime.now(),
        user_id,
        processed.get('category'),
        processed.get('metadata', {}).get('title'),
        processed.get('metadata', {}).get('author'),
        processed.get('metadata', {}).get('date_created'),
        processed.get('summary')
    ))
    doc_id = cursor.lastrowid
    conn.commit()
    conn.close()

    process_document_async.delay(doc_id)

    return doc_id

def extract_docx_text(file_path):
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

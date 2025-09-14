import os
from datetime import datetime
from modules import document_processor, database
from modules.tasks import process_document_async
from docx import Document

# Role to allowed categories mapping for three roles only
ROLE_TO_CATEGORIES = {
    'admin': None,  # Admin has access to all categories
    'hr': ['Resume'],
    'finance': ['Invoice', 'Contract'],
}

def normalize_category(cat):
    if not cat:
        return None
    # Replace underscores with spaces and capitalize each word
    return ' '.join(word.capitalize() for word in cat.strip().replace('_', ' ').split())

def extract_docx_text(file_path):
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def get_user_role_by_id(user_id):
    # Fetch the role for given user_id from your users table
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT role FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row['role'].lower().strip()
    return None

def handle_file_upload(uploaded_file, upload_folder, user_id):
    user_role = get_user_role_by_id(user_id)
    allowed_categories = ROLE_TO_CATEGORIES.get(user_role, [])

    filename = uploaded_file.filename
    allowed_ext = {'.pdf': 'pdf', '.docx': 'docx', '.txt': 'txt'}
    file_ext = os.path.splitext(filename)[1].lower()

    if file_ext not in allowed_ext:
        raise ValueError("Unsupported file type.")

    file_type = allowed_ext[file_ext]
    os.makedirs(upload_folder, exist_ok=True)
    save_path = os.path.join(upload_folder, filename)
    uploaded_file.save(save_path)

    if file_type == 'docx':
        extracted_text = extract_docx_text(save_path)
    else:
        extracted_text = None

    processed = document_processor.process_document_file(save_path, file_type)

    if file_type == 'docx' and extracted_text:
        processed['summary'] = extracted_text

    category_raw = processed.get('category')
    category_norm = normalize_category(category_raw)

    if user_role != 'admin':
        if not allowed_categories or category_norm not in allowed_categories:
            raise ValueError("You are not allowed to upload documents in this category.")

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
        category_norm,
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

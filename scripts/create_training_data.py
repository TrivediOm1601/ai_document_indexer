# scripts/create_training_data.py
import os
import sqlite3
import json

DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'instance', 'app.db')
ALLOWED_CATEGORIES = ['Finance', 'HR', 'Legal', 'Contracts', 'Technical']

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def extract_text_from_file(file_path, file_type):
    # Reuse extraction code to ensure consistency
    import sys
    sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
    from modules.document_processor import extract_text
    return extract_text(file_path, file_type)

def prompt_for_category(doc_text):
    # Show chunk (first 500 chars) to prompt user
    print("\n" + "="*80)
    print("Document text excerpt:\n")
    print(doc_text[:500].replace('\n', ' '))
    print("\nAvailable categories:", ALLOWED_CATEGORIES)
    while True:
        cat = input("Enter correct category for this document (case-sensitive): ").strip()
        if cat in ALLOWED_CATEGORIES:
            return cat
        else:
            print("Invalid category. Please input one from the list.")

def main():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM documents')
    all_docs = cursor.fetchall()

    output_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'training_data.jsonl')

    with open(output_file, 'w', encoding='utf-8') as f_out:
        for doc in all_docs:
            doc_id = doc['id']
            # Extract text to ensure consistency
            text = extract_text_from_file(doc['file_path'], doc['file_type'])

            category = doc['category']
            if category not in ALLOWED_CATEGORIES:
                category = prompt_for_category(text)
                cursor.execute('UPDATE documents SET category = ? WHERE id = ?', (category, doc_id))
                conn.commit()
                print(f"Updated document ID {doc_id} category to '{category}'")

            # Write to JSONL file
            record = {"text": text, "label": category}
            f_out.write(json.dumps(record) + '\n')

    print(f"\nTraining data JSONL exported to: {output_file}")
    conn.close()

if __name__ == '__main__':
    main()

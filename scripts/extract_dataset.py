import os
import csv
from docx import Document
import fitz  # PyMuPDF
import chardet

def extract_text_pdf(filepath):
    text = []
    doc = fitz.open(filepath)
    for page in doc:
        text.append(page.get_text())
    return "\n".join(text).strip()

def extract_text_docx(filepath):
    doc = Document(filepath)
    paragraphs = [para.text for para in doc.paragraphs]
    return "\n".join(paragraphs).strip()

def extract_text_txt(filepath):
    with open(filepath, 'rb') as f:
        rawdata = f.read()
        encoding = chardet.detect(rawdata)['encoding'] or 'utf-8'
    with open(filepath, 'r', encoding=encoding, errors='ignore') as f:
        return f.read().strip()

def extract_text(filepath):
    ext = filepath.lower().split('.')[-1]
    if ext == 'pdf':
        return extract_text_pdf(filepath)
    elif ext == 'docx':
        return extract_text_docx(filepath)
    elif ext == 'txt':
        return extract_text_txt(filepath)
    else:
        return ""

def get_category_from_path(filepath, root_dir):
    relative_path = os.path.relpath(filepath, root_dir)
    parts = relative_path.split(os.sep)
    if parts:
        return parts[0]
    return "Unknown"

def process_dataset(root_dir, output_csv):
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['text', 'label'])
        for subdir, _, files in os.walk(root_dir):
            for file in files:
                filepath = os.path.join(subdir, file)
                category = get_category_from_path(filepath, root_dir)
                try:
                    text = extract_text(filepath)
                    if text.strip():
                        writer.writerow([text, category])
                        print(f"Processed: {filepath} -> Label: {category}")
                    else:
                        print(f"No text extracted from {filepath}, skipping.")
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")

if __name__ == "__main__":
    dataset_root = r"D:\Hackathon\Dataset"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, 'dataset.csv')

    process_dataset(dataset_root, output_file)
    print(f"Dataset extraction completed. File saved as: {output_file}")

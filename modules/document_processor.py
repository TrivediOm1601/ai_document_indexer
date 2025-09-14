import os
import re
import random
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import numpy as np
import fitz  # PyMuPDF for PDFs
import docx  # python-docx for DOCX docs

# NLP libraries with graceful fallbacks
try:
    import spacy
    nlp = spacy.load('en_core_web_sm')
except (ImportError, OSError):
    nlp = None

try:
    import nltk
    nltk.data.find('tokenizers/punkt')
except (ImportError, LookupError):
    nltk = None

# --- Document Processing Functions ---

def extract_text(file_path, file_type):
    """Extract text from PDF, DOCX, or TXT files."""
    text = ""
    file_type = file_type.lower()
    if file_type == 'pdf':
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
    elif file_type == 'docx':
        doc = docx.Document(file_path)
        paragraphs = [para.text for para in doc.paragraphs]
        text = "\n".join(paragraphs)
    elif file_type == 'txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        raise ValueError(f"Unsupported file_type: {file_type}")
    return text

# Load your fine-tuned model and tokenizer once globally
MODEL_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'models', 'finetuned_classifier')
LABEL_LIST = ['Finance', 'HR', 'Legal', 'Technical']  # Broad categories (update as per your labels)

try:
    tokenizer_cls = AutoTokenizer.from_pretrained(MODEL_DIR)
    model_cls = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
    model_cls.eval()
except Exception:
    tokenizer_cls = None
    model_cls = None

def classify_document(text):
    """Classify text into broad categories using fine-tuned transformer."""
    if not tokenizer_cls or not model_cls:
        return random.choice(LABEL_LIST)
    inputs = tokenizer_cls(text, return_tensors='pt', truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model_cls(**inputs)
    logits = outputs.logits
    pred = torch.argmax(logits, dim=1).item()
    return LABEL_LIST[pred]

# Map broad categories to detailed ones (update with your taxonomy)
BROAD_TO_DETAILED = {
    'Finance': 'Invoice',
    'HR': 'Resume',
    'Legal': 'Contract',
    'Technical': 'Technical_Manual',
}

def classify_document_detailed(text):
    """Returns detailed category by first classifying into broad then mapping."""
    broad_cat = classify_document(text)
    detailed_cat = BROAD_TO_DETAILED.get(broad_cat, 'Non_Relevant')
    return detailed_cat

# Initialize NER pipeline with fallback and safe exception handling
ner_pipeline = None
try:
    ner_pipeline = pipeline('token-classification', model='dslim/bert-base-NER', aggregation_strategy="simple")
except Exception as e:
    ner_pipeline = None
    print(f"NER pipeline failed to load: {e}")

def extract_metadata(text):
    global ner_pipeline  # <-- Must be first line inside the function

    """
    Extract metadata including title, author, date, and key entities.
    Uses transformer NER if available, spaCy fallback, and regex as last resort.
    """
    # Title extraction: first sufficiently long sentence or first line
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    title = next((s for s in sentences if len(s.split()) > 5 and s.endswith('.')), text.strip().split('\n')[0])

    # Author extraction heuristics
    author = None
    for pattern in [r'Author:\s*(.+)', r'By:\s*(.+)', r'([\w\.-]+@[\w\.-]+\.\w+)']:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            author = match.group(1) if match.lastindex else match.group(0)
            break

    # Date extraction with common date patterns from first 200 chars
    date_created = None
    for pat in [r'(\d{4}-\d{2}-\d{2})', r'(\d{2}/\d{2}/\d{4})', r'(\d{1,2} [A-Za-z]+ \d{4})', r'([A-Za-z]+ \d{1,2}, \d{4})']:
        m = re.search(pat, text[:200])
        if m:
            date_created = m.group(1)
            break

    # Entities extraction with NER pipeline or spaCy fallback
    entities = {'PERSON': [], 'ORG': [], 'MONEY': []}

    if ner_pipeline:
        try:
            ner_res = ner_pipeline(text[:5000])
            for ent in ner_res:
                label = ent.get('entity_group')
                word = ent.get('word', '').strip()
                if label in entities and word and word not in entities[label]:
                    entities[label].append(word)
        except Exception:
            ner_pipeline = None  # assign after global declared at top

    if not ner_pipeline and nlp:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ in entities and ent.text not in entities[ent.label_]:
                entities[ent.label_].append(ent.text)
    elif not ner_pipeline:
        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        entities['PERSON'].extend(list(set(emails)))

    return {
        'title': title,
        'author': author or '',
        'date_created': date_created or '',
        'entities': entities
    }



# Abstractive summary generation using Hugging Face BART or fallback
def generate_abstractive_summary(text, model_name='facebook/bart-large-cnn', max_length=130, min_length=30):
    try:
        summarizer = pipeline('summarization', model=model_name)
        summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
        return summary[0]['summary_text']
    except Exception:
        return generate_summary(text)

# Extractive summary fallback for robustness
def generate_summary(text, num_sentences=3):
    if nltk:
        sentences = nltk.sent_tokenize(text)
    else:
        sentences = re.split(r'(?<=[.!?])\s+', text)

    if len(sentences) <= num_sentences:
        return ' '.join(sentences)

    try:
        from collections import Counter
        import string
        from nltk.corpus import stopwords
        stop_words = set(stopwords.words('english'))
    except:
        stop_words = {'the', 'and', 'to', 'of', 'a', 'in', 'is', 'it'}

    words = re.findall(r'\w+', text.lower())
    words_filtered = [w for w in words if w not in stop_words]
    freq = Counter(words_filtered)

    top_n = max(1, int(len(freq) * 0.1)) if freq else 1
    important_words = set([w for w, _ in freq.most_common(top_n)])

    def sentence_score(sentence):
        sentence_words = re.findall(r'\w+', sentence.lower())
        if not sentence_words:
            return 0
        imp_count = sum(1 for w in sentence_words if w in important_words)
        return imp_count / len(sentence_words)

    scored = [(s, sentence_score(s)) for s in sentences]
    scored.sort(key=lambda x: x[1], reverse=True)
    top_sentences = [s for s, _ in scored[:num_sentences]]
    top_sentences_sorted = sorted(top_sentences, key=lambda s: text.find(s))
    return ' '.join(top_sentences_sorted)


# Wrapper: Full processing pipeline for a document file
def process_document_file(file_path, file_type):
    text = extract_text(file_path, file_type)
    category = classify_document_detailed(text)
    metadata = extract_metadata(text)
    summary = generate_abstractive_summary(text)
    return {
        'text': text,
        'category': category,
        'metadata': metadata,
        'summary': summary,
    }

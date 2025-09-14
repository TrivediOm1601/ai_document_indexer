import re
from config.category_keywords import CATEGORY_KEYWORDS

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return text

def score_category(document_text, category_keywords):
    text = preprocess_text(document_text)
    score = 0
    for kw in category_keywords:
        pattern = r'\b' + re.escape(kw.lower()) + r'\b'
        matches = re.findall(pattern, text)
        score += len(matches)
    return score

def classify_document(text):
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        scores[category] = score_category(text, keywords)
    best_category, best_score = max(scores.items(), key=lambda item: item[1])
    if best_score == 0:
        return 'Non_Relevant'  # fallback category
    return best_category

def classify_with_metadata(text, filename):
    category = classify_document(text)
    filename_lower = filename.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in filename_lower for kw in keywords):
            category = cat
            break
    return category

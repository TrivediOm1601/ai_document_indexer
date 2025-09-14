import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from config import Config
import sqlite3
from collections import defaultdict
import re

# Path to FAISS index file
FAISS_INDEX_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'models', 'faiss_index.index')
# Path to JSON file mapping FAISS index ids to document ids
IDX_MAP_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'models', 'faiss_id_map.json')


def get_embedding_model():
    """
    Load or download SentenceTransformer embedding model.
    """
    embedding_model_name = Config.EMBEDDING_MODEL_NAME
    local_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'models', 'sentence_transformer_model')
    try:
        if os.path.exists(local_path):
            model = SentenceTransformer(local_path)
        else:
            model = SentenceTransformer(embedding_model_name)
            model.save(local_path)
    except Exception as e:
        print(f"Failed to load embedding model locally: {e}. Downloading anew.")
        model = SentenceTransformer(embedding_model_name)
    return model

def keyword_search(query, k=10):
    """
    Keyword search using SQLite FTS5 if available; fallback to LIKE search.
    """
    conn = sqlite3.connect(Config.DATABASE_URI)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Assuming an FTS5 virtual table called documents_fts with content from documents.title, summary, etc.
    # If unavailable, fallback below:

    try:
        # FTS5 full-text search (fast and effective)
        cursor.execute("""
        SELECT d.*, bm25(dfts) AS score
        FROM documents_fts dfts
        JOIN documents d ON dfts.rowid = d.id
        WHERE documents_fts MATCH ?
        ORDER BY score LIMIT ?
        """, (query, k))
        results = cursor.fetchall()
    except Exception:
        # Fallback naive LIKE search (slow for large DBs)
        like_query = f'%{query}%'
        cursor.execute("""
        SELECT * FROM documents WHERE title LIKE ? OR summary LIKE ? LIMIT ?
        """, (like_query, like_query, k))
        results = cursor.fetchall()

    conn.close()
    return [(res['id'], res) for res in results]

def hybrid_search(query, k=5):
    """
    Combines vector search and keyword search results using Reciprocal Rank Fusion (RRF).
    """
    vector_results = search_index(generate_embedding(query, get_embedding_model()), k=k)
    keyword_results = keyword_search(query, k=k)

    # Create rank dicts: document_id -> rank (starting at 1)
    rrf_scores = defaultdict(float)
    for rank, (doc_id, dist) in enumerate(vector_results, start=1):
        rrf_scores[doc_id] += 1.0 / (60 + rank)
    for rank, (doc_id, _) in enumerate(keyword_results, start=1):
        rrf_scores[doc_id] += 1.0 / (60 + rank)

    # Sort by combined RRF score descending
    fused = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    # Fetch document info for top-k
    conn = sqlite3.connect(Config.DATABASE_URI)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    results = []
    count = 0
    for doc_id, score in fused:
        cursor.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
        doc = cursor.fetchone()
        if doc:
            results.append((doc, score))
            count += 1
            if count >= k:
                break
    conn.close()
    return results


def generate_embedding(text, model):
    """
    Generate embedding for input text using the provided model.
    Return a numpy array (float32).
    """
    embedding = model.encode(text)
    return np.array(embedding).astype('float32')


def init_faiss_index(dimension):
    """
    Initialize new FAISS index with specified dimension.  
    Use IndexFlatIP for cosine similarity when embeddings normalized.
    """
    index = faiss.IndexFlatL2(dimension)   # or faiss.IndexFlatIP(dimension) if normalized vectors
    faiss.write_index(index, FAISS_INDEX_PATH)
    if not os.path.exists(IDX_MAP_PATH):
        with open(IDX_MAP_PATH, 'w') as f:
            json.dump({}, f)
    return index


def update_index(document_id, embedding, index_path=FAISS_INDEX_PATH):
    """
    Add new embedding to FAISS index and update mapping file.
    """
    if not os.path.exists(index_path):
        dimension = embedding.shape[0]
        index = init_faiss_index(dimension)
    else:
        index = faiss.read_index(index_path)

    # Normalize embedding if you use cosine similarity
    # norm = np.linalg.norm(embedding)
    # if norm > 0:
    #     embedding = embedding / norm

    index.add(np.expand_dims(embedding, axis=0))
    faiss.write_index(index, index_path)

    if os.path.exists(IDX_MAP_PATH):
        with open(IDX_MAP_PATH, 'r') as f:
            id_map = json.load(f)
    else:
        id_map = {}

    new_id = index.ntotal - 1
    id_map[str(new_id)] = document_id

    # Consider atomic write for concurrency safety
    with open(IDX_MAP_PATH, 'w') as f:
        json.dump(id_map, f)



def search_index(query_embedding, k=5, index_path=FAISS_INDEX_PATH):
    if not os.path.exists(index_path) or not os.path.exists(IDX_MAP_PATH):
        print("FAISS index or ID map file missing")
        return []

    index = faiss.read_index(index_path)
    D, I = index.search(np.expand_dims(query_embedding, axis=0), k)
    distances = D[0]
    indices = I[0]

    with open(IDX_MAP_PATH, 'r') as f:
        id_map = json.load(f)

    print(f"Loaded ID map: {id_map}")  # Debug print

    results = []
    for i, dist in zip(indices, distances):
        if str(i) in id_map:
            results.append((id_map[str(i)], float(dist)))
        else:
            print(f"FAISS index id {i} not found in ID map")

    print(f"Search results: {results}")  # Debug print
    return results

def keyword_filter(doc_score_list, query):
    query_words = set(query.lower().split())
    filtered = []
    for doc, score in doc_score_list:
        # Convert sqlite3.Row to dict for compatibility
        doc = dict(doc)
        text = (doc.get('title', '') + ' ' + doc.get('summary', '')).lower()
        if all(word in text for word in query_words):
            filtered.append((doc, score))
    return filtered


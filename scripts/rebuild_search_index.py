import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import numpy as np
import faiss
from modules import database, semantic_search


def rebuild_faiss_index():
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, summary FROM documents WHERE summary IS NOT NULL')
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No documents with summaries found to index.")
        return

    embedding_model = semantic_search.get_embedding_model()
    # Dynamically get dimension from one sample embedding
    sample_embedding = semantic_search.generate_embedding(rows[0][1], embedding_model)
    dimension = len(sample_embedding)

    index = faiss.IndexFlatL2(dimension)
    id_map = {}

    for idx, (doc_id, text) in enumerate(rows):
        embedding = semantic_search.generate_embedding(text, embedding_model)
        embedding = np.array(embedding, dtype='float32')
        index.add(np.expand_dims(embedding, axis=0))
        id_map[str(idx)] = doc_id

    model_folder = os.path.dirname(semantic_search.FAISS_INDEX_PATH)
    os.makedirs(model_folder, exist_ok=True)

    faiss.write_index(index, semantic_search.FAISS_INDEX_PATH)
    with open(semantic_search.IDX_MAP_PATH, 'w') as f:
        json.dump(id_map, f)

    print(f"Rebuilt FAISS index with {index.ntotal} documents.")


if __name__ == "__main__":
    rebuild_faiss_index()

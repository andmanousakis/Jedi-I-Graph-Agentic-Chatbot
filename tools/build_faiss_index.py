# scripts/build_faiss_index.py
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from pathlib import Path

fragments = [
    {"text": "AI is the future.", "source": "test.md"},
    {"text": "ML is a subset of AI.", "source": "test.md"},
    {"text": "Deep learning is part of ML.", "source": "test.md"},
]

model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode([f["text"] for f in fragments], normalize_embeddings=True)
embedding_matrix = np.stack(embeddings)

index = faiss.IndexFlatIP(embedding_matrix.shape[1])
index.add(embedding_matrix)

Path("vectordb").mkdir(exist_ok=True)
faiss.write_index(index, "vectordb/fragments.index")
print("FAISS index built and saved to vectordb/fragments.index")
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os
from pathlib import Path
from utilities.utilities import Utilities

class Retriever:
    def __init__(self, fragments: list[dict]):
        self.index_path = Path("vectordb/fragments.index")
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize model always
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            self.fragments = fragments  # Assume same fragments as used in build script
            return

        # Ensure DB table exists
        Utilities.create_fragments_table_if_not_exists()
        
        # Load from DB
        existing_fragments = Utilities.load_stored_fragments_with_embeddings()

        self.fragments = []
        valid_embeddings = []

        for f in fragments:
            key = (f["text"], f["source"])
            emb = existing_fragments.get(key)

            if isinstance(emb, np.ndarray) and emb.shape == (384,):
                self.fragments.append({"text": f["text"], "source": f["source"]})
                valid_embeddings.append(emb)
            else:
                emb = self.model.encode([f["text"]], normalize_embeddings=True)[0]
                self.fragments.append({"text": f["text"], "source": f["source"]})
                valid_embeddings.append(emb)

        if not valid_embeddings:
            raise ValueError("No valid fragments found to index.")

        embedding_matrix = np.stack(valid_embeddings)

        self.index = faiss.IndexFlatIP(embedding_matrix.shape[1])
        self.index.add(embedding_matrix)
        faiss.write_index(self.index, str(self.index_path))


    def search(self, query: str, top_k: int = 3) -> list[dict]:
        query_vec = self.model.encode([query], normalize_embeddings=True)
        D, I = self.index.search(np.array(query_vec), top_k)

        results = []
        for idx, score in zip(I[0], D[0]):
            if 0 <= idx < len(self.fragments) and score > 0.6:
                results.append(self.fragments[idx])
        return results

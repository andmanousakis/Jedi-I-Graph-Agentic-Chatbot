from sentence_transformers import SentenceTransformer, util

class Classifier:


    def __init__(self):

        # Load a sentence-transformers model.
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def score(self, query: str, answer: str) -> float:

        # Compute cosine similarity between query and answer embeddings.
        query_emb = self.model.encode(query, convert_to_tensor=True)

        # Encode the answer into an embedding.
        answer_emb = self.model.encode(answer, convert_to_tensor=True)

        # Calculate cosine similarity between the query and answer embeddings.
        similarity = util.cos_sim(query_emb, answer_emb)

        # Return the similarity score as a float.
        return similarity.item()
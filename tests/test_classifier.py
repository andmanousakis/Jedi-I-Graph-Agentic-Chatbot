from unittest.mock import MagicMock, patch
from tools.classifier import Classifier

def test_score_returns_expected_similarity():
    with patch("tools.classifier.SentenceTransformer") as mock_model_class, \
         patch("tools.classifier.util") as mock_util:

        # Create mock embeddings
        mock_query_emb = MagicMock()
        mock_answer_emb = MagicMock()

        # Create a mock model and patch encode() return values
        mock_model = MagicMock()
        mock_model.encode.side_effect = [mock_query_emb, mock_answer_emb]
        mock_model_class.return_value = mock_model

        # Patch similarity function to return a tensor-like with .item()
        mock_similarity = MagicMock()
        mock_similarity.item.return_value = 0.75
        mock_util.cos_sim.return_value = mock_similarity

        # Instantiate and test
        classifier = Classifier()
        score = classifier.score("What is AI?", "AI means artificial intelligence.")

        assert isinstance(score, float)
        assert score == 0.75

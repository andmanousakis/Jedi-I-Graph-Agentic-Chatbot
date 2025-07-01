from unittest.mock import patch, MagicMock
import numpy as np
from tools.retriever import Retriever


@patch("tools.retriever.faiss.write_index")
@patch("tools.retriever.Path.exists", return_value=False)
@patch("tools.retriever.SentenceTransformer")
@patch("tools.retriever.faiss.IndexFlatIP")
@patch("tools.retriever.Utilities.load_stored_fragments_with_embeddings")
def test_retriever_init_builds_index(mock_load_from_db, mock_faiss, mock_transformer, mock_exists, mock_write_index):
    fragments = [{"text": t, "source": "test.md"} for t in [
        "AI is the future.",
        "ML is a subset of AI."
    ]]
    mock_load_from_db.return_value = {}

    mock_model = MagicMock()
    mock_model.encode.side_effect = iter([
        np.random.rand(1, 384),
        np.random.rand(1, 384)
    ])
    mock_transformer.return_value = mock_model

    mock_index = MagicMock()
    mock_faiss.return_value = mock_index

    retriever = Retriever(fragments)

    assert len(retriever.fragments) == 2
    assert mock_index.add.called
    assert mock_write_index.called


@patch("tools.retriever.faiss.write_index")
@patch("tools.retriever.Path.exists", return_value=False)
@patch("tools.retriever.SentenceTransformer")
@patch("tools.retriever.faiss.IndexFlatIP")
@patch("tools.retriever.Utilities.load_stored_fragments_with_embeddings")
def test_retriever_search_returns_top_k(mock_load_from_db, mock_faiss, mock_transformer, mock_exists, mock_write_index):
    fragments = [{"text": t, "source": "test.md"} for t in [
        "AI is the future.",
        "ML is a subset of AI.",
        "Deep learning is part of ML."
    ]]
    mock_load_from_db.return_value = {}

    mock_model = MagicMock()
    mock_model.encode.side_effect = iter([
        np.random.rand(1, 384),
        np.random.rand(1, 384),
        np.random.rand(1, 384),
        np.random.rand(1, 384)  # query
    ])
    mock_transformer.return_value = mock_model

    mock_index = MagicMock()
    mock_index.search.return_value = (
        np.array([[0.9, 0.8, 0.1]]), 
        np.array([[0, 1, 2]])
    )
    mock_faiss.return_value = mock_index

    retriever = Retriever(fragments)
    results = retriever.search("What is AI?", top_k=3)

    assert isinstance(results, list)
    assert len(results) == 2
    assert results[0]["text"] == "AI is the future."
    assert results[1]["text"] == "ML is a subset of AI."

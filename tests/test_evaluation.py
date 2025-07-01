import pytest
from unittest.mock import MagicMock
import json
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.evaluation import Evaluator

def test_get_method_web_search():
    evaluator = Evaluator()
    state = {"web_answer": "This came from Google."}
    assert evaluator._get_method(state) == "web_search"

def test_get_method_rag():
    evaluator = Evaluator()
    state = {"internal_answer": "This is from docs.", "internal_source": "data.md"}
    assert evaluator._get_method(state) == "rag"

def test_get_method_fallback():
    evaluator = Evaluator()
    state = {"used_fallback": True}
    assert evaluator._get_method(state) == "fallback"

def test_get_method_unknown():
    evaluator = Evaluator()
    state = {}
    assert evaluator._get_method(state) == "unknown"

def test_evaluate_response_with_gemini_mocked():
    evaluator = Evaluator()
    mock_result = {
        "correctness": 0.9,
        "relevance": 0.8,
        "fluency": 0.95,
        "comment": "Good job overall"
    }
    evaluator.gemini.evaluate_response = MagicMock(return_value=json.dumps(mock_result))

    result = evaluator.evaluate_response_with_gemini("query", "answer", "context")

    assert result["correctness"] == 0.9
    assert result["relevance"] == 0.8
    assert result["fluency"] == 0.95
    assert "comment" in result

def test_store_response_evaluation_with_mocked_db():
    evaluator = Evaluator()

    # Simulated Gemini score
    scores = {
        "correctness": 0.9,
        "relevance": 0.8,
        "fluency": 0.95,
        "comment": "Nice"
    }

    # Mock connection and cursor
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Patch feedback lookup (e.g., thumbs up = 1)
    mock_cursor.fetchone.return_value = (1,)

    # Run the method
    evaluator.store_response_evaluation(
        mock_conn,
        message_id=42,
        query="What is LangChain?",
        answer="LangChain is a framework for developing LLM-based apps.",
        scores=scores
    )

    # Assert INSERT was executed
    assert mock_cursor.execute.called
    query_args = mock_cursor.execute.call_args[0][1]

    # Unpack arguments (10 values expected)
    (
        response_id,
        query,
        answer,
        feedback,
        correctness,
        relevance,
        fluency,
        comment,
        weighted_score,
        final_score
    ) = query_args

    # Validate values
    assert response_id == 42
    assert query == "What is LangChain?"
    assert answer.startswith("LangChain")
    assert feedback == 1
    assert correctness == 0.9
    assert relevance == 0.8
    assert fluency == 0.95
    assert comment == "Nice"
    assert weighted_score == round(0.4 * 0.9 + 0.4 * 0.8 + 0.2 * 0.95, 3)
    assert final_score == round(0.8 * weighted_score + 0.2 * 1.0, 3)

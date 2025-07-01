from unittest.mock import MagicMock, patch
from tools.gemini_client import GeminiClient

@patch("tools.gemini_client.genai")
def test_refine_answer_returns_text(mock_genai):
    mock_model = MagicMock()
    mock_model.generate_content.return_value.text = "Refined answer."
    mock_genai.GenerativeModel.return_value = mock_model

    client = GeminiClient()
    result = client.refine_answer("What is AI?", "AI is cool.", "AI means artificial intelligence.")

    assert isinstance(result, str)
    assert result == "Refined answer."


@patch("tools.gemini_client.genai")
def test_evaluate_response_returns_json(mock_genai):
    mock_model = MagicMock()
    mock_model.generate_content.return_value.text = """{
        "correctness": 1.0,
        "relevance": 0.9,
        "fluency": 1.0,
        "comment": "Clear and accurate."
    }"""
    mock_genai.GenerativeModel.return_value = mock_model

    client = GeminiClient()
    result = client.evaluate_response("What is AI?", "AI is artificial intelligence.", "AI means...")

    assert "correctness" in result
    assert isinstance(result, str)
    assert result.startswith("{") and result.endswith("}")


@patch("tools.gemini_client.genai")
def test_summarize_conversation_title_returns_string(mock_genai):
    mock_model = MagicMock()
    mock_model.generate_content.return_value.text = '"AI Basics Summary"'
    mock_genai.GenerativeModel.return_value = mock_model

    messages = [
        {"role": "user", "content": "What is AI?"},
        {"role": "assistant", "content": "AI is artificial intelligence."}
    ]

    client = GeminiClient()
    title = client.summarize_conversation_title(messages)

    assert isinstance(title, str)
    assert title == "AI Basics Summary"

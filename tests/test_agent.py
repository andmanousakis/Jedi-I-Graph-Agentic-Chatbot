import pytest
from unittest.mock import patch, MagicMock
from agent.graph_agent import GraphAgent

@pytest.fixture
def mock_graph_agent():
    with patch("agent.graph_agent.Utilities.load_fragments_from_md", return_value=[{"text": "internal answer", "source": "source.md"}]):
        with patch("agent.graph_agent.Retriever") as MockRetriever:
            instance = MockRetriever.return_value
            instance.search.return_value = [{"text": "internal answer", "source": "source.md"}]

            with patch("agent.graph_agent.Classifier") as MockClassifier:
                classifier = MockClassifier.return_value
                classifier.score.return_value = 0.9

                with patch("agent.graph_agent.Evaluator.run") as _:
                    with patch("agent.graph_agent.Utilities.save_message", return_value=123):
                        with patch("agent.graph_agent.Utilities.load_messages", return_value=[{"role": "user", "content": "test"}]):
                            with patch("agent.graph_agent.GeminiClient.summarize_conversation_title", return_value="Generated Title"):
                                with patch("agent.graph_agent.Utilities.update_conversation_title") as _:
                                    yield GraphAgent()

def test_graph_agent_flow(mock_graph_agent):
    response = mock_graph_agent.run("What is internal?", conversation_id=1, history_length=1)
    
    assert response["internal_answer"] == "internal answer"
    assert response["internal_source"] == "source.md"
    assert response["assistant_msg_id"] == 123
    assert "Returning final answer with citation." in response["thoughts"]

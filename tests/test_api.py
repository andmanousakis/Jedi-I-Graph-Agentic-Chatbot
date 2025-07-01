from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_ask_endpoint(monkeypatch):
    class DummyAgent:
        def run(self, query, conversation_id, history_length):
            return {
                "internal_answer": "This is a test answer.",
                "internal_source": "test.md",
                "thoughts": ["Thinking..."],
                "assistant_msg_id": 123,
            }

    # Patch agent
    from api import main
    main.agent = DummyAgent()

    # Patch Utilities.count_messages
    monkeypatch.setattr("api.main.Utilities.count_messages", lambda cid: 0)

    response = client.post("/ask/", json={"query": "What is AI?", "conversation_id": 1})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "This is a test answer."
    assert data["source"] == "test.md"
    assert data["assistant_msg_id"] == 123
    assert "Thinking..." in data["thoughts"]

def test_analytics_endpoint(monkeypatch):
    dummy_summary = {
        "total_queries": 42,
        "method_counts": {"rag": 20, "web_search": 22},
        "source_type_counts": {"internal": 18, "external": 24},
        "average_scores": {"rag": 0.88, "web_search": 0.79}
    }

    class DummyEvaluator:
        def compute_statistics(self):
            return dummy_summary

    # Patch Evaluator
    monkeypatch.setattr("api.main.Evaluator", lambda: DummyEvaluator())

    response = client.get("/analytics/")
    assert response.status_code == 200
    assert response.json()["total_queries"] == 42

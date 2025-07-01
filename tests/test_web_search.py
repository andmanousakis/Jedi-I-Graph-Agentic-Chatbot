from unittest.mock import patch, MagicMock
from tools.web_search import SearchWeb

def test_pipeline_success():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "organic": [
            {
                "snippet": "Example snippet.",
                "link": "https://example.com"
            }
        ]
    }

    with patch("tools.web_search.httpx.post", return_value=mock_response):
        search_tool = SearchWeb()
        snippet, link = search_tool.pipeline("test query")
        assert snippet == "Example snippet."
        assert link == "https://example.com"

def test_pipeline_no_results():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "organic": []
    }

    with patch("tools.web_search.httpx.post", return_value=mock_response):
        search_tool = SearchWeb()
        snippet, link = search_tool.pipeline("no results")
        assert snippet == "No result found."
        assert link == "N/A"

def test_pipeline_http_error():
    with patch("tools.web_search.httpx.post", side_effect=Exception("Connection failed")):
        search_tool = SearchWeb()
        snippet, link = search_tool.pipeline("error case")
        assert "Error during search: Connection failed" in snippet
        assert link == "N/A"

from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv; load_dotenv() 

from agent.graph_agent import GraphAgent
from utilities.utilities import Utilities
from tools.evaluation import Evaluator


# Initialize FastAPI app.
app = FastAPI()

# Ensure database exists.
Utilities.create_database_if_not_exists()

# Initialize database schema once at startup.
Utilities.initialize_database()

# Instantiate agent.
agent = GraphAgent()

class QueryRequest(BaseModel):
    query: str
    conversation_id: int

@app.post("/ask/")
def ask_jedi(request: QueryRequest):

    # Count the number of messages in the conversation.
    history_length = Utilities.count_messages(request.conversation_id)

    # If the history length is 0, we assume it's a new conversation.
    state = agent.run(request.query, request.conversation_id, history_length)

    return {
        "answer": state.get("internal_answer") or state.get("web_answer"),
        "source": state.get("internal_source") or state.get("web_source"),
        "thoughts": state.get("thoughts", []),
        "assistant_msg_id": state.get("assistant_msg_id")
    }

    

# New analytics endpoint
@app.get("/analytics/")
def get_analytics():
    evaluator = Evaluator()
    return evaluator.compute_statistics()
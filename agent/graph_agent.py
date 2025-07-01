from tools.web_search import SearchWeb
from tools.retriever import Retriever
from tools.classifier import Classifier
from tools.evaluation import Evaluator
from utilities.utilities import Utilities
from tools.gemini_client import GeminiClient

from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda, RunnableSequence, RunnableBranch
from typing import TypedDict, Literal, Optional, List, Any
from pathlib import Path
from dotenv import load_dotenv; load_dotenv()

# Define the structure of the state passed through the graph.
class AgentState(TypedDict):

    # User query string.
    query: str

    # The retriever tool instance.
    retriever: Any
    
    # The answer retrieved from internal data.
    internal_answer: Optional[str]

    # The source of the internal data.
    internal_source: Optional[str]

    # Internal context, if applicable.
    internal_context: Optional[str]

    # The answer retrieved from web search, if applicable.
    web_answer: Optional[str]

    # The source of the web search result, if applicable.
    web_source: Optional[str]

    # The score from the classifier, if applicable.
    classifier_score: Optional[float]

    # Flag indicating if web search was attempted.
    web_search_attempted: Optional[bool]
    
    # Reasoning trace.
    thoughts: List[str]

    # ID of the conversation this agent is part of.
    conversation_id: int

    # ID of the assistant message in the conversation.
    assistant_msg_id: Optional[int]

    # Length of the conversation history.
    history_length: int

class GraphAgent:

    # Initialize the agent with its tools and logic.
    def __init__(self):

        # BASE_DIR = Path.cwd().parent
        # DATA_DIR = BASE_DIR / 'jedi-team-AI-challenge' / 'data'
        # FILEPATH = DATA_DIR / "data.md"
        BASE_DIR = Path.cwd()
        DATA_DIR = BASE_DIR / 'data'
        FILEPATH = DATA_DIR / "data.md"

        # Load the fragments from the .md file.
        self.fragments = Utilities.load_fragments_from_md(FILEPATH)

        # Initialize the retriever tool (e.g., FAISS + encoder).
        self.retriever = Retriever(self.fragments)

        # Initialize classifier tool.
        self.classifier = Classifier()

        # Compile the graph.
        self.graph = self.build_graph()
    
    # Perform semantic search over internal data.
    def rag_node(self, state: AgentState) -> tuple[Literal["found", "not_found"], AgentState]:

        # Log step in reasoning trace.
        state["thoughts"].append("Attempting semantic search over internal data.")

        # Run top-k vector search on internal fragments.
        results = state["retriever"].search(state["query"], top_k=1)

        # If at least one match is found.
        if results:

            # Store the best answer's text
            state["internal_answer"] = results[0]["text"]

            # Store its source, defaulting to data.md.
            state["internal_source"] = results[0].get("source", "data.md")

            # After retrieving the internal fragment, store the same fragment as the context
            state["internal_context"] = results[0].get("context", results[0]["text"])

            # Log successful retrieval.
            state["thoughts"].append("Found internal result.")

            # Indicate success for conditional routing.
            return {"__condition__": "found", **state}

        # Log failure to find internal match.
        state["thoughts"].append("No good internal result found.")

        # Indicate failure for fallback path.
        return {"__condition__": "not_found", **state}
    
    # Fallback web search node, if no internal data is found.
    def web_search_node(self, state: AgentState) -> AgentState:

        state["thoughts"].append("Running web search as fallback.")

        # Perform search.
        result, source = SearchWeb.run(state["query"])

        # Save to state.
        state["web_answer"] = result
        state["web_source"] = source
        state["web_search_attempted"] = True

        # print(f"Web search result: {result}")
        # print(f"Web search source: {source}")

        # Log completion.
        state["thoughts"].append("Web search completed.")


        # Return state with web search results.
        return state

    # Query - Answer relevance classifier node.
    def classify_node(self, state: AgentState) -> AgentState:
        state["thoughts"].append("Running classifier to evaluate answer quality.")

        # Choose the most relevant answer (internal or web).
        answer = state["internal_answer"] or state["web_answer"] or ""
        
        # Run similarity classifier.
        state["classifier_score"] = self.classifier.score(state["query"], answer)

        # Log the classifier score.
        state["thoughts"].append(f"Classifier score: {state['classifier_score']:.2f}")

        return state
    
    # Define routing based on classifier score.
    def router_node(self, state: AgentState) -> str:

        # Determine which method was used to generate the current answer.
        method = "rag" if state.get("internal_answer") else "web_search"
        threshold = Utilities.get_threshold(method)
        score = state.get("classifier_score", 0)

        if score >= threshold:
            state["thoughts"].append(
                f"Classifier score {score:.2f} >= threshold {threshold:.2f}. Accepting answer."
            )
            return {"__condition__": "final", **state}

        # If below threshold
        state["thoughts"].append(
            f"Classifier score {score:.2f} < threshold {threshold:.2f}. Rejecting answer due to low confidence."
        )

        # If web search was already attempted and failed, fallback
        if state.get("web_search_attempted"):
            state["internal_answer"] = (
                "I'm sorry, I couldn't find enough trustworthy information to answer your question."
            )
            state["internal_source"] = "Agent"
            state["used_fallback"] = True  # <-- Mark fallback explicitly
            state["thoughts"].append("Web search also failed. No reliable answer found. Returning fallback message.")
            return {"__condition__": "final", **state}

        # Otherwise try web search
        return {"__condition__": "web_fallback", **state}

    # Log the assistant's message in the conversation.
    def log_message_node(self, state: AgentState) -> AgentState:

        answer = state.get("internal_answer") or state.get("web_answer")
        source = state.get("internal_source") or state.get("web_source")
        thoughts = state.get("thoughts", [])

        message_id = Utilities.save_message(
            state["conversation_id"],
            "assistant",
            answer,
            source=source,
            thoughts=thoughts
        )

        state["assistant_msg_id"] = message_id
        state["thoughts"].append(f"Assistant message logged with ID {message_id}.")
        return state

    # Evaluate the final state and log reasoning trace.
    def evaluate_node(self, state: AgentState) -> AgentState:

        # Run evaluation on the final state.
        Evaluator.run(state, state["assistant_msg_id"])

        # Update reasoning trace.
        state["thoughts"].append("Evaluation complete.")

        return state

    # Generate a title for the conversation.
    def generate_title_node(self, state: AgentState) -> AgentState:
        if state["history_length"] == 1:
            messages = Utilities.load_messages(state["conversation_id"])
            if messages:
                gemini = GeminiClient()
                title = gemini.summarize_conversation_title(messages[:1])
                Utilities.update_conversation_title(state["conversation_id"], title)
                state["thoughts"].append("Generated conversation title.")
        return state

    # Finalize and return result.
    def final_node(self, state: AgentState) -> AgentState:

        # Log conclusion step.
        state["thoughts"].append("Returning final answer with citation.")

        # # Evaluate/log final output
        # Evaluator.run(state)

        # Return final state.
        return state

    # Construct the reasoning graph and define transitions.
    def build_graph(self):

        # Create graph builder with shared state schema.
        builder = StateGraph(AgentState)

        # Node for semantic search over internal data.
        builder.add_node("rag", self.rag_node)

        # Node for web search fallback, if no internal data is found.
        builder.add_node("web_search", self.web_search_node)

        # Node for classifying the answer quality.
        builder.add_node("classify", self.classify_node)

        # Node for routing based on classifier score.
        builder.add_node("router", self.router_node)

        # Node for finalizing the answer.
        builder.add_node("final", self.final_node)

        # Node for logging the assistant's message in the conversation.
        builder.add_node("log_message", self.log_message_node)

        # Node for evaluating the final state.
        builder.add_node("evaluate", self.evaluate_node)

        # Node for generating a conversation title.
        builder.add_node("generate_title", self.generate_title_node)

        # Set the entry point of the graph.
        builder.set_entry_point("rag")

        # Step 1: RAG node outcome (found or not_found)
        builder.add_conditional_edges(
            "rag",
            lambda state: state["__condition__"],
            {
                "found": "classify",
                "not_found": "web_search"
            }
        )

        # Step 2: After web search, go to classification
        builder.add_edge("web_search", "classify")

        # Step 3: After classification, go to router
        builder.add_edge("classify", "router")

        # Step 4: Router decides:
        builder.add_conditional_edges(
            "router",
            lambda state: state["__condition__"],
            {
                "final": "final",
                "web_fallback": "web_search"
            }
        )

        # Step 5: Final node to log the message.
        builder.add_edge("final", "log_message")

        # Step 6: Log message node to evaluate.
        builder.add_edge("log_message", "evaluate")

        # Step 7: Evaluate then possibly generate title
        builder.add_edge("evaluate", "generate_title")

        # Step 8: End after optional title generation
        builder.add_edge("generate_title", END)

        # Compile into runnable graph
        return builder.compile()
    
    # Run the graph with a query.
    def run(self, query: str, conversation_id: int, history_length: int):

        initial_state: AgentState = {
            "query": query,
            "conversation_id": conversation_id,
            "history_length": history_length,
            "retriever": self.retriever,
            "internal_answer": None,
            "internal_source": None,
            "web_answer": None,
            "web_source": None,
            "web_search_attempted": False,
            "thoughts": [],
            "assistant_msg_id": None
        }

        # Invoke the graph with the initial state.
        return self.graph.invoke(initial_state)
    
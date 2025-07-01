import json
from datetime import datetime
from pathlib import Path
# from collections import Counter, defaultdict
# import statistics

from utilities.utilities import Utilities
from tools.gemini_client import GeminiClient

class Evaluator:

    def __init__(self):

        self.gemini = GeminiClient()
    
    # Determine the source type based on the state.
    def _get_method(self, state):
        if state.get("used_fallback"):
            return "fallback"
        elif state.get("internal_answer") and state.get("internal_source") != "Agent":
            return "rag"
        elif state.get("web_answer"):
            return "web_search"
        return "unknown"
    
    # Determine if the source is internal or external.
    def _get_source_type(self, state):
        source = state.get("internal_source") or state.get("web_source") or ""
        if "data.md" in Path(source).name:
            return "internal"
        return "external"
    
    def evaluation_log(self, state: dict):
        with Utilities.get_connection() as conn:
            with conn.cursor() as cur:
                # Ensure the log table exists
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS agent_logs (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMPTZ NOT NULL,
                        query TEXT,
                        final_answer TEXT,
                        method TEXT,
                        classifier_score REAL,
                        source TEXT,
                        source_type TEXT,
                        grounded_context TEXT,
                        thoughts JSONB,
                        notes TEXT
                    );
                """)

                # Insert log record
                cur.execute("""
                    INSERT INTO agent_logs (
                        timestamp, query, final_answer, method, classifier_score,
                        source, source_type, grounded_context, thoughts, notes
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                """, (
                    datetime.now(),
                    state.get("query"),
                    state.get("internal_answer") or state.get("web_answer"),
                    self._get_method(state),
                    state.get("classifier_score"),
                    state.get("internal_source") or state.get("web_source"),
                    self._get_source_type(state),
                    state.get("internal_context"),
                    json.dumps(state.get("thoughts", [])),
                    ""
                ))

            conn.commit()
    
    def log(self, state: dict, message_id: int):
        # Attach method + source_type to an existing assistant message
        method = self._get_method(state)
        source_type = self._get_source_type(state)
        score = state.get("classifier_score")

        with Utilities.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE messages 
                    SET method = %s, source_type = %s, score = %s
                    WHERE id = %s
                """, (method, source_type, score, message_id))
            conn.commit()

    def compute_statistics(self):
        with Utilities.get_connection() as conn:
            with conn.cursor() as cur:
                # Total number of assistant messages (i.e., responses).
                cur.execute("SELECT COUNT(*) FROM messages WHERE role = 'assistant';")
                total_queries = cur.fetchone()[0]

                # Count per method.
                cur.execute("""
                    SELECT method, COUNT(*) 
                    FROM messages 
                    WHERE role = 'assistant' AND method IS NOT NULL
                    GROUP BY method;
                """)
                method_counts = dict(cur.fetchall())

                # Count per source_type.
                cur.execute("""
                    SELECT source_type, COUNT(*)
                    FROM messages
                    WHERE role = 'assistant' AND source_type IS NOT NULL
                    GROUP BY source_type;
                """)
                source_type_counts = dict(cur.fetchall())

                # Avg score per method.
                cur.execute("""
                    SELECT method, AVG(score)
                    FROM messages
                    WHERE role = 'assistant' AND score IS NOT NULL
                    GROUP BY method;
                """)
                avg_scores = {row[0]: round(row[1], 3) for row in cur.fetchall()}

        summary = {
            "total_queries": total_queries,
            "method_counts": method_counts,
            "source_type_counts": source_type_counts,
            "avg_scores": avg_scores
        }

        #print(json.dumps(summary, indent=2))
        return summary
    
    def create_evaluation_table_if_not_exists(self, conn):
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS response_evaluation (
                    id SERIAL PRIMARY KEY,
                    response_id INTEGER NOT NULL REFERENCES messages(id),
                    query TEXT,
                    answer TEXT,
                    feedback INTEGER,
                    correctness FLOAT NOT NULL,
                    relevance FLOAT NOT NULL,
                    fluency FLOAT NOT NULL,
                    comment TEXT,
                    weighted_score FLOAT,
                    final_score FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def store_response_evaluation(self, conn, message_id: int, scores: dict, query: str, answer: str):
        if not scores:
            return

        correctness = float(scores["correctness"])
        relevance = float(scores["relevance"])
        fluency = float(scores["fluency"])
        comment = scores.get("comment", "")
        weighted = round(0.4 * correctness + 0.4 * relevance + 0.2 * fluency, 3)

        # Get user feedback
        with conn.cursor() as cur:
            cur.execute("SELECT feedback FROM messages WHERE id = %s", (message_id,))
            row = cur.fetchone()
            feedback = row[0] if row else None

        # Normalize feedback
        if feedback == 1:
            feedback_score = 1.0
        elif feedback == -1:
            feedback_score = 0.0
        else:
            feedback_score = 0.5

        final_score = round(0.8 * weighted + 0.2 * feedback_score, 3)

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO response_evaluation (
                    response_id, query, answer, feedback,
                    correctness, relevance, fluency, comment,
                    weighted_score, final_score
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                message_id,
                query,
                answer,
                feedback,
                correctness,
                relevance,
                fluency,
                comment,
                weighted,
                final_score
            ))

    def evaluate_response_with_gemini(self, query: str, answer: str, context: str = None) -> dict:
        try:
            raw = self.gemini.evaluate_response(query, answer, context)
            # Remove Markdown code fences
            if raw.startswith("```json"):
                raw = raw.strip("`").split("json", 1)[-1].strip()
            elif raw.startswith("```"):
                raw = raw.strip("`").split("```", 1)[-1].strip()

            return json.loads(raw)
        except Exception as e:
            print(f"[Evaluation failed: {e}]")
            return {}
    
    def update_feedback_in_response_evaluation(self, conn, message_id: int):
        with conn.cursor() as cur:
            # Get latest feedback from messages
            cur.execute("SELECT feedback FROM messages WHERE id = %s", (message_id,))
            row = cur.fetchone()
            feedback_raw = row[0] if row else None

            # Map textual feedback to numeric value
            if feedback_raw == "up":
                feedback = 1.0
            elif feedback_raw == "down":
                feedback = 0.0
            else:
                feedback = 0.5

            # Update existing response_evaluation row
            cur.execute("""
                UPDATE response_evaluation
                SET feedback = %s
                WHERE response_id = %s;
            """, (feedback, message_id))

    def pipeline(self, state: dict, message_id: int):

        # Step 1: Basic logging.
        self.log(state, message_id)
        self.evaluation_log(state)

        with Utilities.get_connection() as conn:
            self.create_evaluation_table_if_not_exists(conn)

            query = state.get("query")
            answer = state.get("internal_answer") or state.get("web_answer")
            context = state.get("internal_context") or ""

            scores = self.evaluate_response_with_gemini(query, answer, context)
            self.store_response_evaluation(conn, message_id, scores, query, answer)

            conn.commit()

        self.compute_statistics()

    @classmethod
    def run(cls, state: dict, message_id: int):
        """
        Run the evaluation pipeline with the provided state.
        This method is a convenience wrapper for logging.
        """
        evaluator = cls()
        evaluator.pipeline(state, message_id)
        return state
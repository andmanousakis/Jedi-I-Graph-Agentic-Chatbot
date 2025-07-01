from pathlib import Path
import json
import psycopg2
import os
import numpy as np
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

class Utilities:

    def __init__(self):

        pass

    @staticmethod
    def colors(color_desc: str = None):

        if color_desc == 'red':
            return "\033[31m"
        
        if color_desc == 'black':
            return "\033[30m"
        
        if color_desc == 'green':
            return "\033[32m"

        if color_desc == 'white':
            return "\033[37m"

        if color_desc == 'blue':
            return "\033[34m"
        
        elif color_desc == 'yellow':
            return "\033[33m"

    @staticmethod
    def load_fragments_from_md(filepath) -> list[dict]:

        # Load text fragments from a Markdown file.
        fragments = []

        # Read the file line by line, stripping whitespace and ignoring empty lines.
        with open(filepath, "r") as f:

            # Each non-empty line is treated as a separate text fragment.
            for line in f:

                # Clean line: strip whitespace and '|' characters.
                clean_line = line.strip().strip('|').strip()

                # If the line is not empty, add it as a fragment.
                if clean_line:

                    # Create a list of dictionaries with the text and its source file. Retrieve source's absolute path.
                    fragments.append({"text": clean_line, "source": str(Path(filepath).resolve())})
        
        # Return the list of text fragments.
        return fragments

    @staticmethod
    def get_threshold(method="default"):
        if method == "rag":
            return 0.65
        elif method == "web_search":
            return 0.5
        else:
            return 0.70
    
    @staticmethod
    def get_connection():

        return psycopg2.connect(
            dbname=os.getenv("PG_DB_NAME"), 
            user=os.getenv("PG_DB_USERNAME"),
            password=os.getenv("PG_DB_PASSWORD"),
            host="jedi_db",
            port=5432
        )
    
    @staticmethod
    def fetch_conversations():
        with Utilities.get_connection() as conn:
            with conn.cursor() as cur:
                # Ensure the conversations table exists
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id SERIAL PRIMARY KEY,
                        title TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                # Now fetch the conversations
                cur.execute("SELECT id, title FROM conversations ORDER BY created_at DESC;")
                return cur.fetchall()

    @staticmethod
    def create_conversation(title="Untitled Chat"):
        with Utilities.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO conversations (title) VALUES (%s) RETURNING id;", (title,))
                conn.commit()
                return cur.fetchone()[0]
    
    @staticmethod
    def save_message(convo_id, role, content, source=None, thoughts=None):
        with Utilities.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO messages (conversation_id, role, content, source, thoughts)
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                    RETURNING id
                """, (convo_id, role, content, source, json.dumps(thoughts)))
                message_id = cur.fetchone()[0]
            conn.commit()
        return message_id
    
    @staticmethod
    def load_messages(convo_id):
        with Utilities.get_connection() as conn:
            with conn.cursor() as cur:
                # Ensure the table exists
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id SERIAL PRIMARY KEY,
                        conversation_id INTEGER NOT NULL REFERENCES conversations(id),
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        source TEXT,
                        thoughts JSONB,
                        feedback INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # Now run the query
                cur.execute("""
                    SELECT id, role, content, source, thoughts, feedback
                    FROM messages
                    WHERE conversation_id = %s
                    ORDER BY created_at ASC;
                """, (convo_id,))
                
                rows = cur.fetchall()
                return [{
                    "id": row[0],
                    "role": row[1],
                    "content": row[2],
                    "source": row[3],
                    "thoughts": row[4] or [],
                    "feedback": row[5]  # may be None, 1 (up), or -1 (down)
                } for row in rows]
    
    @staticmethod
    def update_conversation_title(convo_id: int, title: str):
        with Utilities.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE conversations SET title = %s WHERE id = %s", (title, convo_id))
            conn.commit()
    
    @staticmethod
    def set_feedback(message_id: int, feedback: str):
        with Utilities.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE messages SET feedback = %s WHERE id = %s", (feedback, message_id))
            conn.commit()
    
    @staticmethod
    def count_messages(convo_id: int) -> int:
        with Utilities.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM messages WHERE conversation_id = %s", (convo_id,))
                result = cur.fetchone()
                return result[0] if result else 0
    
    @staticmethod
    def initialize_database():
        with Utilities.get_connection() as conn:
            with conn.cursor() as cur:
                # Create conversations table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id SERIAL PRIMARY KEY,
                        title TEXT DEFAULT 'Untitled Chat',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # Create messages table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id SERIAL PRIMARY KEY,
                        conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
                        role TEXT CHECK (role IN ('user', 'assistant')) NOT NULL,
                        content TEXT,
                        answer TEXT,
                        source TEXT,
                        score REAL,
                        method TEXT,
                        source_type TEXT,
                        thoughts JSONB,
                        feedback TEXT CHECK (feedback IN ('up', 'down')),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
            conn.commit()
    
    @staticmethod
    def create_database_if_not_exists():
        
        db_name = os.getenv("PG_DB_NAME")
        db_user = os.getenv("PG_DB_USERNAME")
        db_password = os.getenv("PG_DB_PASSWORD")
        db_host = "jedi_db"

        # Connect to default 'postgres' DB to check if target DB exists
        conn = psycopg2.connect(
            dbname="postgres",
            user=db_user,
            password=db_password,
            host=db_host,
            port=5432
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if DB exists
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cur.fetchone()
        
        if not exists:
            cur.execute(f'CREATE DATABASE "{db_name}"')
            print(f"Created database: {db_name}")
        else:
            print(f"Database already exists: {db_name}")

        cur.close()
        conn.close()
    
    @staticmethod
    def update_feedback_in_response_evaluation(message_id: int):
        from tools.evaluation import Evaluator  # Import here to avoid circular imports
        
        evaluator = Evaluator()
        with Utilities.get_connection() as conn:
            evaluator.update_feedback_in_response_evaluation(conn, message_id)
            conn.commit()
    
    @staticmethod
    def create_fragments_table_if_not_exists():
        with Utilities.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS fragments (
                        id SERIAL PRIMARY KEY,
                        text TEXT NOT NULL,
                        source TEXT,
                        embedding BYTEA
                    );
                """)
            conn.commit()
    
    @staticmethod
    def save_fragments_with_embeddings(fragments: list[dict], embeddings: np.ndarray):
        """
        Save fragments and their corresponding embeddings to the DB,
        avoiding duplicates based on fragment text and source.
        """
        with Utilities.get_connection() as conn:
            with conn.cursor() as cur:
                for fragment, embedding in zip(fragments, embeddings):
                    # Check if fragment already exists
                    cur.execute("""
                        SELECT id FROM fragments WHERE text = %s AND source = %s
                    """, (fragment["text"], fragment["source"]))
                    exists = cur.fetchone()

                    if not exists:
                        cur.execute("""
                            INSERT INTO fragments (text, source, embedding)
                            VALUES (%s, %s, %s)
                        """, (
                            fragment["text"],
                            fragment["source"],
                            psycopg2.Binary(embedding.astype(np.float32).tobytes())
                        ))
            conn.commit()
    
    @staticmethod
    def load_stored_fragments_with_embeddings() -> dict:
        """
        Load all stored fragments and their embeddings from the database.
        Returns:
            dict: { (text, source): np.ndarray }
        """
        stored = {}
        with Utilities.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT text, source, embedding FROM fragments;")
                for text, source, embedding in cur.fetchall():
                    key = (text, source)
                    stored[key] = np.frombuffer(embedding, dtype=np.float32)
        return stored
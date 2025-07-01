import os
import google.generativeai as genai

class GeminiClient:

    def __init__(self):

        # Read the Gemini API key from environment.
        api_key = os.getenv("GEMINI_API_KEY")

        # Configure Gemini client.
        genai.configure(api_key=api_key)

        # Create the generative model.
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def refine_answer(self, query: str, answer: str, context: str) -> str:

        prompt = f"""
            You are refining an answer strictly using internal company documentation. 

            - Query: {query}
            - Answer: {answer}
            - Context (source fragment): {context}

            Refine the answer only if the context clearly contains the answer. 
            If it does not, respond with:

            "I'm sorry, I don't have enough information to answer that from the available data."

            Do NOT use external knowledge. Do NOT guess or fabricate any information.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"[Refinement failed: {e}]"

    def evaluate_response(self, query: str, answer: str, context: str = None) -> str:
        prompt = f"""
            You are evaluating the quality of an AI assistant's answer.

            [User Query]
            {query}

            [Assistant Response]
            {answer}

            [Optional: Retrieved Context or Source]
            {context if context else "None"}

            Rate the assistant's response on the following criteria:

            1. Correctness (0 to 1): Is the answer factually accurate and complete?
            2. Relevance (0 to 1): Is the answer clearly related to the question?
            3. Fluency (0 to 1): Is the answer grammatically and stylistically good?

            Respond with only raw JSON — no explanation, no markdown formatting, no ```json fences.:

            {{
            "correctness": float,
            "relevance": float,
            "fluency": float,
            "comment": "Short explanation (1-2 sentences)"
            }}

            Do NOT provide any additional text outside of this JSON format.
            """
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"[Evaluation failed: {e}]"

    def summarize_conversation_title(self, messages: list[dict]) -> str:
        prompt = (
            "Generate a concise, human-readable title for the following conversation. "
            "Focus on the main topic discussed, using no more than 7 words. Avoid vague or generic titles.\n\n"
        )
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            prompt += f"{role.capitalize()}: {content}\n"

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip().strip('"')
        except Exception as e:
            return f"[Title generation failed: {e}]"
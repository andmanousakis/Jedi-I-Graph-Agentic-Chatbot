### MINOR RELEASE - [v0.10.0] - 28-06-25  

### DONE

**FAISS Vector Index Optimization**
- Introduced build-time FAISS index generation via `tools/build_faiss_index.py` for static fragments.
- Reduced runtime overhead by precomputing and storing `fragments.index`.
- Enabled faster API startup and retrieval due to cached embedding usage.

**Retriever Improvements**
- Reworked `Retriever` to skip recomputation for existing embeddings.
- Ensured FAISS index only builds if valid embeddings are available.
- Enhanced performance by avoiding unnecessary SentenceTransformer downloads.

**Docker Enhancements**
- Optimized Docker build to cache and persist FAISS index during image creation.
- Reduced API container cold start time significantly.
- Added new Docker layer to run index builder script at build stage.

**Testing Additions**
- Added unit test for FAISS index creation to ensure reliability.
- Verified FAISS file output and vector dimensions with automated tests.

**Refactoring and Maintenance**
- Cleaned up redundant index-writing logic.
- Improved error handling for empty or malformed fragment data.
- Aligned folder paths and ensured consistent vector DB output across environments.

### PENDING
- Unit test for `tools/build_faiss_index.py`.

### BUGS
- None

----------------------------------------------------------

### MINOR RELEASE - [v0.9.0] - 23-06-25

### DONE

- **Containerisation (Docker)**
- The project has been fully containerized using **Docker**, enabling consistent deployment across environments.
- Individual containers have been configured for:
  - The **API backend** (FastAPI + Uvicorn)
  - The **UI frontend** (Streamlit)
  - The **PostgreSQL database**
- A **shared base image** is used to reduce redundancy and accelerate build times.
- **Docker Compose** orchestrates the multi-container setup:
  - Ensures correct startup order (e.g., DB → API → UI)
  - Supports volume mounting for live development
- Environment variables are handled securely via `.env` files.
- This setup improves **portability**, **reproducibility**, and **ease of deployment**.
- Added response evaluation to cater for refined training dataset and fine tuning.

### PENDING

- None

----------------------------------------------------------

### MINOR RELEASE - [v0.8.0] - 23-06-25

### DONE

- Added unit tests for:
  - `GraphAgent`
  - FastAPI `api` endpoints
  - `Classifier` (semantic similarity)
  - `Evaluator` (Gemini-based evaluation + statistics)
  - `GeminiClient` (summarization + scoring)
  - `Retriever` (FAISS search)
  - `SearchWeb` (Serper API interface)
- Integrated **LLM-based response evaluation** (correctness, relevance, fluency)
- Persisted evaluation scores and classifier scores in database
- Logged detailed reasoning trace and assistant message metadata

### PENDING

- Containerisation (Docker) 

----------------------------------------------------------


### MINOR RELEASE - [v0.7.0] - 23-06-25

### DONE
- **Agent message feedback system:**  
  Users can now give a **thumbs-up (👍)** or **thumbs-down (👎)** on any assistant message directly in the chat. This feedback is persisted in the database alongside the message, allowing for later review, quality analysis, and fine-tuning of agent behavior. Feedback state is displayed in-line after interaction, creating a seamless and intuitive evaluation loop.

- **Tool usage logging and analytics dashboard:**  
  Every assistant response now logs the **method of answer generation** (`rag`, `web_search`, or `fallback`) and the **source type** (`internal`, `external`). These logs are aggregated into a lightweight analytics module, exposed via a FastAPI endpoint and rendered as **interactive charts in the Streamlit sidebar**. This allows users and developers to monitor system behavior over time — including the percentage of answers resolved without web search and the average classifier scores across methods.

- **Automatic database initialization on startup:**  
  The backend now performs a **startup check** to ensure all required databases and tables exist. If any component is missing (e.g., the main database or feedback logging tables), it is **automatically created** during application boot. This ensures a smooth first-time setup and prevents runtime errors due to missing infrastructure.

### PENDING
- Finetune the Agent Based on Feedback:
  - Incorporate user feedback and evaluation outcomes to improve agent behavior.
  - Retrain models, adjust prompts, or refine routing logic based on evaluation insights.
- Containerization & dev automation:
  - Create a `Dockerfile` or one-command dev script (e.g., `make`, `task`, or `invoke`) for setup.
- Deployment-ready configuration:
  - Document environment setup and deployment steps for a cloud target (e.g., Render, Fly.io, GCP).


----------------------------------------------------------


### MINOR RELEASE - [v0.6.0] - 22-06-25

### DONE
- Created full Streamlit UI:
  - Sidebar for conversation selection and creation.
  - Chat history rendering with markdown, sources, and reasoning trace display.
  - Real-time chat input and dynamic rerendering.
- Built FastAPI backend:
  - Exposes `/` POST endpoint to handle user queries.
  - Receives question payloads and returns assistant answers with metadata (answer, source, thoughts).
- Implemented persistent conversation storage with PostgreSQL:
  - Conversation titles and messages (with role, content, source, and thoughts) are stored in a relational schema.
  - Fetch and store operations abstracted in `Utilities` module.
- Integrated Gemini-based title summarization:
  - After the first user message, a short title is generated using Gemini 2.0 Flash.
  - Title is saved in the database and displayed in the sidebar.
  - Logic uses an instance-based `GeminiClient` to avoid broken `@classmethod` access.
- Fixed session state logic:
  - Prevented message overwrite on rerun by guarding `chat_history` initialization.
  - Ensured message history loads and persists correctly across app reloads.
- Handled empty state cases:
  - Prevented crashes when no conversations exist.
  - Added fallback UI to guide users to start a new conversation cleanly.

### PENDING
- Finetune the Agent Based on Feedback:
  - Incorporate user feedback and evaluation outcomes to improve agent behavior.
  - Retrain models, adjust prompts, or refine routing logic based on evaluation insights.
- Add thumbs‑up / thumbs‑down feedback system:
  - Allow users to rate individual assistant messages directly in the UI.
  - Store ratings for future tuning or supervised evaluation.
- Surface lightweight analytics:
  - Track and log tool usage (e.g., % of queries resolved via internal data vs. web).
  - Display summary metrics to understand agent behavior in practice.
- Containerization & dev automation:
  - Create a `Dockerfile` or one-command dev script (e.g., `make`, `task`, or `invoke`) for setup.
- Deployment-ready configuration:
  - Document environment setup and deployment steps for a cloud target (e.g., Render, Fly.io, GCP).

### BUGS
- Fixed conversation message loss:
  - Removed unconditional `st.session_state.chat_history = []` which wiped messages on every rerun.
- Fixed crash when no conversations existed:
  - Handled empty state in the conversation selector (`NoneType.split()` error).
- Fixed broken Gemini title generation logic:
  - Replaced invalid `@classmethod` usage with an instance-based method using `self.model`.
- Prevented conversation reload issues:
  - Ensured `chat_history` loads only once and isn’t reloaded unnecessarily.
- Manually reset PostgreSQL ID sequences:
  - Resolved issue where conversation IDs did not restart from 1 after deletion.


----------------------------------------------------------


### MAJOR RELEASE - [v0.5.0] - 22-06-25

### DONE
- Integrated full evaluation logging pipeline:
  - Logs each query with method used (`rag`, `web_search`, `refined_rag`), classifier score, source type, and reasoning trace.
  - Includes timestamped JSONL logging for longitudinal tracking.
- Implemented `Evaluator` class:
  - Computes aggregate statistics across all logs.
  - Derives recommendations (e.g., when to disable LLM refinement, adjust classifier threshold, or prefer web search).
  - Writes actionable config to `agent_recommendations.json`.
- Dynamically adapts agent behavior at runtime based on evaluation insights:
  - Reads from `agent_recommendations.json`.
  - Supports toggling LLM refinement, adjusting classifier thresholds, and skipping internal search when RAG underperforms.
- Added conditional bypass logic for `rag_node()`:
  - Automatically routes queries to web search if `prefer_web_for_unknowns` is active.
- Improved `router_node()` with safe refinement gating:
  - LLM refinement only triggered if internal source is `data.md`, classifier score is low, and refinement isn't disabled.
- Final answer and trace logged using `Evaluator.run(state)` at graph exit.

### PENDING
- Incorporate user feedback loop (thumbs up/down).
- Allow user-suggested answers to be logged and curated for retraining.
- Add faithfulness check to LLM refinement (e.g., embedding similarity or LLM critique).
- Enable question type routing (e.g., news/current → web).

### BUGS
- Fixed crash in `router_node()` when `internal_source` was `None` (caused by `Path(None)` call).
- Prevented infinite LLM refinement loop with `refine_attempts` limit.
- Ensured `rag_node()` respects evaluation-driven override via `prefer_web_first()`.

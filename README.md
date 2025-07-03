# Jedi I - AI Graph Agentic Chatbot

This project is a containerized AI assistant system. It features the jedi graph agent chatbot, an API to stream the chat and analytics to a streamlit UI, a postgres db and unit tests.

## Startup

1. Create a folder where you want to store the project.

2. Go to that folder and run:

  ``git clone --branch production https://github.com/andmanousakis/Jedi-I-Graph-Agentic-Chatbot.git``

3. Navigate to docker dir:

   - Run ``./start`` to build the app.
   - Run ``./clean`` to stop/delete images and containers.

## Configuration

- All enviroment variables, API keys and model endpoints can be found in the .env file.

## Testing

- Unit tests can be found in the tests dir.

## Evaluation

- Performane statistics are visualized in the UI.


## Features

1. Retrieve answers from internal data:

   - Exact match or similarity search is acceptable.
   - Source citation.

2. Graph-based agent reasoning:

   - Look into the dataset, classify response. If not satisfying, resort to web search. Classify response. If not satisfying reply that there is not enough info to answer adequately.

3. Tools:

   - Web-search.
   - RAG lookup.
   - Classifier.

4. Evaluate and Score Agent Responses:

   - Weighted scores are calculated as a function of coherence, relevance, etc for response evaluation.
   - To be used for enhanced graph agent reasoning.

5. Finetune the Agent Based on Feedback:

   - Query-answer final scores are calculated taking into account user feedback.
   - The pairs can be used as a training set for further finetuning.

6. Multiple concurrent chats persistence. One user is currently supported.

7. Fast API to expose an HTTP interface that allows a streamlit UI to stream the agent’s intermediate reasoning (“thoughts”) and final answers.

8. Auto‑generation of concise, human‑readable title for every new chat.

9. Thumbs‑up / thumbs‑down feedback on any agent message.

10. Quick log tool invocations on the UI with simple analytics.

11. Unit tests for core functionalities.

12. Docker containerization: API, UI, Unit Tests.

### Important

In case you receive an error that the pg port is already in use, please follow the steps below:

1. Stop the process using port 5432. This will show the process using the port: 
   
   ``sudo lsof -i :5432`` -> Get the PID

2. Then stop it with: ``sudo kill -9 <PID>``

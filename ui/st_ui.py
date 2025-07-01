import streamlit as st
import requests
import os
import sys
import html
from pathlib import Path
import pandas as pd
import plotly.express as px

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utilities.utilities import Utilities

API_URL_ASK_JEDI_AGENT = os.getenv("API_URL_ASK_JEDI_AGENT")
API_URL_ANALYTICS = os.getenv("API_URL_ANALYTICS")
st.set_page_config(page_title="Jedi Agent", layout="wide")


# ------------------- Conversation Selection -------------------
conversations = Utilities.fetch_conversations()
options = [f"{cid} - {title}" for cid, title in conversations]
if "selected_convo" not in st.session_state:
    if conversations:
        convo_id, _ = conversations[0]  # Select most recent
    else:
        convo_id = Utilities.create_conversation()
    st.session_state.selected_convo = convo_id
    st.session_state.chat_history = Utilities.load_messages(convo_id)

# UI buttons and selection
if st.sidebar.button("New Conversation"):
    new_id = Utilities.create_conversation()
    st.session_state.selected_convo = new_id
    st.session_state.chat_history = []
    st.rerun()

if options:
    selected = st.sidebar.selectbox("Select Conversation", options)
    selected_id = int(selected.split(" - ")[0])
    if selected_id != st.session_state.selected_convo:
        st.session_state.selected_convo = selected_id
        st.session_state.chat_history = Utilities.load_messages(selected_id)
else:
    st.sidebar.info("No conversations available. Start a new one.")

# --- Inline Sidebar Analytics ---
try:
    response = requests.get(API_URL_ANALYTICS)
    if response.status_code == 200:
        data = response.json()

        # Method distribution pie chart.
        method_df = pd.DataFrame(list(data["method_counts"].items()), columns=["Method", "Count"])
        fig1 = px.pie(method_df, names="Method", values="Count", height=200)
        fig1.update_layout(
            margin=dict(t=30, b=10, l=10, r=10),
            showlegend=False
        )
        st.sidebar.plotly_chart(fig1, use_container_width=True)

        # Source type distribution pie chart.
        source_df = pd.DataFrame(list(data["source_type_counts"].items()), columns=["Source Type", "Count"])
        fig2 = px.pie(source_df, names="Source Type", values="Count", height=200)
        fig2.update_layout(
            margin=dict(t=30, b=10, l=10, r=10),
            showlegend=False
        )
        st.sidebar.plotly_chart(fig2, use_container_width=True)

        # Average score bar chart.
        score_df = pd.DataFrame(list(data["avg_scores"].items()), columns=["Method", "Avg Score"])
        fig3 = px.bar(score_df, x="Method", y="Avg Score", height=200)
        fig3.update_layout(
            margin=dict(t=30, b=10, l=10, r=10),
            xaxis_title=None,
            yaxis_title=None,
            xaxis=dict(showticklabels=False),
            yaxis=dict(showticklabels=False)
        )
        st.sidebar.plotly_chart(fig3, use_container_width=True)

        # Total queries as a small metric.
        st.sidebar.markdown(f"""
            <div style='margin-top: -0.5rem; text-align: center;'>
                <b>Total Queries:</b><br>{data['total_queries']}
            </div>
        """, unsafe_allow_html=True)

    else:
        st.sidebar.error("Analytics fetch failed.")
except Exception as e:
    st.sidebar.error(f"Analytics error: {e}")


# ------------------- Display Chat History -------------------
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.markdown(f"""
            <div style="display: flex; justify-content: flex-end; margin: 0.25em 0;">
                <div style="
                    background-color: #005eff;
                    color: white;
                    padding: 0.6em 1em;
                    border-radius: 1em;
                    max-width: 60%;
                    text-align: left;
                    word-wrap: break-word;
                ">
                    {html.escape(msg.get("content") or "").replace('\n', '<br>')}
                </div>
            </div>
        """, unsafe_allow_html=True)

    elif msg["role"] == "assistant":
        msg_key = f"feedback_{msg.get('id') or id(msg)}"

        st.markdown(f"""
            <div style="display: flex; justify-content: flex-start; margin: 0.25em 0;">
                <div style="
                    background-color: #262730;
                    color: white;
                    padding: 0.6em 1em;
                    border-radius: 1em;
                    max-width: 60%;
                    text-align: left;
                    word-wrap: break-word;
                ">
                    {html.escape(msg.get("answer") or msg.get("content") or "").replace('\n', '<br>')}
                </div>
            </div>
        """, unsafe_allow_html=True)

        col1, col2, _ = st.columns([1, 1, 25])
        with col1:
            if st.button("👍", key=msg_key + "_up"):
                Utilities.set_feedback(msg["id"], "up")
                Utilities.update_feedback_in_response_evaluation(msg["id"])
                msg["feedback"] = "up"
                st.rerun()
        with col2:
            if st.button("👎", key=msg_key + "_down"):
                Utilities.set_feedback(msg["id"], "down")
                Utilities.update_feedback_in_response_evaluation(msg["id"])
                msg["feedback"] = "down"
                st.rerun()
        current_feedback = msg.get("feedback")
        if current_feedback == "up":
            st.markdown("<span style='color: green;'>👍 You liked this response.</span>", unsafe_allow_html=True)
        elif current_feedback == "down":
            st.markdown("<span style='color: red;'>👎 You disliked this response.</span>", unsafe_allow_html=True)


        if msg.get("source"):
            st.markdown(f"""
                <div style="
                    display: inline-block;
                    background-color: #fff3cd;
                    color: #856404;
                    padding: 0.3em 0.6em;
                    border-radius: 1em;
                    font-size: 0.9em;
                    margin-top: 0.3em;
                ">
                    <strong>Source:</strong> {msg['source']}
                </div>
            """, unsafe_allow_html=True)

        if msg.get("thoughts"):
            # Inject a negative margin above the expander
            st.markdown("<div style='padding-top: -0.5rem;'></div>", unsafe_allow_html=True)
            with st.expander("Reasoning Trace"):
                for thought in msg["thoughts"]:
                    st.markdown(f"- {thought}")

# ------------------- Chat Input -------------------
query = st.chat_input("Ask the Jedi Agent...")

if query and st.session_state.selected_convo:

    # Store user message in DB.
    Utilities.save_message(st.session_state.selected_convo, "user", query)
    st.session_state.chat_history.append({"role": "user", "content": query})

    try:
        response = requests.post(API_URL_ASK_JEDI_AGENT, json={
            "query": query,
            "conversation_id": st.session_state.selected_convo
        })
        if response.status_code == 200:
            data = response.json()
            st.session_state.chat_history.append({
                "id": data.get("assistant_msg_id"),
                "role": "assistant",
                "answer": data.get("answer", "No answer provided."),
                "source": data.get("source"),
                "thoughts": data.get("thoughts", []),
                "feedback": None
            })
        else:
            st.session_state.chat_history.append({
                "role": "assistant",
                "answer": "Error: Invalid response from server.",
                "source": None,
                "thoughts": []
            })
    except Exception as e:
        st.session_state.chat_history.append({
            "role": "assistant",
            "answer": f"Request failed: {str(e)}",
            "source": None,
            "thoughts": []
        })

    st.rerun()

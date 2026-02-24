import streamlit as st
import requests
import pandas as pd

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Mental Health Chatbot", page_icon="🧠", layout="wide")
st.title("🧠 Mental Health Chatbot")
st.markdown(
    "A supportive space to reflect on your emotions. Chat with the bot and see your emotional trends over time."
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "opened" not in st.session_state:
    try:
        resp = requests.get(f"{BACKEND_URL}/opening", timeout=10)
        resp.raise_for_status()
        opening = resp.json().get("bot_message", "Hello! How are you feeling today?")
    except requests.exceptions.RequestException as e:
        opening = "Hello! How are you feeling today?"
        st.warning(f"Could not connect to backend: {e}")
    st.session_state.messages.append({"role": "assistant", "content": opening})
    st.session_state.opened = True

col_chat, col_charts = st.columns([1, 1])

with col_chat:
    st.subheader("💬 Conversation")

    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("emotion_scores"):
                    scores = msg["emotion_scores"]
                    df_bar = pd.DataFrame(
                        {"Emotion": list(scores.keys()), "Score": list(scores.values())}
                    )
                    st.bar_chart(df_bar.set_index("Emotion"), height=180)

    user_input = st.chat_input("Share how you're feeling...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        history_payload = [
            {
                "role": h["role"],
                "content": h["content"],
                "dominant_emotion": max(h["emotion_scores"], key=h["emotion_scores"].get)
                if h.get("emotion_scores")
                else None,
            }
            for h in st.session_state.history
            if h.get("emotion_scores") is not None
        ]

        try:
            resp = requests.post(
                f"{BACKEND_URL}/chat",
                json={"message": user_input, "history": history_payload},
                timeout=30,
            )
            data = resp.json()
            emotion_scores = data.get("emotion_scores", {})
            bot_message = data.get("bot_message", "I'm here to listen.")
            timestamp = data.get("timestamp", "")
        except Exception as e:
            emotion_scores = {}
            bot_message = f"Sorry, I couldn't connect to the backend. Please ensure it is running. ({e})"
            timestamp = ""

        assistant_entry = {
            "role": "assistant",
            "content": bot_message,
            "emotion_scores": emotion_scores,
            "timestamp": timestamp,
        }
        st.session_state.messages.append(assistant_entry)
        st.session_state.history.append(
            {
                "role": "user",
                "content": user_input,
                "emotion_scores": emotion_scores,
                "timestamp": timestamp,
            }
        )
        st.session_state.history.append(assistant_entry)
        st.rerun()

with col_charts:
    st.subheader("📊 Emotion Analytics")

    user_turns = [
        h for h in st.session_state.history if h["role"] == "user" and h.get("emotion_scores")
    ]

    if user_turns:
        latest = user_turns[-1]
        st.markdown("**Latest Message Emotions**")
        df_latest = pd.DataFrame(
            {
                "Emotion": list(latest["emotion_scores"].keys()),
                "Score": list(latest["emotion_scores"].values()),
            }
        )
        st.bar_chart(df_latest.set_index("Emotion"), height=250)

        if len(user_turns) > 1:
            st.markdown("**Emotion Trends Over Time**")
            all_emotions = set()
            for turn in user_turns:
                all_emotions.update(turn["emotion_scores"].keys())

            trend_data = []
            for i, turn in enumerate(user_turns):
                row = {"Message": i + 1}
                for emotion in all_emotions:
                    row[emotion] = turn["emotion_scores"].get(emotion, 0)
                trend_data.append(row)

            df_trend = pd.DataFrame(trend_data).set_index("Message")
            st.line_chart(df_trend, height=300)

    st.subheader("🕒 Conversation History")
    if st.session_state.history:
        history_display = []
        for h in st.session_state.history:
            if h["role"] == "user":
                history_display.append(
                    {
                        "Timestamp": h.get("timestamp", "")[:19].replace("T", " ") if h.get("timestamp") else "",
                        "Speaker": "You",
                        "Message": h["content"],
                        "Dominant Emotion": max(h["emotion_scores"], key=h["emotion_scores"].get)
                        if h.get("emotion_scores")
                        else "",
                    }
                )
            else:
                history_display.append(
                    {
                        "Timestamp": h.get("timestamp", "")[:19].replace("T", " ") if h.get("timestamp") else "",
                        "Speaker": "Bot",
                        "Message": h["content"],
                        "Dominant Emotion": "",
                    }
                )
        df_hist = pd.DataFrame(history_display)
        st.dataframe(df_hist, use_container_width=True, hide_index=True)
    else:
        st.info("Your conversation history will appear here once you start chatting.")

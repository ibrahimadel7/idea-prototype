# Mental Health Chatbot Prototype

A lightweight mental health chatbot that classifies emotions in user messages and encourages reflective conversation.

## Features

- **Emotion classification** using [j-hartmann/emotion-english-distilroberta-base](https://huggingface.co/j-hartmann/emotion-english-distilroberta-base) (joy, sadness, anger, fear, surprise, disgust, neutral)
- **Conversational bot** that asks follow-up questions based on detected emotions
- **Emotion bar chart** shown after each user message
- **Emotion trend line chart** over the course of the conversation
- **Conversation history** table with timestamps and dominant emotions
- Messages, timestamps, and emotion scores stored in a local **SQLite** database

## Requirements

- Python 3.10+

## Setup

```bash
pip install -r requirements.txt
```

## Running the App

Open **two terminals** in the project directory.

### Terminal 1 – Start the FastAPI backend

```bash
uvicorn backend:app --host 127.0.0.1 --port 8000
```

### Terminal 2 – Start the Streamlit frontend

```bash
streamlit run frontend.py
```

Then open the URL shown by Streamlit (usually http://localhost:8501) in your browser.

## Project Structure

| File | Description |
|------|-------------|
| `backend.py` | FastAPI server – emotion classification, SQLite storage, chat logic |
| `frontend.py` | Streamlit app – chat UI, bar chart, trend chart, history table |
| `requirements.txt` | Python dependencies |
| `conversations.db` | SQLite database (auto-created on first run) |

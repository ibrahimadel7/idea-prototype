import datetime
import json
import random
import sqlite3

from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline

app = FastAPI()

emotion_classifier = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
    top_k=None,
)

DB_PATH = "conversations.db"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_message TEXT NOT NULL,
                bot_message TEXT NOT NULL,
                emotion_scores TEXT NOT NULL
            )
            """
        )
        conn.commit()


init_db()

FOLLOW_UP_QUESTIONS = {
    "joy": [
        "That's wonderful! What's bringing you joy today?",
        "It sounds like things are going well. What has been the highlight of your day?",
        "I'm glad to hear that! Is there something specific that made you happy recently?",
    ],
    "sadness": [
        "I'm sorry to hear that. Would you like to share what's been making you feel this way?",
        "It's okay to feel sad sometimes. What do you think triggered these feelings?",
        "Thank you for sharing that with me. How long have you been feeling this way?",
    ],
    "anger": [
        "I understand. What happened that made you feel angry?",
        "Anger can be really draining. Is there something specific that frustrated you?",
        "Let's explore this together. What would help you feel calmer right now?",
    ],
    "fear": [
        "It's natural to feel afraid sometimes. What's been worrying you?",
        "Fear can be overwhelming. Would you like to talk about what's causing it?",
        "I'm here with you. What feels most scary or uncertain right now?",
    ],
    "surprise": [
        "Wow, that sounds unexpected! How did that make you feel?",
        "Surprises can be a lot to process. How are you feeling about it?",
        "That must have caught you off guard. What went through your mind?",
    ],
    "disgust": [
        "I hear you. What's been bothering you so much?",
        "It sounds like something really unsettled you. Can you tell me more?",
        "That sounds really unpleasant. How are you coping with it?",
    ],
    "neutral": [
        "I see. How have you been feeling overall lately?",
        "Thanks for sharing. Is there anything on your mind you'd like to explore?",
        "I'm here to listen. What's been going on for you recently?",
    ],
}

OPENING_PROMPTS = [
    "Hello! I'm here to listen and support you. How are you feeling today?",
    "Hi there! I'm glad you're here. What's on your mind today?",
    "Welcome! I'm here to chat and help you reflect. How has your day been?",
]


class MessageRequest(BaseModel):
    message: str
    history: list[dict] = []


def get_dominant_emotion(emotion_scores: dict) -> str:
    return max(emotion_scores, key=emotion_scores.get)


def build_bot_response(emotion_scores: dict, history: list[dict]) -> str:
    dominant = get_dominant_emotion(emotion_scores)
    questions = FOLLOW_UP_QUESTIONS.get(dominant, FOLLOW_UP_QUESTIONS["neutral"])

    if not history:
        prefix = random.choice(
            [
                "Thank you for sharing that with me. ",
                "I appreciate you opening up. ",
                "I hear you. ",
            ]
        )
    else:
        last_emotions = [turn.get("dominant_emotion") for turn in history if turn.get("dominant_emotion")]
        if last_emotions and last_emotions[-1] == dominant:
            prefix = "It seems like you're still feeling " + dominant + ". "
        else:
            prefix = random.choice(
                [
                    "I notice your feelings may be shifting. ",
                    "Thank you for continuing to share. ",
                    "I'm listening. ",
                ]
            )

    follow_up = random.choice(questions)
    return prefix + follow_up


@app.get("/opening")
def opening_message():
    return {"bot_message": random.choice(OPENING_PROMPTS)}


@app.post("/chat")
def chat(request: MessageRequest):
    results = emotion_classifier(request.message)[0]
    emotion_scores = {item["label"].lower(): round(item["score"], 4) for item in results}

    bot_message = build_bot_response(emotion_scores, request.history)

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO messages (timestamp, user_message, bot_message, emotion_scores) VALUES (?, ?, ?, ?)",
            (timestamp, request.message, bot_message, json.dumps(emotion_scores)),
        )
        conn.commit()

    return {
        "emotion_scores": emotion_scores,
        "bot_message": bot_message,
        "timestamp": timestamp,
    }


@app.get("/history")
def get_history():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT timestamp, user_message, bot_message, emotion_scores FROM messages ORDER BY id ASC")
        rows = c.fetchall()
    history = []
    for row in rows:
        history.append(
            {
                "timestamp": row[0],
                "user_message": row[1],
                "bot_message": row[2],
                "emotion_scores": json.loads(row[3]),
            }
        )
    return {"history": history}

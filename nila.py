from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List
import json, atexit, os

MEM_FILE = "memory.json"

# ---- Load persistent memory ----
if os.path.exists(MEM_FILE):
    with open(MEM_FILE, "r", encoding="utf-8") as f:
        try:
            memory = json.load(f)
        except:
            memory = {}
else:
    memory = {}

def save_memory():
    with open(MEM_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

atexit.register(save_memory)

# ---- FastAPI setup ----
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    sender: str
    message: str

# ---- Helper: Greeting by time ----
def get_greeting() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "☀️ Good morning"
    elif hour < 18:
        return "🌞 Good afternoon"
    else:
        return "🌙 Good evening"

# ---- Main chat logic ----
@app.post("/chat")
def chat(msg: Message):
    sender = msg.sender
    raw = msg.message or ""
    text = raw.strip().lower()

    # Initialize memory
    if sender not in memory:
        memory[sender] = {"name": None, "topic": None}
    user_state = memory[sender]
    responses: List[Dict[str, str]] = []

    # ---- Greeting trigger ----
    if any(token in text for token in ["/greet", "hi", "hello", "hey", "salam"]):
        greeting = get_greeting()
        return [{
            "text": f"{greeting}! I’m Saleh 🎵, your Qanun teacher.\nMay I know your name? 😊"
        }]

    # ---- Ask for name if not known ----
    if user_state["name"] is None:
        name = None
        if not text:
            greeting = get_greeting()
            return [{"text": f"{greeting}! I’m Saleh 🎵, your Qanun teacher.\nMay I know your name? 😊"}]

        # Detect name
        if "my name is" in text:
            name_candidate = text.split("my name is", 1)[-1].strip()
            if name_candidate and name_candidate.split()[0].isalpha():
                name = name_candidate.split()[0].title()
        elif text.startswith(("i am ", "i'm ", "im ")):
            name_candidate = text.split(" ", 2)[-1].strip()
            if name_candidate and name_candidate.split()[0].isalpha():
                name = name_candidate.split()[0].title()
        elif len(text.split()) == 1:
            forbidden = ["facts", "history", "famous", "players", "sound", "image", "menu", "more", "hi", "hello", "hey", "salam"]
            clean_text = ''.join(c for c in text if c.isalpha())
            if clean_text and clean_text not in forbidden and len(clean_text) <= 15:
                name = clean_text.title()

        if name:
            user_state["name"] = name
            save_memory()
            return [{
                "text": (
                    f"🎶 Nice to meet you, {name}!\n"
                    "🎵 What would you like to learn today?\n"
                    "1️⃣ Facts about the Qanun\n"
                    "2️⃣ History of the Qanun\n"
                    "3️⃣ Famous Players\n"
                    "4️⃣ Qanun Sound\n"
                    "5️⃣ Qanun Images\n"
                    "(Please type one option, e.g., 'facts' or 'history')"
                )
            }]
        else:
            return [{"text": "I didn’t catch your name — could you tell me again? 😊"}]

    # ---- Menu ----
    if any(x in text for x in ["menu", "show menu", "main menu", "back to menu"]):
        responses.append({"text": "📜 Sure! Here's the menu again:"})
        responses.append({
            "text": (
                "🎶 What would you like to learn about?\n"
                "1️⃣ Facts about the Qanun\n"
                "2️⃣ History of the Qanun\n"
                "3️⃣ Famous Players\n"
                "4️⃣ Qanun Sound\n"
                "5️⃣ Qanun Images\n"
                "(Please type one option, e.g., 'facts' or 'history')"
            )
        })
        return responses

    # ---- Topics ----
    if "fact" in text:
        user_state["topic"] = "facts"
        save_memory()
        return [{"text": "🎼 The Qanun is a trapezoid-shaped string instrument with about 78 strings, producing a bright, harp-like tone."}]

    if "history" in text:
        user_state["topic"] = "history"
        save_memory()
        return [{"text": "🏺 The Qanun has ancient roots, dating back to Mesopotamia, and became a key part of Arabic and Turkish classical music."}]

    if "player" in text or "famous" in text:
        user_state["topic"] = "famous players"
        save_memory()
        return [{"text": "🎵 One of the most famous Qanun players is Mohamed Abdo Saleh, who performed with Umm Kulthum."}]

    # ---- 🎶 SOUND SECTION (UPDATED) ----
    if "sound" in text:
        user_state["topic"] = "sound"
        save_memory()
        responses = [
            {"text": "🎧 The Qanun produces a bright, zither-like sound — elegant and full of resonance."},
            {"audio": "https://example.com/qanun.mp3"},  # 👈 replace this with your real MP3 link
            {"text": "Would you like to hear another sound sample? 🎶 (Type 'more')"}
        ]
        return responses

    if any(w in text for w in ["image", "picture", "photo"]):
        user_state["topic"] = "images"
        save_memory()
        responses.append({"text": "🎨 Here's how a Qanun looks:"})
        responses.append({"image": "https://upload.wikimedia.org/wikipedia/commons/5/5a/Qanun_02.jpg"})
        return responses

    # ---- More info ----
    if any(w in text for w in ["more", "continue", "another"]):
        topic = user_state.get("topic")
        if topic == "facts":
            responses.append({"text": "📚 The Qanun’s strings are plucked using plectra attached to the fingers, allowing expressive melodies."})
        elif topic == "history":
            responses.append({"text": "🕰️ The Qanun evolved through centuries in the Middle East and remains central in Arabic orchestras."})
        elif topic == "famous players":
            responses.append({"text": "🎶 Another renowned player is Julien Jalaleddin Weiss, who mastered the instrument’s microtonal tuning."})
        elif topic == "sound":
            responses.append({"text": "🎵 Each note on the Qanun can be tuned using small levers, creating intricate scales unique to Arabic music."})
            responses.append({"audio": "https://example.com/qanun2.mp3"})  # Optional: another MP3 link
        elif topic == "images":
            responses.append({"text": "📷 Here’s another view of the Qanun:"})
            responses.append({"image": "https://upload.wikimedia.org/wikipedia/commons/8/81/Qanun_Armenian.jpg"})
        else:
            responses.append({"text": "Let's go back to the menu! 😊 Type 'menu' to choose again."})
        return responses

    # ---- Positive reactions ----
    positive_words = [
        "nice", "great", "amazing", "cool", "wow", "good", "lovely",
        "beautiful", "awesome", "fantastic", "wonderful", "ok", "okay", "alright"
    ]
    if any(w in text for w in positive_words):
        topic = user_state.get("topic")
        if topic:
            return [{"text": f"😊 I'm glad you think so! Want to know more about the {topic}? Type 'more' or 'menu'."}]
        else:
            return [{"text": "😊 I'm happy you liked it! Type 'menu' to explore more."}]

    # ---- Fallback ----
    return [{"text": "🤖 Hmm, I didn’t quite get that. Try typing 'menu' or 'more'."}]

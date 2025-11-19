from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List
import json, atexit, os
from datetime import datetime
import pytz

from pyngrok import ngrok

#
# MEM_FILE = "memory.json"
#
# # ---- Load persistent memory ----
# if os.path.exists(MEM_FILE):
#     with open(MEM_FILE, "r", encoding="utf-8") as f:
#         try:
#             memory = json.load(f)
#         except:
#             memory = {}
# else:
memory = {}

# def save_memory():
#     with open(MEM_FILE, "w", encoding="utf-8") as f:
#         json.dump(memory, f, ensure_ascii=False, indent=2)
# atexit.register(save_memory)

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

def get_greeting() -> str:
    hour = datetime.now().hour
    if 6 <= hour < 12:
        return "☀️ Good morning"
    elif 12 <= hour <= 18:
        return "🌞 Good afternoon"
    elif 18 < hour <= 23:
        return "🌙 Good evening"
    else:
        return "🌙 You’re still awake?"

# ---- Serve MP3 files directly ----
@app.get("/sound1")
def qanun_sound1():
    return FileResponse("QanunSound1.mp3")

@app.get("/sound2")
def qanun_sound2():
    return FileResponse("QanunSound2.mp3")

# ---- Serve images directly ----
@app.get("/image1")
def qanun_image1():
    return FileResponse("qanun_image1.webp")

@app.get("/image2")
def qanun_image2():
    return FileResponse("qanun_image2.jpeg")

with open("knowledge.json", "r", encoding="utf-8") as f:
    qa_pairs = json.load(f)

# ---- Chat logic ----
@app.post("/chat")
def chat(msg: Message):
    sender = msg.sender.strip().lower()
    raw = msg.message or ""
    text = raw.strip().lower()

    # Initialize memory
    if sender not in memory:
        memory[sender] = {"name": None, "topic": None}
    user_state = memory[sender]
    responses: List[Dict[str, str]] = []

    # 1. --- Initial Greeting & Name Detection (Highest Priority) ---
    if user_state["name"] is None:
        # ... (Your existing Name Detection logic: /greet, my name is X, bare name, etc.) ...

        # --- (Existing name detection logic block goes here) ---
        name = None
        words = text.split()
        greetings = ["hi", "hello", "hey", "salam", "/greet"]  # Include /greet for frontend init

        # If the input is just the bare /greet command (from frontend initialization)
        if text == "/greet":
            greeting = get_greeting()
            return [{"text": f"{greeting}! I’m Saleh 🎵, your Qanun teacher.\nMay I know your name? 😊"}]

        # Pattern 1: "my name is ..."
        if "my name is" in text:
            name_candidate = text.split("my name is", 1)[-1].strip()
            if name_candidate:
                name = name_candidate.split()[0].title()

        # Pattern 2: "I am ..." or "I'm ..." or "Im ..."
        elif text.startswith(("i am ", "i'm ", "im ")):
            name_candidate = text.split(" ", 2)[-1].strip()
            if name_candidate:
                name = name_candidate.split()[0].title()

        # Pattern 3: Greeting + Name
        else:
            for greet in greetings:
                if text.startswith(greet):
                    remainder = text[len(greet):].strip()
                    if remainder:
                        first_word = remainder.split()[0]
                        if first_word.isalpha() and first_word.lower() not in {"facts", "history", "players", "sound",
                                                                               "image", "menu"}:
                            name = first_word.title()
                    break

        # Pattern 4: Single-word name
        if not name and len(words) == 1:
            clean_text = ''.join(c for c in text if c.isalpha())
            if clean_text.lower() not in greetings and clean_text.lower() not in {"facts", "history", "players",
                                                                                  "sound", "image", "menu"}:
                name = clean_text.title()

        # ✅ If a name is detected
        if name:
            user_state["name"] = name
            # save_memory()
            return [
                {"text": f"🎶 Nice to meet you, {name}!"},
                {
                    "text": "🎵 What would you like to learn today?\n"
                            "1️⃣ Facts\n"
                            "2️⃣ History\n"
                            "3️⃣ Famous Players\n"
                            "4️⃣ Qanun Sound\n"
                            "5️⃣ Qanun Images\n"
                            " (Please type one option, e.g., 'facts' or 'history) "
            }
            ]

        # ❌ If no name found, and it wasn't the initial /greet, ask again.
        return [{"text": "I didn’t quite catch your name — could you tell me again? 😊"}]

    # quick instrument guard
    other_instruments = {"oud", "piano", "guitar", "violin", "drums"}
    if any(instr in text for instr in other_instruments):
        return [{"text": "I only have qanun info in my knowledge base — I can’t answer about other instruments here."}]

    # Check Q&A first
    for q, a in qa_pairs.items():
        if q in text:
            return [{"text": a}]

    # -------------------------------------------------------------------------
    # --- LOGIC BELOW THIS LINE RUNS ONLY IF user_state["name"] IS KNOWN ---
    # -------------------------------------------------------------------------

    # 2. --- Menu --- (Should be checked early)
    if any(x in text for x in ["menu", "show menu", "main menu", "back to menu"]):
        user_state["topic"] = None  # Clear topic after menu request
        # save_memory()
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

    # 3. --- Topic Handlers (The core functionality) ---
    if "fact" in text:
        user_state["topic"] = "facts"
        # save_memory()
        return [{
            "text": "🎼 The Qanun is a trapezoid-shaped string instrument with about 78 strings, producing a bright, harp-like tone."}]

    if "history" in text:
        user_state["topic"] = "history"
        # save_memory()
        return [{
            "text": "🏺 The Qanun has ancient roots, dating back to Mesopotamia, and became a key part of Arabic and Turkish classical music."}]

    if "player" in text or "famous" in text:
        user_state["topic"] = "famous players"
        # save_memory()
        return [
            {"text": "🎵 One of the most famous Qanun players is Mohamed Abdo Saleh, who performed with Umm Kulthum."}]

    if any(w in text for w in ["sound", "audio"]):
        user_state["topic"] = "sound"
        # save_memory()
        return [
            {"text": "🎧 The Qanun produces a bright, zither-like sound — elegant and full of resonance."},
            {"audio": "https://aphaeretic-superfantastically-mirian.ngrok-free.dev/sound1"},
        ]

    if any(w in text for w in ["image", "picture", "photo"]):
        user_state["topic"] = "images"
        # save_memory()
        return [
            {"text": "🎨 Here's how a Qanun looks:"},
            {"image": "https://aphaeretic-superfantastically-mirian.ngrok-free.dev/image1"}
        ]

    # 4. --- More info ---
    if any(w in text for w in ["more", "continue", "another","what else"]):
        # ... (Your existing 'more info' logic) ...
        topic = user_state.get("topic")
        if topic == "facts":
            responses.append({
                "text": "📚 The Qanun’s strings are plucked using plectra attached to the fingers, allowing expressive melodies."})
        elif topic == "history":
            responses.append({
                "text": "🕰️ The Qanun evolved through centuries in the Middle East and remains central in Arabic orchestras."})
        elif topic == "famous players":
            responses.append({
                "text": "🎶 Another renowned player is Julien Jalaleddin Weiss, who mastered the instrument’s microtonal tuning."})
        elif topic == "sound":
            responses.append({
                "text": "🎵 Each note on the Qanun can be tuned using small levers, creating intricate scales unique to Arabic music."})
            responses.append({"audio": "https://aphaeretic-superfantastically-mirian.ngrok-free.dev/sound2"})
        elif topic == "images":
            responses.append({"text": "📷 Here’s another view of the Qanun:"})
            responses.append({"image": "https://aphaeretic-superfantastically-mirian.ngrok-free.dev/image2"})
        else:
            responses.append({"text": "Let's go back to the menu! 😊 Type 'menu' to choose again."})
        return responses

    # 5. --- Positive reactions ---
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

    # 6. --- Greeting for Returning Users (Lowest priority before Fallback) ---
    if any(token in text for token in ["/greet", "hi", "hello", "hey", "salam"]):
        greeting = get_greeting()
        return [{
            "text": f"{greeting}, {user_state['name']}! What would you like to learn today? Type 'menu' for options. 😊"
        }]

    # 7. --- Farewell handling ---
    farewells = ["bye", "goodbye", "see you", "talk later", "farewell", "exit"]
    if any(word in text for word in farewells):
        user_state["topic"] = None
        # save_memory()
        return [
            {"text": "👋 Goodbye! It was nice teaching you the Qanun today. See you next time!"}
        ]

    # 8. --- Fallback ---
    return [{"text": "🤖 Hmm, I didn’t quite get that. Try typing 'menu' or 'more'."}]


# ---- Run the app ----
if __name__ == "__main__":
    # from pyngrok import ngrok
    # public_url = ngrok.connect(8000)
    # print("🔥 Public URL:", public_url)
    # import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8000)

    import uvicorn

    # Koyeb uses port 8080
    uvicorn.run(app, host="0.0.0.0", port=8080)

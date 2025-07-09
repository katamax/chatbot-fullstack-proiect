# backend/app.py

import os
import sys
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI, OpenAI # Comentat

# --- CORECȚIE CRITICĂ PENTRU PLAYWRIGHT PE WINDOWS ---
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Importăm logica principală a chatbot-ului și stările inițiale.
from chatbot_logic import process_chat_message, reset_chatbot_state # Comentat

load_dotenv()
# ... alte inițializări comentate dacă e cazul ...

app = FastAPI()

origins = ["http://localhost:3000", "*"] # Lasă "*" pentru siguranță în timpul testării

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ... (păstrează clasa ChatRequest)

# @app.post("/chat") # Comentează endpoint-ul de chat pentru moment
# async def chat_endpoint(request: ChatRequest):
#     pass

@app.post("/reset")
async def reset_endpoint():
    """Endpoint de test simplificat."""
    print("[TEST] Endpoint /reset a fost apelat.")
    # Nu mai apelăm nicio funcție externă, doar returnăm un JSON simplu.
    return {"message": "Hello from simplified reset!"}
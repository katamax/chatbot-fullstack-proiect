# backend/app.py

import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI, OpenAI

# Importăm logica refactorizată
from chatbot_logic import process_chat_message, reset_chatbot_state

load_dotenv()
print(f"DEBUG: OPENAI_API_KEY este {'setată' if os.getenv('OPENAI_API_KEY') else 'NU este setată'} la startup.")

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("Variabila de mediu OPENAI_API_KEY nu este setată. Asigură-te că fișierul .env există sau este setată în mediul de rulare.")

openai_client_async = AsyncOpenAI(api_key=openai_api_key)
openai_client_sync = OpenAI(api_key=openai_api_key)

app = FastAPI(
    title="Chatbot Colectare Date & Automatizare",
    description="Un chatbot inteligent care colectează date și automatizează completarea formularelor.",
    version="1.1.0"
)


# ADAUGĂ ACEST BLOC PENTRU TESTARE
@app.get("/")
def health_check():
    return {"status": "ok", "message": "Backend is running!"}

# Configurăm CORS pentru a permite cereri de la orice origine.
origins = [
    "http://localhost:3000",                  # Pentru testare locală
    "https://chatbot-fullstack.netlify.app"   # Pentru aplicația live
]
# În producție, poți restricționa la domeniul frontend-ului tău.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    user_message: str
    current_conversation_state: dict

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        response_data = await process_chat_message(
            request.user_message,
            request.current_conversation_state,
            openai_client_async,
            openai_client_sync
        )
        return response_data
    except Exception as e:
        print(f"Eroare neașteptată în endpoint-ul /chat: {e}")
        raise HTTPException(status_code=500, detail=f"Eroare internă a serverului: {e}")

@app.post("/reset")
async def reset_endpoint():
    initial_state = reset_chatbot_state()
    return {
        "assistant_message": initial_state["conversation_history"][0]["content"],
        "new_conversation_state": initial_state,
        "status_message": "Sesiune nouă. Introduceți informațiile companiei...",
        "is_automation_running": False,
        "final_response": None
    }
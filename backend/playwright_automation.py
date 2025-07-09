# backend/playwright_automation.py

import time
import base64
import traceback
from multiprocessing import Queue
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from openai import OpenAI
import json

# --- Funcții Ajutătoare ---
def get_screen_dimensions():
    """Determină dimensiuni standard pentru ecranul virtual."""
    return 1920, 1080

def get_screenshot(page_or_frame):
    """Realizează o captură de ecran a contextului curent."""
    return page_or_frame.screenshot()

# --- FUNCȚIA DE GESTIONARE A ACȚIUNILOR, CU CORECȚIE PENTRU "ENTER" ---
def handle_model_action(page, action):
    """Execută o acțiune trimisă de modelul AI pe pagina curentă."""
    action_type = getattr(action, "type", "unknown_action_type")
    print(f"  -> Execut acțiunea AI: {action_type}")
    try:
        if action_type == "click":
            page.mouse.click(action.x, action.y, button=getattr(action, "button", "left"))
        elif action_type == "scroll":
            page.mouse.move(action.x, action.y)
            page.evaluate(f"window.scrollBy({action.scroll_x}, {action.scroll_y})")
        elif action_type == "type":
            page.keyboard.type(action.text)
        elif action_type == "keypress":
            keys = getattr(action, 'keys', [])
            for k in keys:
                # --- CORECȚIA CRITICĂ AICI ---
                # Normalizăm numele tastei: transformăm "ENTER" în "Enter".
                # .capitalize() face prima literă mare și restul mici.
                key_to_press = k.capitalize()
                print(f"  -> Apăsare tastă (normalizată): '{key_to_press}'")
                page.keyboard.press(key_to_press)
                # -----------------------------
        elif action_type == "wait":
            time.sleep(getattr(action, "time_seconds", 2))
        else:
            print(f"  -> Acțiune AI nerecunoscută: {action_type}")
        return page
    except Exception as e:
        print(f"  -> EROARE la execuția acțiunii AI '{action_type}': {e}")
        raise

# --- Bucla Principală de Automatizare ---
def computer_use_loop(page, initial_response, tools, openai_client: OpenAI) -> str:
    response = initial_response
    while True:
        computer_calls = [item for item in getattr(response, "output", []) if hasattr(item, "type") and item.type == "computer_call"]
        if not computer_calls:
            return response.output_text.strip() or "Automatizare finalizată."
        action = computer_calls[0].action
        try:
            page = handle_model_action(page, action)
            time.sleep(2)
        except Exception as e:
            return f"Eroare în timpul executării acțiunii: {e}"
        screenshot_bytes = get_screenshot(page)
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")
        try:
            input_dict = {"type": "computer_call_output", "call_id": computer_calls[0].call_id, "output": {"type": "input_image", "image_url": f"data:image/png;base64,{screenshot_base64}"}}
            response = openai_client.responses.create(model="computer-use-preview", previous_response_id=getattr(response, "id", None), tools=tools, input=[input_dict], truncation="auto") # type: ignore
        except Exception as e:
            return f"Eroare API în buclă: {e}"

# --- Funcția cu Logica de Automatizare (cu promptul tău) ---
def _perform_automation(collected_data: dict, openai_client: OpenAI) -> str:
    print("\n" + "="*60)
    print(">>> EXECUT VERSIUNEA 'FULL AI' CU PROMPT-UL TĂU COMPLET <<<")
    print("="*60 + "\n")
    
    denumire_firma = collected_data.get("nume companie", "")
    servicii = collected_data.get("servicii selected", [])
    categorie = collected_data.get("categorie", "")
    idei_client = "Informatii colectate via chatbot."

    # --- PROMPT-UL TĂU COMPLET ȘI DIRECTIV ---
    input_messages = [
        {
            "role": "user",
            "content": f"""Acceseaza https://podio.com/webforms/25990350/1948325. Folosindu-te de actiunile corespunzatoare
             de tipul click(x,y), type(text), scroll etc.:
            1. Identifica campul input text aflat dupa stringul 'Denumire client *' si introdu {denumire_firma}
            2. La câmpul 'Regiune (sediu)': dă un singur click pentru a-l activa, tastează 'Vest' direct, și imediat după aceea apasă tasta 'Enter' pentru a finaliza selecția. Nu mai cere confirmare.
            3. Identifica chackbox-urile aflate dupa 'Interesat de serviciile *' si bifeaza optiunile din {servicii}
            4. La campul 'Categoria întreprinderii *': da un singur click pentru a-l activa, scrii {categorie}, si imediat dupa aceea apasa tasta 'Enter pentru a finaliza selectia. Nu mai cere confirmarea si treci la pasul urmator.
            5. Identifica campul de input aflat dupa 'Ideile clientului - etapa SALES *' si introdu textul {idei_client} si treci la pasul urmator.
            6. Click pe butonul 'Trimite'
            """
        }
    ]
    
    w, h = get_screen_dimensions()
    tools = [{"type": "computer_use_preview", "display_width": w, "display_height": h, "environment": "browser"}]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
            page = browser.new_page()
            page.set_viewport_size({"width": w, "height": h})
            page.goto("https://podio.com/webforms/25990350/1948325", wait_until="networkidle", timeout=30000)
            print("Pagina pare să fie încărcată complet.")
            
            initial_response = openai_client.responses.create(
                model="computer-use-preview",
                input=json.dumps(input_messages),
                tools=tools,           # type: ignore
                truncation="auto"
            )
            print("Răspuns inițial de la AI primit. Se intră în bucla de automatizare...")

            automation_result = computer_use_loop(page, initial_response, tools, openai_client)
            browser.close()
            return automation_result
    except Exception as e:
        print(f"Eroare majoră în _perform_automation: {traceback.format_exc()}"); return f"Eroare critică la rularea automatizării: {e}"

# --- Funcția Wrapper pentru `multiprocessing` (neschimbată) ---
def run_automation_process_wrapper(queue: Queue, collected_data: dict, openai_api_key: str):
    try:
        print("[Process Wrapper] Procesul de automatizare a pornit.")
        openai_client = OpenAI(api_key=openai_api_key)
        result = _perform_automation(collected_data, openai_client)
        queue.put(result)
        print("[Process Wrapper] Rezultatul a fost pus în coadă.")
    except Exception as e:
        error_message = f"Eroare critică în procesul wrapper: {e}"
        print(f"[Process Wrapper] {error_message}"); traceback.print_exc()
        queue.put(error_message)
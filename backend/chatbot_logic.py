# backend/chatbot_logic.py

import json, os
from typing import Any, Dict
from openai import OpenAI, AsyncOpenAI
from anyio import to_thread
from multiprocessing import Process, Queue, freeze_support
from playwright_automation import run_automation_process_wrapper
from llm_utils import llm_extract_services, llm_match_category

def _run_automation_in_process(collected_data: dict, openai_api_key: str) -> str:
    freeze_support()
    result_queue = Queue()
    automation_process = Process(target=run_automation_process_wrapper, args=(result_queue, collected_data, openai_api_key)) # type: ignore
    automation_process.start()
    print("[Orchestrator] Procesul a pornit. Se așteaptă rezultatul...")
    result = result_queue.get() 
    print("[Orchestrator] Rezultat primit din coadă.")
    automation_process.join()
    print("[Orchestrator] Procesul s-a încheiat.")
    return result

INITIAL_STATE_VALUE = { "collected_data": { "nume companie": None, "servicii selected": [], "categorie": None }, "conversation_history": [], "status": "initial", "automation_result_message": None, "asked_for_confirmation": False }

def reset_chatbot_state() -> Dict[str, Any]:
    initial_history_message = ( "Salut! Sunt aici să te ajut să înregistrezi informații despre compania ta. " "Te rog să-mi spui, în discuție liberă, următoarele detalii: " "**numele companiei**, **categoria firmei** (Micro, Mica, Mijlocie, Mare, APL) " "și **serviciile** de care ești interesat. " "Voi încerca să extrag aceste date din conversația noastră." )
    return { "collected_data": { "nume companie": None, "servicii selected": [], "categorie": None }, "conversation_history": [{"role": "assistant", "content": initial_history_message}], "status": "collecting", "automation_result_message": None, "asked_for_confirmation": False }

async def process_chat_message(user_message: str, current_state: Dict[str, Any], openai_client_async: AsyncOpenAI, openai_client_sync: OpenAI) -> Dict[str, Any]:
    new_state = current_state.copy()
    new_state["collected_data"] = current_state["collected_data"].copy()
    new_state["conversation_history"] = list(current_state["conversation_history"])
    new_state["conversation_history"].append({"role": "user", "content": user_message})

    assistant_message, status_message, final_response = "", "Procesez...", None
    is_automation_running = False

    if new_state["status"] in ["completed", "error"]:
        assistant_message = "Sesiunea este finalizată. Apasă 'Șterge & Reîncepe'."
        new_state["conversation_history"].append({"role": "assistant", "content": assistant_message})
        return {"assistant_message": assistant_message, "new_conversation_state": new_state, "status_message": status_message, "is_automation_running": is_automation_running, "final_response": final_response}
    
    user_intends_to_finish = False

    try:
        extraction_schema = { "type": "object", "properties": { "nume_companie": {"type": ["string", "null"]}, "categorie_firma": {"type": ["string", "null"]}, "servicii_dorite": {"type": "array", "items": {"type": "string"}}, "intentie_finalizare": {"type": "boolean"} }, "required": ["nume_companie", "categorie_firma", "servicii_dorite", "intentie_finalizare"], "additionalProperties": False }
        extraction_instructions = ("Ești un asistent inteligent care extrage informații cheie...")
        extraction_response = await to_thread.run_sync( lambda: openai_client_sync.responses.create( model="gpt-4o-mini", instructions=extraction_instructions, input=new_state["conversation_history"][-6:], text={"format": {"type": "json_schema", "name": "data_extractor", "schema": extraction_schema, "strict": True}}, temperature=0.2 ) )
        extracted_data_raw = json.loads(extraction_response.output_text)
        if extracted_data_raw.get("nume_companie"): new_state["collected_data"]["nume companie"] = extracted_data_raw["nume_companie"].strip()
        if extracted_data_raw.get("categorie_firma"):
            canonical_category = await to_thread.run_sync(llm_match_category, extracted_data_raw["categorie_firma"], openai_client_sync)
            if canonical_category: new_state["collected_data"]["categorie"] = canonical_category
        if extracted_data_raw.get("servicii_dorite"):
            services_string = ", ".join(extracted_data_raw["servicii_dorite"])
            if services_string:
                canonical_services = await to_thread.run_sync(llm_extract_services, services_string, openai_client_sync)
                for service in canonical_services:
                    if service not in new_state["collected_data"]["servicii selected"]: new_state["collected_data"]["servicii selected"].append(service)
        user_intends_to_finish = extracted_data_raw.get("intentie_finalizare", False)
    except Exception as e:
        print(f"Eroare extracție: {e}"); assistant_message = "Am întâmpinat o problemă internă."; new_state["status"] = "error"
        new_state["conversation_history"].append({"role": "assistant", "content": assistant_message})
        return {"assistant_message": assistant_message, "new_conversation_state": new_state, "status_message": "Eroare internă", "is_automation_running": False, "final_response": None}

    missing_info = [k for k, v in new_state["collected_data"].items() if not v or (isinstance(v, list) and not v)]

    if not missing_info:
        if new_state["status"] == "collecting":
            nume_companie, servicii_selectate, categorie = new_state['collected_data'].get('nume companie', 'N/A'), new_state['collected_data'].get('servicii selected', []), new_state['collected_data'].get('categorie', 'N/A')
            servicii_text = ', '.join(servicii_selectate) if servicii_selectate else 'N/A'
            friendly_summary = (f"**Date colectate:**\n- Nume companie: **{nume_companie}**\n- Servicii: **{servicii_text}**\n- Categorie: **{categorie}**")
            assistant_message = f"{friendly_summary}\n\nDoriți să trimit datele acum? Răspunde doar cu 'yes' sau 'no'."
            new_state["status"] = "ready_to_confirm"
        elif new_state["status"] == "ready_to_confirm":
            confirmation_response = await to_thread.run_sync(lambda: openai_client_sync.responses.create(model="gpt-4.1", instructions="Răspunde doar cu 'yes' sau 'no'.", input=[{"role": "user", "content": user_message}], temperature=0.0))
            if "yes" in confirmation_response.output_text.strip().lower() or user_intends_to_finish:
                new_state["status"] = "automation_running"; assistant_message = "Perfect! Inițiez completarea automată a formularului."; status_message = "Se trimit datele..."; is_automation_running = True
                openai_api_key = os.getenv("OPENAI_API_KEY")
                if not openai_api_key: automation_result_message = "Eroare: Cheia API nu este disponibilă."
                else: automation_result_message = await to_thread.run_sync(_run_automation_in_process, new_state["collected_data"], openai_api_key)
                new_state["automation_result_message"] = automation_result_message; new_state["status"] = "completed"; final_response = automation_result_message
                assistant_message += f"\n\nAutomatizare finalizată: {automation_result_message}"; status_message = "Automatizare finalizată."
            else: assistant_message = "În regulă, ce doriți să corectați?"; new_state["status"] = "collecting"
    else:
        assistant_message = f"Mai am nevoie de: **{', '.join(missing_info)}**."; new_state["status"] = "collecting"

    new_state["conversation_history"].append({"role": "assistant", "content": assistant_message})
    return {"assistant_message": assistant_message, "new_conversation_state": new_state, "status_message": status_message, "is_automation_running": is_automation_running, "final_response": final_response}
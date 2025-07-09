# backend/chatbot_logic.py

import json
import asyncio
from typing import Dict, Any
from openai import OpenAI, AsyncOpenAI
from anyio import to_thread

from llm_utils import llm_extract_services, llm_match_category
from playwright_automation import run_playwright_automation  # Acum async!

INITIAL_STATE_VALUE = {
    "collected_data": {
        "nume companie": None,
        "servicii selected": [],
        "categorie": None
    },
    "conversation_history": [],
    "status": "initial",
    "automation_result_message": None,
    "asked_for_confirmation": False
}

def reset_chatbot_state() -> Dict[str, Any]:
    initial_history_message = (
        "Salut! Sunt aici să te ajut să înregistrezi informații despre compania ta. "
        "Te rog să-mi spui, în discuție liberă, următoarele detalii: "
        "**numele companiei**, **categoria firmei** (Micro, Mica, Mijlocie, Mare, APL) "
        "și **serviciile** de care ești interesat. "
        "Voi încerca să extrag aceste date din conversația noastră. "
        "Poți începe oricum dorești, de exemplu: "
        "'Am o companie mică care activează în domeniul construcțiilor și se numește Alfa SRL, "
        "și mă interesează dezvoltare RPA.' "
        "Când ai terminat de oferit toate informațiile, te rog să-mi spui, de exemplu, 'Gata, e tot!'."
    )
    return {
        "collected_data": {
            "nume companie": None,
            "servicii selected": [],
            "categorie": None
        },
        "conversation_history": [{"role": "assistant", "content": initial_history_message}],
        "status": "collecting",
        "automation_result_message": None,
        "asked_for_confirmation": False
    }

async def process_chat_message(
    user_message: str,
    current_state: Dict[str, Any],
    openai_client_async: AsyncOpenAI,
    openai_client_sync: OpenAI
) -> Dict[str, Any]:
    new_state = current_state.copy()
    new_state["collected_data"] = current_state["collected_data"].copy()
    new_state["conversation_history"] = current_state["conversation_history"].copy()
    new_state["conversation_history"].append({"role": "user", "content": user_message})

    assistant_message = ""
    status_message = "Procesez mesajul..."
    is_automation_running = False
    final_response = None

    if new_state["status"] in ["completed", "error"]:
        assistant_message = "Sesiunea este finalizată. Te rog apasă 'Șterge & Reîncepe' pentru o nouă sesiune."
        new_state["conversation_history"].append({"role": "assistant", "content": assistant_message})
        return {
            "assistant_message": assistant_message,
            "new_conversation_state": new_state,
            "status_message": status_message,
            "is_automation_running": is_automation_running,
            "final_response": final_response
        }

    extraction_schema = {
        "type": "object",
        "properties": {
            "nume_companie": {"type": ["string", "null"], "description": "Numele complet al companiei menționate."},
            "categorie_firma": {"type": ["string", "null"], "description": "Categoria firmei menționată de utilizator (ex: 'mică', 'mijlocie', 'apl')."},
            "servicii_dorite": {"type": "array", "items": {"type": "string"}, "description": "O listă a serviciilor menționate de utilizator."},
            "intentie_finalizare": {"type": "boolean", "description": "True dacă utilizatorul indică explicit că a terminat de oferit informații."}
        },
        "required": ["nume_companie", "categorie_firma", "servicii_dorite", "intentie_finalizare"],
        "additionalProperties": False
    }

    try:
        history_for_llm = new_state["conversation_history"][-6:]

        extraction_instructions = (
            "Ești un asistent inteligent care extrage informații cheie dintr-o conversație. "
            "Analizează conversația și completează formularul JSON conform schemei furnizate. "
            "Pentru `intentie_finalizare`, setează `true` doar dacă utilizatorul spune clar că a terminat (ex: 'gata', 'asta e tot', 'terminat', 'nu mai am nimic de adăugat'). "
            "Dacă o informație nu este prezentă, folosește `null` sau o listă goală `[]`."
        )

        print("[Chatbot Logic] Apel LLM principal pentru extracție de date (responses.create)...")

        extraction_response = await to_thread.run_sync(
            lambda: openai_client_sync.responses.create(
                model="gpt-4o-mini",
                instructions=extraction_instructions,
                input=history_for_llm,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "data_extractor_schema",
                        "description": "Schema pentru extragerea datelor despre companie.",
                        "schema": extraction_schema,
                        "strict": True
                    }
                },
                temperature=0.2
            )
        )
        extracted_data_raw = json.loads(extraction_response.output_text)
        print(f"[Chatbot Logic] Date brute extrase de LLM: {extracted_data_raw}")

        # Canonicalizăm și completăm datele
        if extracted_data_raw.get("nume_companie"):
            new_state["collected_data"]["nume companie"] = extracted_data_raw["nume_companie"].strip()
        if extracted_data_raw.get("categorie_firma"):
            canonical_category = await to_thread.run_sync(
                llm_match_category, extracted_data_raw["categorie_firma"], openai_client_sync
            )
            if canonical_category:
                new_state["collected_data"]["categorie"] = canonical_category
                print(f"[Chatbot Logic] Categorie canonicalizată: {canonical_category}")
        if extracted_data_raw.get("servicii_dorite"):
            services_string = ", ".join(extracted_data_raw["servicii_dorite"])
            if services_string:
                canonical_services = await to_thread.run_sync(
                    llm_extract_services, services_string, openai_client_sync
                )
                for service in canonical_services:
                    if service not in new_state["collected_data"]["servicii selected"]:
                        new_state["collected_data"]["servicii selected"].append(service)
                print(f"[Chatbot Logic] Servicii canonicalizate: {new_state['collected_data']['servicii selected']}")
        user_intends_to_finish = extracted_data_raw.get("intentie_finalizare", False)
        print(f"[Chatbot Logic] Intenție finalizare detectată: {user_intends_to_finish}")

    except Exception as e:
        print(f"[Chatbot Logic] Eroare în timpul extracției de date: {e}")
        assistant_message = "Am întâmpinat o problemă internă în timpul procesării mesajului tău. Vă rog, încercați din nou mai târziu."
        new_state["status"] = "error"
        new_state["conversation_history"].append({"role": "assistant", "content": assistant_message})
        return {
            "assistant_message": assistant_message,
            "new_conversation_state": new_state,
            "status_message": "Eroare internă",
            "is_automation_running": False,
            "final_response": None
        }

    missing_info = []
    if not new_state["collected_data"]["nume companie"]:
        missing_info.append("numele companiei")
    if not new_state["collected_data"]["servicii selected"]:
        missing_info.append("serviciile dorite")
    if not new_state["collected_data"]["categorie"]:
        missing_info.append("categoria firmei")
    print(f"[Chatbot Logic] Informații lipsă: {missing_info}")

    # --- Generare respondere, inclusiv declanșare RPA ---
    if not missing_info:
        if new_state["status"] == "collecting":
            friendly_data_summary = (
                "**Date colectate:**\n"
                f"- Nume companie: {new_state['collected_data'].get('nume companie') or 'N/A'}\n"
                f"- Servicii: {', '.join(new_state['collected_data'].get('servicii selected', [])) or 'N/A'}\n"
                f"- Categorie: {new_state['collected_data'].get('categorie') or 'N/A'}"
            )
            assistant_message = (
                f"{friendly_data_summary}\n\n"
                "Am colectat toate informațiile necesare. Doriți să trimit datele acum "
                "sau mai aveți de adăugat/corectat ceva?"
            )
            new_state["status"] = "ready_to_confirm"
            new_state["asked_for_confirmation"] = True
            status_message = "Aștept confirmarea dvs."
        elif new_state["status"] == "ready_to_confirm":
            confirmation_instructions = "Ești un asistent care determină dacă utilizatorul confirmă o acțiune. Răspunde doar cu 'yes' sau 'no'."
            print("[Chatbot Logic] Apel LLM pentru confirmare (responses.create)...")
            confirmation_response = await to_thread.run_sync(
                lambda: openai_client_sync.responses.create(
                    model="gpt-4o-mini",
                    instructions=confirmation_instructions,
                    input=[{"role": "user", "content": user_message}],
                    temperature=0.0,
                    max_output_tokens=100
                )
            )
            confirmation_intent = confirmation_response.output_text.strip().lower()
            print(f"[Chatbot Logic] Intenție confirmare clasificată: {confirmation_intent}")

            if "yes" in confirmation_intent or user_intends_to_finish:
                new_state["status"] = "automation_running"
                assistant_message = "Perfect! Inițiez completarea automată a formularului online (browserul se va deschide automat în fundal)."
                status_message = "Se trimit datele în Podio... Vă rog să așteptați."
                is_automation_running = True
                new_state["asked_for_confirmation"] = False

                print("[Chatbot Logic] Declanșez run_playwright_automation...")
                # !!! Apel direct await la funcția ASYNC !!!
                automation_result_message = await run_playwright_automation(
                    new_state["collected_data"], openai_client_sync
                )

                new_state["automation_result_message"] = automation_result_message
                new_state["status"] = "completed"
                final_response = automation_result_message

                assistant_message += f"\n\nAutomatizare finalizată: {automation_result_message}\n" \
                                    "Sesiunea a fost încheiată. Doriți să începem o nouă sesiune? Apăsați 'Șterge & Reîncepe' sau spuneți 'Începe din nou'."
                status_message = "Automatizare finalizată. Sesiune încheiată."
            else:
                assistant_message = "În regulă, ce ați dori să adăugați sau să corectați?"
                new_state["status"] = "collecting"
                new_state["asked_for_confirmation"] = False
                status_message = "Aștept detalii suplimentare."
    else:
        current_collected_summary = []
        if new_state["collected_data"]["nume companie"]:
            current_collected_summary.append(f"numele companiei ({new_state['collected_data']['nume companie']})")
        if new_state["collected_data"]["servicii selected"]:
            current_collected_summary.append(f"serviciile ({', '.join(new_state['collected_data']['servicii selected'])})")
        if new_state["collected_data"]["categorie"]:
            current_collected_summary.append(f"categoria firmei ({new_state['collected_data']['categorie']})")
        if current_collected_summary:
            assistant_message += f"Am înțeles: {'; '.join(current_collected_summary)}.\n"
        assistant_message += f"Pentru a finaliza, mai am nevoie de **{', '.join(missing_info)}**."
        status_message = "Vă rog să-mi furnizați informațiile lipsă."
        new_state["status"] = "collecting"
        new_state["asked_for_confirmation"] = False

    new_state["conversation_history"].append({"role": "assistant", "content": assistant_message})

    return {
        "assistant_message": assistant_message,
        "new_conversation_state": new_state,
        "status_message": status_message,
        "is_automation_running": is_automation_running,
        "final_response": final_response
    }
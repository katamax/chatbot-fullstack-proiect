# backend/llm_utils.py

import os
# Acum vom folosi clientul SINCRON OpenAI aici, pentru că apelăm `responses.create`
# care, din specificația ta, este disponibil pe clientul sincron.
from openai import OpenAI # <--- MODIFICAT: Importăm clientul Sincron

# Opțiunile valide și predefinite pentru servicii și categorii.
SERVICE_OPTIONS = [
    "Dezvoltare RPA",
    "Roboti pusi pe treaba",
    "Consultanta Digitalizare",
    "RoboCRM - Podio"
]
CATEGORY_OPTIONS = [
    "Micro",
    "Mica",
    "Mijlocie",
    "Mare",
    "APL"
]

# <--- ATENȚIE: Aceste funcții NU MAI SUNT async def, ci SINCRONE,
# pentru că apelează client.responses.create care e sincron.
# Ele vor fi rulate în to_thread.run_sync din chatbot_logic.py.

def llm_extract_services(user_text_segment: str, openai_client: OpenAI) -> list[str]: # <--- MODIFICAT: Sincron, și client: OpenAI
    """
    Extrage și canonicalizează serviciile menționate de utilizator dintr-un segment de text liber.
    Folosește modelul OpenAI `responses.create` pentru a potrivi textul liber cu opțiunile predefinite.
    :param user_text_segment: Segmentul de text al utilizatorului de analizat.
    :param openai_client: Instanța clientului OpenAI (sincron).
    :returns: O listă de stringuri canonicale ale serviciilor identificate.
    """
    opt_str = "\n".join(SERVICE_OPTIONS)

    # Instrucțiuni pentru modelul `responses.create`
    instructions = f"""Ești un asistent care extrage servicii dintr-un text liber și le canonicalizează conform unei liste date.
Lista de opțiuni corecte este:\n{opt_str}\n\n
Returnează exact elementul (stringul complet) din listă care se potrivește cel mai bine cu textul din input, chiar dacă inputul e abreviat, parțial sau greșit.
Dacă sunt mai multe servicii, returnează fiecare opțiune găsită pe o linie separată, exact cum apare în lista de opțiuni.
Dacă nu se menționează nicio opțiune validă, scrie doar 'None'."""

    try:
        # Apelăm modelul OpenAI folosind `responses.create`.
        # `input` așteaptă o listă de mesaje, nu un string direct, conform noului API.
        response = openai_client.responses.create(
            model="gpt-4o-mini", # Sau modelul tău preferat pentru acest task
            instructions=instructions,
            input=[{"role": "user", "content": user_text_segment}], # <--- MODIFICAT: Format input
            temperature=0.1,
            max_output_tokens=100 # Folosim max_output_tokens pentru responses.create
        )
        text = response.output_text.strip() # Accesează răspunsul prin .output_text
        if text.lower() == "none" or not text:
            return []
        
        matches = []
        for line in text.splitlines():
            opt = line.strip()
            if opt in SERVICE_OPTIONS:
                matches.append(opt)
        return list(set(matches))
    except Exception as e:
        print(f"LLM service match failed: {e}")
        return []

# <--- ATENȚIE: Această funcție NU MAI ESTE async def, ci SINCRONĂ.
def llm_match_category(user_text_segment: str, openai_client: OpenAI) -> str | None: # <--- MODIFICAT: Sincron, și client: OpenAI
    """
    Extrage și canonicalizează categoria firmei menționată de utilizator.
    Folosește modelul OpenAI `responses.create`.
    :param user_text_segment: Segmentul de text al utilizatorului de analizat.
    :param openai_client: Instanța clientului OpenAI (sincron).
    :returns: Stringul canonic al categoriei identificate, sau None dacă nu s-a putut determina.
    """
    opt_str = "\n".join(CATEGORY_OPTIONS)

    instructions = f"""Ești un asistent care extrage categoria unei firme dintr-un text liber și o canonicalizează conform unei liste date.
Lista de categorii valide este:\n{opt_str}\n\n
Care dintre categorii corespunde CEL MAI BINE răspunsului?
Returnează exact elementul (stringul complet) din listă care se potrivește cel mai bine cu textul din input, chiar dacă inputul e abreviat, parțial sau greșit.
Nu adauga nimic în plus, doar categoria exactă din listă.
Dacă nu se poate determina nicio categorie, scrie exact 'None'."""

    try:
        # Apelăm modelul OpenAI folosind `responses.create`.
        response = openai_client.responses.create(
            model="gpt-4o-mini",
            instructions=instructions,
            input=[{"role": "user", "content": user_text_segment}], # <--- MODIFICAT: Format input
            temperature=0.1,
            max_output_tokens=20 # Folosim max_output_tokens
        )
        result = response.output_text.strip() # Accesează răspunsul prin .output_text
        if result in CATEGORY_OPTIONS:
            return result
        else:
            return None
    except Exception as e:
        print(f"LLM category match fail: {e}")
        return None
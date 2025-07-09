# backend/llm_utils.py

from openai import OpenAI

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

def llm_extract_services(user_text_segment: str, openai_client: OpenAI) -> list[str]:
    """
    Extrage serviciile menționate dintr-un text și le canonicalizează conform listei definite.
    """
    opt_str = "\n".join(SERVICE_OPTIONS)
    instructions = f"""Ești un asistent care extrage servicii dintr-un text liber și le canonicalizează conform unei liste date.
Lista de opțiuni corecte este:\n{opt_str}\n\n
Returnează exact elementul (stringul complet) din listă care se potrivește cel mai bine cu textul din input, chiar dacă inputul e abreviat, parțial sau greșit.
Dacă sunt mai multe servicii, returnează fiecare opțiune găsită pe o linie separată.
Dacă nu se menționează nicio opțiune validă, scrie doar 'None'."""

    try:
        response = openai_client.responses.create(
            model="gpt-4o-mini",
            instructions=instructions,
            input=[{"role": "user", "content": user_text_segment}],
            temperature=0.1,
            max_output_tokens=100
        )
        text = response.output_text.strip()
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

def llm_match_category(user_text_segment: str, openai_client: OpenAI) -> str | None:
    """
    Extrage și canonicalizează categoria firmei menționată de utilizator.
    """
    opt_str = "\n".join(CATEGORY_OPTIONS)
    instructions = f"""Ești un asistent care extrage categoria unei firme dintr-un text liber și o canonicalizează conform unei liste date.
Lista de categorii valide este:\n{opt_str}\n\n
Care dintre categorii corespunde CEL MAI BINE răspunsului?
Returnează exact elementul (stringul complet) din listă.
Dacă nu se poate determina nicio categorie, scrie exact 'None'."""

    try:
        response = openai_client.responses.create(
            model="gpt-4o-mini",
            instructions=instructions,
            input=[{"role": "user", "content": user_text_segment}],
            temperature=0.1,
            max_output_tokens=20
        )
        result = response.output_text.strip()
        if result in CATEGORY_OPTIONS:
            return result
        else:
            return None
    except Exception as e:
        print(f"LLM category match fail: {e}")
        return None
# backend/playwright_automation.py

import base64
import traceback
import asyncio
from playwright.async_api import async_playwright, Page, Error as PlaywrightError
from openai import OpenAI

def get_screen_dimensions():
    return 1920, 1080

async def get_screenshot(page: Page) -> bytes:
    return await page.screenshot()

async def handle_model_action(browser_page: Page, action):
    action_type = getattr(action, "type", "unknown_action_type")
    print(f"  -> Execut acțiunea: {action_type}")
    try:
        if action_type == "click":
            await browser_page.mouse.click(action.x, action.y, button=getattr(action, "button", "left"))
        elif action_type == "scroll":
            await browser_page.mouse.move(action.x, action.y)
            await browser_page.evaluate(f"window.scrollBy({action.scroll_x}, {action.scroll_y})")
        elif action_type == "keypress":
            for k in action.keys:
                await browser_page.keyboard.press(k)
        elif action_type == "type":
            await browser_page.keyboard.type(action.text)
        elif action_type == "wait":
            await asyncio.sleep(getattr(action, "time_seconds", 2))
        else:
            print(f"  -> Acțiune nerecunoscută: {action_type}. Detalii: {action}")
        return browser_page
    except Exception as e:
        print(f"  -> EROARE la execuția acțiunii Playwright '{action_type}': {e}")
        raise

# Buclă principală
async def computer_use_loop(browser_page: Page, initial_response, tools, openai_client: OpenAI) -> str:
    response = initial_response

    while True:
        computer_calls = [
            item for item in getattr(response, "output", [])
            if hasattr(item, "type") and item.type == "computer_call"
        ]

        if not computer_calls:
            result_message = response.output_text.strip()
            if not result_message:
                result_message = "Automatizare finalizată cu succes (fără mesaj specific)."
            print(f"[Computer Use Loop] Automatizare finalizată. Mesaj: {result_message}")
            return result_message

        computer_call = computer_calls[0]
        last_call_id = computer_call.call_id
        action = computer_call.action

        try:
            browser_page = await handle_model_action(browser_page, action)
            await asyncio.sleep(1)
        except Exception as e:
            error_message = f"Eroare în timpul executării acțiunii '{getattr(action, 'type', 'unknown')}': {e}"
            print(f"[Computer Use Loop] {error_message}")
            return error_message

        screenshot_bytes = await get_screenshot(browser_page)
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")

        try:
            input_data = {
                "type": "computer_call_output",
                "call_id": last_call_id,
                "output": {
                    "type": "input_image",
                    "image_url": f"data:image/png;base64,{screenshot_base64}"
                }
            }
            # acest call e tot sincronic pe OpenAI!
            response = openai_client.responses.create(
                model="computer-use-preview",
                previous_response_id=getattr(response, "id", None),
                tools=tools,
                input=input_data, # type: ignore
                truncation="auto"
            )
        except Exception as e:
            error_message = f"Eroare la apelul computer-use-preview API: {e}"
            print(f"[Computer Use Loop] {error_message}")
            return error_message

# Funcția principală asincronă!!
async def run_playwright_automation(collected_data: dict, openai_client: OpenAI) -> str:
    print(f"[Playwright Automation] Inițiez automatizarea cu datele: {collected_data}")

    denumire_firma = collected_data.get("nume companie", "")
    servicii = collected_data.get("servicii selected", [])
    categorie = collected_data.get("categorie", "")
    idei_client = "Informatii colectate via chatbot (LLM-driven automation)."

    prompt_content = (
        f"Completează formularul de pe pagina curentă cu următoarele date: "
        f"Denumire client: '{denumire_firma}', "
        f"Regiune sediu: 'Centru', "
        f"Servicii de interes: selectează {', '.join(servicii)}, "
        f"Categoria intreprinderii: selectează '{categorie}', "
        f"Idei client: '{idei_client}'. "
        "La final, apasă butonul de trimitere."
    )

    w, h = get_screen_dimensions()
    tools = [{
        "type": "computer_use_preview",
        "display_width": w,
        "display_height": h,
        "environment": "browser"
    }]

    if not openai_client:
        return "Eroare critică: Clientul OpenAI nu a fost furnizat."

    try:
        async with async_playwright() as p:
            print("[Playwright] Context manager 'async_playwright' a fost inițiat cu succes.")
            try:
                browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
                print("[Playwright] Browser Chromium lansat cu succes.")
            except Exception as launch_error:
                print("="*50)
                print("[Playwright] EROARE CRITICĂ LA LANSAREA BROWSER-ULUI!")
                traceback.print_exc()
                print("="*50)
                return f"Eroare la pornirea browser-ului. Detalii: {launch_error}"

            page = await browser.new_page()
            await page.set_viewport_size({"width": w, "height": h})
            await page.goto("https://podio.com/webforms/25990350/1948325", wait_until="domcontentloaded")
            await asyncio.sleep(2)

            # openai_client.responses.create este încă sincronic!
            initial_response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: openai_client.responses.create(
                    model="computer-use-preview",
                    input=prompt_content,
                    tools=tools, # type: ignore
                    truncation="auto"
                )
            )
            print("[Playwright Automation] Răspuns inițial de la computer-use-preview primit.")

            automation_result = await computer_use_loop(page, initial_response, tools, openai_client)

            await browser.close()
            print(f"[Playwright Automation] Browser închis. Rezultat final: {automation_result}")
            return automation_result

    except PlaywrightError as e:
        print("="*50)
        print("Eroare majoră Playwright în run_playwright_automation:")
        traceback.print_exc()
        print("="*50)
        return f"Eroare Playwright la rularea automatizării: {e}"
    except Exception as e:
        print("="*50)
        print("Eroare majoră în run_playwright_automation:")
        traceback.print_exc()
        print("="*50)
        return f"Eroare critică la rularea automatizării: {e}"
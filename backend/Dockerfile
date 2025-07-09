# Dockerfile pentru Backend - Optimizat pentru Google Cloud Run și Dezvoltare Locală

# Pasul 1: Imaginea de bază
FROM python:3.10-slim

# Pasul 2: Setăm directorul de lucru
WORKDIR /app

# Pasul 3: Copiem fișierul de dependențe
COPY requirements.txt .

# Pasul 4: Instalăm dependențele Python
RUN pip install --no-cache-dir -r requirements.txt

# Pasul 5: Instalăm Playwright și browser-ul cu dependințele de sistem
# --with-deps este crucial pentru mediile Linux headless precum cele din Cloud Run
RUN playwright install --with-deps chromium

# Pasul 6: Copiem codul sursă al aplicației
COPY . .

# Pasul 7: Setăm o valoare IMPLICITĂ pentru variabila de mediu PORT.
# Aceasta va fi folosită dacă rulăm local și nu o specificăm.
# Pe Cloud Run, această valoare va fi SUPRASCRISĂ automat (de obicei cu 8080).
ENV PORT 8080

# Pasul 8: Expunem portul. Acesta este un pas documentar.
# Nu este obligatoriu, dar este o practică bună să arăți ce port intenționezi să folosești.
EXPOSE 8080

# Pasul 9: Comanda de pornire a containerului.
# ACEASTA ESTE PARTEA CRITICĂ PENTRU CLOUD RUN.
# Folosim `sh -c` pentru a permite shell-ului să substituie variabila de mediu `${PORT}`.
# Astfel, Uvicorn va porni pe portul dictat de Cloud Run (sau pe cel implicit, 8080, dacă rulăm local).
CMD exec sh -c "uvicorn app:app --host 0.0.0.0 --port ${PORT}"
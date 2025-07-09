// frontend/src/InputBar.js

import React from 'react';
import './App.css'; // Importă stilurile CSS pentru input bar

/**
 * Componenta InputBar oferă câmpul de text pentru introducerea mesajelor și butoane de acțiune.
 * @param {object} props - Proprietățile componentei.
 * @param {string} props.currentInput - Valoarea curentă a textului din câmpul de input.
 * @param {function} props.onInputChange - Funcție apelată la modificarea textului din input.
 * @param {function} props.onSendMessage - Funcție apelată la trimiterea mesajului (click pe buton sau Enter).
 * @param {function} props.onResetChat - Funcție apelată la resetarea chat-ului.
 * @param {boolean} props.isLoading - Indică dacă o operație de încărcare este în curs (ex: așteptarea răspunsului de la backend).
 * @param {boolean} props.isAutomationRunning - Indică dacă automatizarea Playwright rulează pe backend.
 */
const InputBar = ({ currentInput, onInputChange, onSendMessage, onResetChat, isLoading, isAutomationRunning }) => {
  // `isDisabled` controlează dacă inputul și butonul de trimitere sunt dezactivate.
  // Se dezactivează când se încarcă sau când automatizarea rulează.
  const isDisabled = isLoading || isAutomationRunning;

  // Funcție pentru a gestiona apăsarea tastelor în câmpul de text.
  // Permite trimiterea mesajului la apăsarea Enter (fără Shift+Enter).
  const handleKeyPress = (e) => {
    // Verifică dacă tasta apăsată este 'Enter' și dacă tasta 'Shift' NU este apăsată.
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // Previne comportamentul implicit (nouă linie în textarea)
      if (currentInput.trim() !== '' && !isDisabled) {
        onSendMessage(); // Apelez funcția de trimitere mesaj
      }
    }
  };

  return (
    <div className="input-bar">
      <textarea
        value={currentInput} // Textul controlat de starea `currentInput` din App.js
        onChange={onInputChange} // Funcția apelată la fiecare modificare
        onKeyPress={handleKeyPress} // Funcția pentru gestionarea apăsării tastelor
        placeholder={isDisabled ? "Așteptați..." : "Introduceți mesajul aici..."} // Text placeholder
        rows="3" // Înălțimea inițială a câmpului de text
        disabled={isDisabled} // Dezactivează inputul dacă `isDisabled` este true
      />
      <div className="input-buttons">
        {/* Butonul "Trimite" este dezactivat dacă se încarcă, rulează automatizarea
            sau dacă inputul este gol (doar spații albe). */}
        <button onClick={onSendMessage} disabled={isDisabled || currentInput.trim() === ''}>
          Trimite
        </button>
        {/* Butonul "Șterge & Reîncepe" este dezactivat doar dacă se încarcă. */}
        <button onClick={onResetChat} disabled={isLoading}>
          Șterge & Reîncepe
        </button>
      </div>
    </div>
  );
};

export default InputBar;
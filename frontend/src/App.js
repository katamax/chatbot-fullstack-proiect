// frontend/src/App.js

import React, { useState, useEffect } from 'react';
import ChatWindow from './ChatWindow';    // Componenta pentru afișarea mesajelor
import InputBar from './InputBar';        // Componenta pentru inputul utilizatorului
import StatusBar from './StatusBar';      // Componenta pentru mesajele de status
import { sendMessage, resetChat } from './api'; // Funcțiile pentru interacțiunea cu backend-ul
import './App.css';                       // Fișierul CSS principal pentru stilizare

function App() {
  // Starea pentru istoricul mesajelor afișate în interfața utilizatorului.
  // Fiecare obiect mesaj are un `role` ('user' sau 'assistant') și `content` (textul mesajului).
  const [messages, setMessages] = useState([]);

  // Starea pentru textul curent din câmpul de input al utilizatorului.
  const [currentInput, setCurrentInput] = useState('');

  // Starea conversației. Aceasta este o oglindă a stării gestionate de backend.
  // O trimitem la backend și o actualizăm cu răspunsul de la backend pentru a menține contextul.
  const [conversationState, setConversationState] = useState({
    collected_data: { "nume companie": null, "servicii selected": [], "categorie": null },
    conversation_history: [], // Va fi populat la inițializare cu primul mesaj al asistentului
    status: "initial",
    automation_result_message: null,
    asked_for_confirmation: false
  });

  // Mesajul de status afișat deasupra câmpului de input (ex: "Procesez..." sau "Aștept informații").
  const [statusMessage, setStatusMessage] = useState("Încărcare chatbot...");

  // Flag boolean pentru a indica dacă o cerere către backend este în curs.
  // Când este `true`, inputul utilizatorului este dezactivat.
  const [isLoading, setIsLoading] = useState(false);

  // Flag boolean pentru a indica dacă automatizarea Playwright rulează pe backend.
  // Când este `true`, inputul utilizatorului este dezactivat.
  const [isAutomationRunning, setIsAutomationRunning] = useState(false);

  // Hook `useEffect` pentru a inițializa conversația la prima încărcare a componentei.
  // Se rulează o singură dată (datorită array-ului de dependențe gol `[]`).
  useEffect(() => {
    const initializeChat = async () => {
      setIsLoading(true); // Activează starea de încărcare
      try {
        // Apelez `resetChat` pentru a obține starea inițială și primul mesaj de la backend.
        const initialResponse = await resetChat();
        setConversationState(initialResponse.new_conversation_state);
        // Setăm mesajele inițiale (doar mesajul asistentului din `conversation_history`).
        setMessages(initialResponse.new_conversation_state.conversation_history);
        setStatusMessage(initialResponse.status_message);
      } catch (error) {
        console.error("Eroare la inițializarea chat-ului:", error);
        setMessages([{ role: 'assistant', content: 'Eroare la încărcarea chatbot-ului. Vă rugăm să reîncărcați pagina.' }]);
        setStatusMessage("Eroare de inițializare.");
      } finally {
        setIsLoading(false); // Dezactivează starea de încărcare indiferent de rezultat
      }
    };
    initializeChat();
  }, []);

  /**
   * Handler pentru modificarea textului din câmpul de input.
   * Actualizează starea `currentInput` pe măsură ce utilizatorul tastează.
   */
  const handleInputChange = (e) => {
    setCurrentInput(e.target.value);
  };

  /**
   * Handler pentru trimiterea mesajului utilizatorului către backend.
   * Este apelat la click pe butonul "Trimite" sau la apăsarea tastei Enter.
   */
  const handleSendMessage = async () => {
    const userMessage = currentInput.trim(); // Elimină spațiile albe de la început/sfârșit
    if (!userMessage) return; // Nu trimite mesaje goale

    setIsLoading(true); // Activează starea de încărcare (blochează inputul)
    setCurrentInput(''); // Golește câmpul de input imediat după trimitere

    // Adaugă mesajul utilizatorului la istoricul afișat în UI.
    setMessages((prevMessages) => [...prevMessages, { role: 'user', content: userMessage }]);

    try {
      // Apelez funcția `sendMessage` din `api.js` pentru a comunica cu backend-ul.
      // Trimitem mesajul utilizatorului și starea curentă a conversației pentru context.
      const response = await sendMessage(userMessage, conversationState);
      
      // Actualizează starea conversației locală cu noua stare primită de la backend.
      setConversationState(response.new_conversation_state);
      
      // Adaugă răspunsul asistentului la istoricul afișat în UI.
      setMessages((prevMessages) => [...prevMessages, { role: 'assistant', content: response.assistant_message }]);
      
      // Actualizează mesajul de status.
      setStatusMessage(response.status_message);
      
      // Setează flag-ul pentru automatizare, care va bloca inputul dacă automatizarea rulează.
      setIsAutomationRunning(response.is_automation_running);

      // Dacă automatizarea s-a terminat și există un mesaj final, îl afișăm.
      // În implementarea actuală, mesajul final este inclus în assistant_message.
      // if (response.new_conversation_state.status === "completed" && response.final_response) {
      //   setMessages((prevMessages) => [...prevMessages, { role: 'assistant', content: `Automatizare Podio: ${response.final_response}` }]);
      // }

    } catch (error) {
      console.error("Eroare la trimiterea mesajului către backend:", error);
      // Afișează un mesaj de eroare în chat dacă apelul API eșuează.
      setMessages((prevMessages) => [...prevMessages, { role: 'assistant', content: `Ne pare rău, a apărut o eroare de comunicare: ${error.message}. Vă rog să încercați din nou.` }]);
      setStatusMessage("Eroare de comunicare. Vă rog să încercați din nou.");
    } finally {
      setIsLoading(false); // Dezactivează starea de încărcare, permițând din nou inputul
    }
  };

  /**
   * Handler pentru resetarea întregii sesiuni de chat.
   * Apelat la click pe butonul "Șterge & Reîncepe".
   */
  const handleResetChat = async () => {
    setIsLoading(true); // Activează starea de încărcare
    try {
      // Apelez funcția `resetChat` din `api.js` pentru a reseta starea la backend.
      const response = await resetChat();
      // Resetăm toate stările locale la valorile inițiale sau la cele primite de la backend.
      setConversationState(response.new_conversation_state);
      setMessages(response.new_conversation_state.conversation_history); // Doar mesajul inițial al asistentului
      setStatusMessage(response.status_message);
      setCurrentInput(''); // Golește inputul
      setIsAutomationRunning(false); // Asigură că flag-ul de automatizare este resetat
    } catch (error) {
      console.error("Eroare la resetarea chat-ului:", error);
      setMessages([{ role: 'assistant', content: 'Eroare la resetarea chat-ului. Vă rugăm să reîncărcați pagina.' }]);
      setStatusMessage("Eroare la resetare.");
    } finally {
      setIsLoading(false); // Dezactivează starea de încărcare
    }
  };

  return (
    <div className="App">
      <div className="chat-container">
        <h1>Asistent Colectare Date</h1>
        {/* Componenta pentru afișarea mesajelor */}
        <ChatWindow messages={messages} />
        {/* Componenta pentru afișarea mesajului de status */}
        <StatusBar message={statusMessage} />
        {/* Componenta pentru inputul utilizatorului și butoane */}
        <InputBar
          currentInput={currentInput}
          onInputChange={handleInputChange}
          onSendMessage={handleSendMessage}
          onResetChat={handleResetChat}
          isLoading={isLoading}
          isAutomationRunning={isAutomationRunning}
        />
      </div>
    </div>
  );
}

export default App;
// frontend/src/ChatWindow.js

import React, { useRef, useEffect } from 'react';
import Message from './Message'; // Importă componenta pentru a afișa un singur mesaj
import './App.css'; // Importă stilurile CSS necesare pentru aspect

/**
 * Componenta ChatWindow afișează o listă de mesaje în interfața de chat.
 * Asigură scroll automat la cel mai recent mesaj.
 * @param {object} props - Proprietățile componentei.
 * @param {Array<object>} props.messages - O listă de obiecte mesaj ({ role: 'user' | 'assistant', content: string }).
 */
const ChatWindow = ({ messages }) => {
  // `useRef` este utilizat pentru a crea o referință la un element DOM.
  // Aici, o vom folosi pentru a "marca" sfârșitul listei de mesaje, permițând scroll-ul automat.
  const messagesEndRef = useRef(null);

  // `useEffect` este un hook React care rulează un efect secundar după fiecare randare.
  // Aici, este folosit pentru a derula la cel mai recent mesaj ori de câte ori
  // lista de `messages` se actualizează.
  useEffect(() => {
    // `scrollIntoView` derulează elementul în vizualizare.
    // `behavior: "smooth"` face scroll-ul animat.
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]); // Acest efect se va rula doar când `messages` se modifică.

  return (
    <div className="chat-window">
      {/* Mapează fiecare obiect mesaj la o componentă <Message /> */}
      {messages.map((msg, index) => (
        // `key` este o proprietate obligatorie pentru listele de componente în React,
        // ajută React să identifice elementele în mod eficient.
        <Message key={index} role={msg.role} content={msg.content} />
      ))}
      {/* Acest div invizibil servește drept ancora pentru scroll-ul automat */}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default ChatWindow;
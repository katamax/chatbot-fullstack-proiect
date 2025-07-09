// frontend/src/Message.js

import React from 'react';
import './App.css'; // Importă stilurile CSS pentru aspectul bulelor de mesaj

/**
 * Componenta Message afișează o singură bulă de chat.
 * Stilează mesajul în funcție de rol (user sau assistant).
 * Permite redarea conținutului HTML (pentru text bold/italic etc.) folosind dangerouslySetInnerHTML.
 * @param {object} props - Proprietățile componentei.
 * @param {'user' | 'assistant'} props.role - Rolul expeditorului mesajului.
 * @param {string} props.content - Conținutul text al mesajului (poate conține HTML).
 */
const Message = ({ role, content }) => {
  // Determină clasa CSS bazată pe rolul mesajului.
  const messageClass = role === 'user' ? 'user-message' : 'assistant-message';

  return (
    // Div-ul principal al bulei de mesaj, cu clase CSS pentru stilizare.
    <div className={`message-bubble ${messageClass}`}>
      {/* dangerouslySetInnerHTML este folosit pentru a injecta HTML direct în DOM.
          Atenție: Folosește-l doar cu conținut de încredere, deoarece poate introduce vulnerabilități XSS
          dacă conținutul provine direct de la utilizator fără sanitarizare.
          În acest caz, conținutul asistentului este de încredere. */}
      <div dangerouslySetInnerHTML={{ __html: content }} />
    </div>
  );
};

export default Message;
// frontend/src/StatusBar.js

import React from 'react';
import './App.css'; // Importă stilurile CSS pentru status bar

/**
 * Componenta StatusBar afișează un mesaj de status sub fereastra de chat.
 * @param {object} props - Proprietățile componentei.
 * @param {string} props.message - Mesajul de status de afișat.
 */
const StatusBar = ({ message }) => {
  return (
    <div className="status-bar">
      <p>{message}</p>
    </div>
  );
};

export default StatusBar;
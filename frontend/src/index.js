// frontend/src/index.js

import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css'; // Importă stiluri CSS globale (dacă există)
import App from './App'; // Importă componenta principală a aplicației
import reportWebVitals from './reportWebVitals'; // Pentru măsurarea performanței (opțional)

// Creează o "rădăcină" React pentru aplicație. Aceasta este noua API React 18.
const root = ReactDOM.createRoot(document.getElementById('root'));

// Randează componenta <App /> în elementul HTML cu id-ul 'root'.
// <React.StrictMode> ajută la detectarea problemelor potențiale în aplicație în timpul dezvoltării.
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Funcție pentru a trimite metrici de performanță (ex: la Google Analytics).
// Poți elimina acest apel dacă nu ai nevoie de el.
reportWebVitals();
// frontend/src/api.js

const API_BASE_URL = 'https://chatbot-backend-service-916511052664.europe-west1.run.app';
// const API_BASE_URL = 'http://localhost:5000';

export const sendMessage = async (userMessage, currentConversationState) => {
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_message: userMessage,
                current_conversation_state: currentConversationState
            }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`HTTP error! Status: ${response.status}, Detail: ${errorData.detail || 'Unknown error'}`);
        }

        return response.json();
    } catch (error) {
        console.error("Eroare la trimiterea mesajului către backend:", error);
        throw error;
    }
};

export const resetChat = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/reset`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`HTTP error! Status: ${response.status}, Detail: ${errorData.detail || 'Unknown error'}`);
        }

        return response.json();
    } catch (error) {
        console.error("Eroare la resetarea chat-ului:", error);
        throw error;
    }
};
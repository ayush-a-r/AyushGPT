// --- DOM ELEMENTS ---
const loginScreen = document.getElementById('login-screen');
const chatApp = document.getElementById('chat-app');
const emailInput = document.getElementById('email-input');
const passwordInput = document.getElementById('password-input');
const loginBtn = document.getElementById('login-btn');
const registerBtn = document.getElementById('register-btn');
const logoutBtn = document.getElementById('logout-btn');

const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

const API_BASE_URL = 'https://ayush-gpt.onrender.com';
let jwtToken = null;

// --- INITIALIZATION ---
window.onload = () => {
    const savedToken = localStorage.getItem('ayushgpt_token');
    if (savedToken) {
        jwtToken = savedToken;
        loadChatHistory(); 
    }
};

// --- AUTHENTICATION ---
registerBtn.addEventListener('click', async () => {
    const email = emailInput.value.trim();
    const password = passwordInput.value.trim();
    if (!email || !password) return alert("Enter email and password!");

    try {
        const res = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        alert(data.message || data.detail);
    } catch (err) {
        alert("Server connection failed.");
    }
});

loginBtn.addEventListener('click', async () => {
    const email = emailInput.value.trim();
    const password = passwordInput.value.trim();
    if (!email || !password) return alert("Enter email and password!");

    try {
        const res = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();

        if (res.ok) {
            localStorage.setItem('ayushgpt_token', data.token);
            jwtToken = data.token;
            loadChatHistory();
        } else {
            alert(data.detail || "Login failed");
        }
    } catch (err) {
        alert("Ensure FastAPI server is running!");
    }
});

logoutBtn.addEventListener('click', () => {
    localStorage.removeItem('ayushgpt_token');
    jwtToken = null;
    chatApp.classList.add('hidden');
    loginScreen.classList.remove('hidden');
    chatBox.innerHTML = ''; 
});

// --- CHAT & MEMORY LOGIC ---
const typingIndicator = document.createElement('div');
typingIndicator.className = 'message ai-message typing-indicator';
typingIndicator.innerHTML = '<div class="message-content">Ayush is typing...</div>';

function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = text.replace(/\n/g, '<br>');
    messageDiv.appendChild(contentDiv);
    
    chatBox.insertBefore(messageDiv, typingIndicator);
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function loadChatHistory() {
    try {
        const res = await fetch(`${API_BASE_URL}/chat/history`, {
            headers: { 'Authorization': `Bearer ${jwtToken}` }
        });
        const data = await res.json();

        if (res.ok) {
            chatBox.innerHTML = ''; 
            chatBox.appendChild(typingIndicator); 

            if (data.history && data.history.length > 0) {
                data.history.forEach(msg => {
                    const sender = msg.type === 'human' ? 'user' : 'ai';
                    addMessage(msg.data.content, sender);
                });
            } else {
                addMessage("Hi, I am Ayush's AI Twin! How can I help you?", "ai");
            }

            loginScreen.classList.add('hidden');
            chatApp.classList.remove('hidden');
        } else {
            logoutBtn.click();
        }
    } catch (err) {
        console.error("Failed to fetch history:", err);
    }
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    addMessage(text, 'user');
    userInput.value = '';
    typingIndicator.style.display = 'flex';
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${jwtToken}`
            },
            body: JSON.stringify({ message: text })
        });

        const data = await response.json();
        typingIndicator.style.display = 'none';
        
        // Fixed: The backend returns 'data.reply', not 'data.status'
        if (response.ok && data.reply) {
            addMessage(data.reply, 'ai');
        } else {
            addMessage("❌ Error: " + (data.detail || "Something went wrong"), 'ai');
        }
    } catch (error) {
        typingIndicator.style.display = 'none';
        addMessage("❌ Connection error! Is your Python server running?", 'ai');
    }
}

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});
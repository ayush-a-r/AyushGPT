# 🤖 AyushGPT: Personalized AI Twin Backend

A highly personalized AI backend that replicates my personality, communication style, and memories using **Retrieval-Augmented Generation (RAG)**. Built with **FastAPI**, **LangChain**, **MongoDB Atlas Vector Search**, and **Google Gemini**, AyushGPT delivers natural conversations while maintaining long-term context through vector memory and persistent chat history.

---

## ✨ Features

### 🧠 Personality Cloning
- Replicates my communication style using:
  - Custom system prompt
  - JSON personality profile
  - Hinglish conversational tone
  - Personal memories and preferences

### 🔍 Retrieval-Augmented Generation (RAG)
- Uses **MongoDB Atlas Vector Search**
- Retrieves the most relevant memories before generating responses
- Makes conversations context-aware instead of relying only on the LLM

### 💬 Persistent Memory
- Stores complete user chat history
- Maintains conversation continuity across sessions
- Saves messages in MongoDB

### 🔐 JWT Authentication
- Secure user registration and login
- Token-based authentication
- User-specific chat history and memories

### ⚡ Fast & Asynchronous
- Built completely using **FastAPI**
- Async API endpoints
- Low latency responses

### 📚 Vector Embeddings
- Uses **HuggingFace all-MiniLM-L6-v2**
- Generates 384-dimensional embeddings
- Cosine similarity search

---

# 🏗️ Architecture

```
                   User
                     │
                     ▼
             FastAPI REST API
                     │
      ┌──────────────┼──────────────┐
      ▼                             ▼
JWT Authentication          Chat History
      │                     (MongoDB)
      │
      ▼
 LangChain RAG Pipeline
      │
      ▼
MongoDB Atlas Vector Search
      │
      ▼
Relevant Personal Memories
      │
      ▼
Google Gemini 1.5 Flash
      │
      ▼
Personalized Response
```

---

# 🛠 Tech Stack

| Category | Technology |
|----------|------------|
| Backend | FastAPI |
| Language | Python |
| LLM Framework | LangChain |
| LLM | Google Gemini 1.5 Flash |
| Embeddings | HuggingFace all-MiniLM-L6-v2 |
| Vector Database | MongoDB Atlas Vector Search |
| Database | MongoDB Atlas |
| Authentication | JWT |
| Deployment | Render / Railway |

---


# ⚙️ Prerequisites

Before running the project, make sure you have:

- Python 3.8+
- MongoDB Atlas Account
- MongoDB Vector Search Index
- Google Gemini API Key

---

# 🚀 Installation

## 1. Clone Repository

```bash
git clone https://github.com/ayush-a-r/ayushgpt-ai-service.git

cd ayushgpt-ai-service
```

---

## 2. Create Virtual Environment

### Windows

```bash
python -m venv venv

venv\Scripts\activate
```

### Mac/Linux

```bash
python3 -m venv venv

source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Create Environment Variables

Create a `.env` file in the root directory.

```env
MONGO_URI=your_mongodb_connection_string

GOOGLE_API_KEY=your_google_api_key

JWT_SECRET=your_secret_key
```

---

## 5. Start FastAPI Server

```bash
uvicorn main:app --reload
```

The API will be available at

```
http://127.0.0.1:8000
```

Swagger Documentation

```
http://127.0.0.1:8000/docs
```

ReDoc Documentation

```
http://127.0.0.1:8000/redoc
```

---

# 📡 API Endpoints

## Authentication

### Register User

```
POST /register
```

Creates a new user.

Example Request

```json
{
    "name":"Ayush",
    "email":"abc@gmail.com",
    "password":"123456"
}
```

---

### Login

```
POST /login
```

Returns JWT Token.

Example

```json
{
    "email":"abc@gmail.com",
    "password":"123456"
}
```

Response

```json
{
    "access_token":"jwt_token",
    "token_type":"bearer"
}
```

---

## AI Chat

### Generate Response

```
POST /chat
```

Headers

```
Authorization: Bearer <JWT_TOKEN>
```

Request

```json
{
    "message":"Tell me about your internship."
}
```

Flow

```
User Message
      │
      ▼
Generate Embedding
      │
      ▼
Vector Search
      │
Retrieve Relevant Memories
      │
      ▼
LangChain Retrieval Chain
      │
      ▼
Gemini
      │
      ▼
Response
```

---

### Chat History

```
GET /chat/history
```

Returns complete conversation history of authenticated user.

---

### Health Check

```
GET /health
```

Checks

- Database connection
- Gemini API
- Server status

---

# 🧠 RAG Pipeline

The backend follows a Retrieval-Augmented Generation architecture.

```
User Question
       │
       ▼
Generate Embedding
       │
       ▼
MongoDB Vector Search
       │
Top Relevant Memories
       │
       ▼
Prompt Builder
       │
       ▼
Gemini 1.5 Flash
       │
       ▼
Final Personalized Response
```

---

# 🗂 MongoDB Vector Search Configuration

Collection

```
vectors
```

Index Name

```
vector_index
```

Embedding Model

```
all-MiniLM-L6-v2
```

Dimensions

```
384
```

Similarity Metric

```
cosine
```

---

# 🔐 Authentication Flow

```
Register
      │
      ▼
Password Hashing
      │
      ▼
MongoDB
      │
      ▼
Login
      │
      ▼
JWT Token
      │
      ▼
Protected Routes
```

---

# 📦 Main Dependencies

```txt
fastapi

uvicorn

langchain

langchain-community

langchain-google-genai

sentence-transformers

pymongo

motor

python-dotenv

python-jose

passlib

bcrypt

pydantic
```

---

# 🌟 Future Improvements

- Voice cloning
- Speech-to-Speech conversation
- Image understanding
- Long-term memory summarization
- Multi-agent architecture
- Function calling
- Emotion detection
- Streaming responses
- WebSocket support
- Redis caching
- Tool calling
- Calendar integration
- WhatsApp integration

---

# 📄 License

This project is intended for educational and portfolio purposes.

---

# 👨‍💻 Author

**Ayush Ranjan**

If you found this project interesting, feel free to ⭐ the repository.

---

## ⭐ Built With

- FastAPI
- LangChain
- MongoDB Atlas
- Google Gemini
- HuggingFace Embeddings
- JWT Authentication
- Python
import os
import json
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

# LangChain and Database Integrations
from pymongo import MongoClient
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

# Load environment variables from .env 
load_dotenv()

# --- Configuration ---
MONGO_URI = os.getenv("MONGO_URI")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

if not all([MONGO_URI, GOOGLE_API_KEY, SECRET_KEY]):
    raise ValueError("Missing critical environment variables.")

# --- FastAPI Initialization ---
app = FastAPI(title="AI Twin Backend")

# Create a list of allowed frontend URLs
origins = [
    "https://your-custom-url.netlify.app" # TODO: Update this with your live Netlify URL later
]
# CORS Configuration (Allows frontend to communicate with backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Security & Manual User Management ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception

# --- Database & AI Setup ---
# 1. Connect to MongoDB Atlas
client = MongoClient(MONGO_URI)
vector_collection = client.ayushgpt_db.vectors

# 2. Setup Embeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 3. Initialize MongoDB Vector Search
vector_store = MongoDBAtlasVectorSearch(
    collection=vector_collection,
    embedding=embeddings,
    index_name="vector_index"
)
retriever = vector_store.as_retriever(search_kwargs={"k": 3})

# 4. Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", 
    google_api_key=GOOGLE_API_KEY,
    temperature=0.7
)

# 5. Load Style Profile
STYLE_PROFILE = ""
style_path = os.path.join("data", "processed", "ayush_style_profile.json")

try:
    with open(style_path, "r", encoding="utf-8") as f:
        STYLE_PROFILE = json.dumps(json.load(f), indent=2)
except FileNotFoundError:
    print(f"⚠️ Warning: {style_path} not found.")

# --- Pydantic Data Models ---
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

# --- API Endpoints ---
@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Manual user management (Update with your specific admin credentials)
    if form_data.username != "ayush" or form_data.password != "password123": 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, current_user: str = Depends(verify_token)):
    user_message = request.message
    
    # Retrieve memories mathematically matched to the user's question
    retrieved_docs = retriever.invoke(user_message)
    context_text = "\n\n".join([doc.page_content for doc in retrieved_docs])
    
    # Construct the RAG prompt
    prompt_template = """
    You are an AI clone of the user. Use the provided personality style and memory context to respond to the message.
    
    Style Profile:
    {style}
    
    Memory Context:
    {context}
    
    User Message: {question}
    
    Respond strictly in the first person ("I"), adopting the tone and knowledge from the style profile and context. Do not mention that you are an AI or reading from a profile.
    """
    
    prompt = PromptTemplate.from_template(prompt_template)
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "style": STYLE_PROFILE,
            "context": context_text,
            "question": user_message
        })
        return ChatResponse(reply=response.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok", "database": "connected", "ai": "ready"}
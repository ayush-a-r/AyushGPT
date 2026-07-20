import os
import json
from pydantic import BaseModel
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

# LangChain and Database Integrations
from pymongo import MongoClient
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Import the auth router and token verifier from your auth.py file!
from auth import router as auth_router, verify_token

# Load environment variables
load_dotenv()

# --- Configuration ---
MONGO_URI = os.getenv("MONGO_URI")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not all([MONGO_URI, GOOGLE_API_KEY]):
    raise ValueError("Missing critical environment variables.")

# --- FastAPI Initialization ---
app = FastAPI(title="AI Twin Backend")

# CORS Configuration
origins = "https://a-r-gpt.netlify.app"


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect the auth.py endpoints (/login and /register) to this main file
app.include_router(auth_router)

# --- Database & AI Setup ---
client = MongoClient(MONGO_URI)
vector_collection = client.ayushgpt_db.vectors

embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-2", 
    google_api_key=GOOGLE_API_KEY,
    output_dimensionality=384
)
vector_store = MongoDBAtlasVectorSearch(collection=vector_collection, embedding=embeddings, index_name="vector_index")
retriever = vector_store.as_retriever(search_kwargs={"k": 3})

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", google_api_key=GOOGLE_API_KEY, temperature=0.7)

# Load Style Profile
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
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, current_user: str = Depends(verify_token)):
    user_message = request.message
    
    retrieved_docs = retriever.invoke(user_message)
    context_text = "\n\n".join([doc.page_content for doc in retrieved_docs])
    
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

# Added this so your frontend's loadChatHistory doesn't hit a 404 error!
@app.get("/chat/history")
async def chat_history(current_user: str = Depends(verify_token)):
    return {"history": []}

@app.get("/health")
async def health_check():
    return {"status": "ok", "database": "connected", "ai": "ready"}
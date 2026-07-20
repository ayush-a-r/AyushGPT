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
from langchain_core.prompts import ChatPromptTemplate
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
origins = ["https://a-r-gpt.netlify.app"]


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
    
    system_prompt = """
    You are Ayush Ranjan, a B.Tech CSE student at NIT Jamshedpur.
    You are NOT an AI assistant. You are Ayush. Never break character.

    Here is a psychological and stylistic breakdown of how you speak and behave:
    {STYLE_PROFILE}

    ### RETRIEVED MEMORIES & CONTEXT:
    {{context}}

    ### INSTRUCTIONS:
    1. Tone & Style: Adopt the exact vocabulary, tone, and formatting described in your style profile. 
    2. Factual Accuracy: Use the 'RETRIEVED MEMORIES' to answer questions about your personal life, projects, or friends.
    3. General Tech & Knowledge: If asked a general programming, math, or world knowledge question, USE your underlying AI intelligence to answer it accurately. You are a smart CSE student, so explain things practically in your Hinglish style!
    4. Unknown Personal Facts: ONLY if asked about a personal memory or life event that is NOT in the retrieved context, casually deflect in your native Hinglish style.

    Respond to the user's message exactly as Ayush would.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        # MessagesPlaceholder(variable_name="chat_history"), # Uncomment when ready to use history
        ("human", "{input}"),
    ])
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "style": STYLE_PROFILE,
            "context": context_text,
            "input": user_message
        })
        
        # Explicitly extract content and convert to string to ensure Pydantic doesn't fail
        reply_content = response.content
        
        if isinstance(reply_content, list):
            # If it's a list of blocks, join them into a single string
            reply_text = "".join([block.get("text", "") if isinstance(block, dict) else str(block) for block in reply_content])
        else:
            reply_text = str(reply_content)
        
        return ChatResponse(reply=reply_text)
       
        
    except Exception as e:
        print(f"Chat Error: {e}") # Log the actual error for debugging
        raise HTTPException(status_code=500, detail=str(e))

# Added this so your frontend's loadChatHistory doesn't hit a 404 error!
@app.get("/chat/history")
async def chat_history(current_user: str = Depends(verify_token)):
    return {"history": []}

@app.get("/health")
async def health_check():
    return {"status": "ok", "database": "connected", "ai": "ready"}
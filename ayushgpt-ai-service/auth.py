from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
import time
import os
import motor.motor_asyncio
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# --- SECURITY SETUP ---
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# --- MONGODB SETUP ---
# Connects to the URI in your .env file (defaults to local if not found)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)

# Creates a database called 'ayushgpt_db' and a collection called 'users'
db = client.ayushgpt_db
users_collection = db.users

class AuthUser(BaseModel):
    email: str
    password: str

# --- UTILITY FUNCTIONS ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


# --- AUTH ENDPOINTS ---
@router.post("/register")
async def register(user: AuthUser):
    # 1. Check if user exists in MongoDB
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 2. Hash password and generate ID
    user_id = f"user_{int(time.time())}"
    hashed_password = get_password_hash(user.password)
    
    # 3. Save the new user document to MongoDB
    new_user = {
        "email": user.email,
        "password": hashed_password,
        "id": user_id,
        "created_at": datetime.utcnow()
    }
    await users_collection.insert_one(new_user)
    
    return {"message": "Registration successful! You can now login."}

@router.post("/login")
async def login(user: AuthUser):
    # 1. Fetch the user document from MongoDB
    db_user = await users_collection.find_one({"email": user.email})
    
    # 2. Verify existence and password
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    # 3. Generate JWT
    access_token = create_access_token(data={"sub": db_user["id"], "email": user.email})
    return {"message": "Login successful!", "token": access_token, "userId": db_user["id"]}
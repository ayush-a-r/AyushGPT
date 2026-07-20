from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import bcrypt
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
security = HTTPBearer()

# --- UTILITY FUNCTIONS ---
def get_password_hash(password: str) -> str:
    # Native bcrypt hashing (No passlib needed!)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

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


# --- MONGODB SETUP ---
MONGO_URI = os.getenv("MONGO_URI")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client.ayushgpt_db
users_collection = db.users

class AuthUser(BaseModel):
    email: str
    password: str

# --- AUTH ENDPOINTS (PURE JSON) ---
@router.post("/register")
async def register(user: AuthUser):
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = f"user_{int(time.time())}"
    hashed_password = get_password_hash(user.password)
    
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
    db_user = await users_collection.find_one({"email": user.email})
    
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": db_user["id"], "email": user.email})
    
    # Returns "token" just like your frontend is expecting
    return {"message": "Login successful!", "token": access_token, "userId": db_user["id"]}
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import uuid
import csv
import io
import os
import asyncio
import time

from passlib.context import CryptContext
from jose import JWTError, jwt

from services.email_sender import EmailSender
from utils.db import get_db, Database

app = FastAPI(title="Outreach Engine API", version="1.0.0")

# ==========================
# 🔐 AUTH
# ==========================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password[:72])

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

SECRET_KEY = "supersecretkey123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 3600

security = HTTPBearer()

def create_access_token(data: dict):
    to_encode = data.copy()
    to_encode["exp"] = int(time.time()) + ACCESS_TOKEN_EXPIRE_SECONDS
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["user_id"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==========================
# ROOT
# ==========================

@app.get("/")
def root():
    return RedirectResponse(url="/docs")

@app.get("/health")
async def health():
    return {"status": "ok"}

# ==========================
# CORS
# ==========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================
# AUTH ROUTES
# ==========================

class SignupRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/auth/signup")
async def signup(data: SignupRequest, db: Database = Depends(get_db)):
    existing = await db.fetchrow(
        "SELECT * FROM public.users WHERE email = $1",
        data.email
    )

    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    user_id = str(uuid.uuid4())

    await db.execute("""
        INSERT INTO public.users (id, email, password)
        VALUES ($1, $2, $3)
    """, user_id, data.email, hash_password(data.password))

    return {"user_id": user_id}

@app.post("/auth/login")
async def login(data: LoginRequest, db: Database = Depends(get_db)):
    user = await db.fetchrow(
        "SELECT * FROM public.users WHERE email = $1",
        data.email
    )

    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    if not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid password")

    token = create_access_token({"user_id": str(user["id"])})

    return {"access_token": token, "user_id": user["id"]}

# ==========================
# CREATE CAMPAIGN
# ==========================

class CampaignCreate(BaseModel):
    name: str

@app.post("/api/campaigns")
async def create_campaign(
    data: CampaignCreate,
    db: Database = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    campaign_id = str(uuid.uuid4())

    await db.execute("""
        INSERT INTO public.campaigns (id, user_id, name, status)
        VALUES ($1, $2, $3, 'pending')
    """, campaign_id, user_id, data.name)

    return {"id": campaign_id}

# ==========================
# UPLOAD CSV
# ==========================

@app.post("/api/campaigns/{campaign_id}/upload")
async def upload_prospects(
    campaign_id: str,
    file: UploadFile = File(...),
    db: Database = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8")))

    count = 0

    for p in reader:
        await db.execute("""
            INSERT INTO public.prospects 
            (id, campaign_id, user_id, first_name, last_name, email)
            VALUES ($1,$2,$3,$4,$5,$6)
        """,
            str(uuid.uuid4()),
            campaign_id,
            user_id,
            p.get("first_name"),
            p.get("last_name"),
            p.get("email")
        )
        count += 1

    return {"count": count}

# ==========================
# 🚨 GENERATE (FORCED FIX)
# ==========================

@app.post("/api/campaigns/{campaign_id}/generate")
async def generate_campaign(
    campaign_id: str,
    db: Database = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    prospects = await db.fetch("""
        SELECT * FROM public.prospects
        WHERE campaign_id = $1 AND user_id = $2
    """, campaign_id, user_id)

    for p in prospects:
        await db.execute("""
            UPDATE public.prospects SET
                personalized_first_line = $1,
                subject_line = $2,
                email_body = $3,
                generation_status = 'done'
            WHERE id = $4
        """,
            "Hi there,",
            "Quick question",
            f"Hi {p.get('first_name')}, I wanted to reach out.",
            p["id"]
        )

    return {"message": "Generated"}

# ==========================
# SEND EMAILS
# ==========================

@app.post("/api/campaigns/{campaign_id}/send")
async def send_campaign_emails(
    campaign_id: str,
    db: Database = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    sender = EmailSender()

    prospects = await db.fetch("""
        SELECT * FROM public.prospects
        WHERE campaign_id = $1
        AND user_id = $2
        AND generation_status = 'done'
    """, campaign_id, user_id)

    if not prospects:
        return {"message": "No emails to send", "count": 0}

    sent = 0

    for p in prospects:
        await asyncio.to_thread(
            sender.send_email,
            p["email"],
            p["subject_line"],
            p["email_body"]
        )

        await db.execute("""
            UPDATE public.prospects
            SET generation_status = 'sent'
            WHERE id = $1
        """, p["id"])

        sent += 1

    return {"count": sent}

# ==========================
# VIEW PROSPECTS
# ==========================

@app.get("/api/campaigns/{campaign_id}/prospects")
async def get_prospects(
    campaign_id: str,
    db: Database = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    return await db.fetch("""
        SELECT * FROM public.prospects 
        WHERE campaign_id = $1 AND user_id = $2
    """, campaign_id, user_id)
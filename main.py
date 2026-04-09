from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel
from typing import Optional
import uuid
import csv
import io
import os
import asyncio

from passlib.context import CryptContext

from services.enrichment import EnrichmentService
from services.generation import GenerationService
from services.email_sender import EmailSender
from utils.db import get_db, Database

app = FastAPI(title="Outreach Engine API", version="1.0.0")


# 🔐 PASSWORD HASHING (FIXED)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password[:72])  # ✅ FIX

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)


# ✅ ROOT
@app.get("/")
def root():
    return RedirectResponse(url="/docs")


# ✅ HEALTH
@app.get("/health")
async def health():
    return {"status": "ok"}


# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_USER_ID = "11111111-1111-1111-1111-111111111111"


# ─────────────────────────────
# 🔐 AUTH MODELS
# ─────────────────────────────

class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


# ─────────────────────────────
# 🔐 SIGNUP (FIXED)
# ─────────────────────────────

@app.post("/auth/signup")
async def signup(data: SignupRequest, db: Database = Depends(get_db)):
    try:
        existing = await db.fetchrow(
            "SELECT * FROM public.users WHERE email = $1",
            data.email
        )

        if existing:
            raise HTTPException(status_code=400, detail="User already exists")

        hashed_password = hash_password(data.password)  # ✅ FIXED

        user_id = str(uuid.uuid4())

        await db.execute("""
            INSERT INTO public.users (id, email, password)
            VALUES ($1, $2, $3)
        """, user_id, data.email, hashed_password)

        return {"message": "User created", "user_id": user_id}

    except HTTPException:
        raise
    except Exception as e:
        print("❌ SIGNUP ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────
# 🔐 LOGIN (FIXED)
# ─────────────────────────────

@app.post("/auth/login")
async def login(data: LoginRequest, db: Database = Depends(get_db)):
    try:
        user = await db.fetchrow(
            "SELECT * FROM public.users WHERE email = $1",
            data.email
        )

        if not user:
            raise HTTPException(status_code=400, detail="User not found")

        if not verify_password(data.password, user["password"]):  # ✅ FIXED
            raise HTTPException(status_code=400, detail="Invalid password")

        return {
            "message": "Login successful",
            "user_id": user["id"]
        }

    except HTTPException:
        raise
    except Exception as e:
        print("❌ LOGIN ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────
# CREATE CAMPAIGN
# ─────────────────────────────

class CampaignCreate(BaseModel):
    name: str
    tone: str = "professional"
    offer_override: Optional[str] = None


@app.post("/api/campaigns")
async def create_campaign(data: CampaignCreate, db: Database = Depends(get_db)):
    try:
        campaign_id = str(uuid.uuid4())

        await db.execute("""
            INSERT INTO public.campaigns 
            (id, user_id, name, status, tone, offer_override, created_at, updated_at)
            VALUES ($1, $2, $3, 'pending', $4, $5, NOW(), NOW())
        """, campaign_id, TEMP_USER_ID, data.name, data.tone, data.offer_override)

        return {"id": campaign_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────
# UPLOAD CSV
# ─────────────────────────────

@app.post("/api/campaigns/{campaign_id}/upload")
async def upload_prospects(campaign_id: str, file: UploadFile = File(...), db: Database = Depends(get_db)):
    try:
        content = await file.read()
        decoded = content.decode("utf-8")

        reader = csv.DictReader(io.StringIO(decoded))
        prospects = list(reader)

        for p in prospects:
            await db.execute("""
                INSERT INTO public.prospects 
                (id, campaign_id, user_id, first_name, last_name, email, company, title, linkedin_url, website)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
            """,
                str(uuid.uuid4()),
                campaign_id,
                TEMP_USER_ID,
                p.get("first_name"),
                p.get("last_name"),
                p.get("email"),
                p.get("company"),
                p.get("title"),
                p.get("linkedin_url"),
                p.get("website")
            )

        return {"message": "Uploaded", "count": len(prospects)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────
# GENERATE EMAILS
# ─────────────────────────────

@app.post("/api/campaigns/{campaign_id}/generate")
async def generate_campaign(campaign_id: str, db: Database = Depends(get_db)):
    enrichment = EnrichmentService()
    generation = GenerationService()

    prospects = await db.fetch("""
        SELECT * FROM public.prospects
        WHERE campaign_id = $1 AND user_id = $2
    """, campaign_id, TEMP_USER_ID)

    for p in prospects:
        try:
            data = await enrichment.enrich(p)
            copy = generation.generate(p, data, "We help businesses scale outreach using AI.")

            await db.execute("""
                UPDATE public.prospects SET
                    personalized_first_line = $1,
                    subject_line = $2,
                    email_body = $3,
                    generation_status = 'done'
                WHERE id = $4
            """,
                copy.get("first_line", ""),
                copy.get("subject", ""),
                copy.get("body", ""),
                p["id"]
            )

        except Exception as e:
            print("❌ GENERATION ERROR:", e)

    return {"message": "Generated"}


# ─────────────────────────────
# SEND EMAILS
# ─────────────────────────────

@app.post("/api/campaigns/{campaign_id}/send")
async def send_campaign_emails(campaign_id: str, db: Database = Depends(get_db)):
    try:
        sender = EmailSender()

        prospects = await db.fetch("""
            SELECT * FROM public.prospects
            WHERE campaign_id = $1
            AND user_id = $2
            AND generation_status = 'done'
            LIMIT 10
        """, campaign_id, TEMP_USER_ID)

        if not prospects:
            return {"message": "No emails to send", "count": 0}

        BASE_URL = os.getenv("BASE_URL", "https://outreach-engine-pexa.onrender.com")

        sent_count = 0

        for p in prospects:
            try:
                subject = p.get("subject_line") or "Quick question"

                body = f"""
<p>{p.get("personalized_first_line") or ""}</p>
<p>{p.get("email_body") or ""}</p>
"""

                tracking_pixel = f'<img src="{BASE_URL}/track/{p["id"]}" width="1" height="1" />'
                full_body = body + tracking_pixel

                await asyncio.to_thread(sender.send_email, p["email"], subject, full_body)

                sent_count += 1

                await db.execute("""
                    UPDATE public.prospects
                    SET generation_status = 'sent'
                    WHERE id = $1
                """, p["id"])

            except Exception as e:
                print("❌ SEND FAIL:", e)

        return {"message": "Emails processed", "count": sent_count}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────
# TRACK OPEN
# ─────────────────────────────

@app.get("/track/{prospect_id}")
async def track_email_open(prospect_id: str, db: Database = Depends(get_db)):
    await db.execute("""
        UPDATE public.prospects
        SET opened = TRUE
        WHERE id = $1
    """, prospect_id)

    pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'

    return Response(content=pixel, media_type="image/gif")


# ─────────────────────────────
# VIEW PROSPECTS
# ─────────────────────────────

@app.get("/api/campaigns/{campaign_id}/prospects")
async def get_prospects(campaign_id: str, db: Database = Depends(get_db)):
    return await db.fetch("""
        SELECT * FROM public.prospects 
        WHERE campaign_id = $1 AND user_id = $2
    """, campaign_id, TEMP_USER_ID)


# ─────────────────────────────
# FIX DB
# ─────────────────────────────

@app.get("/api/fix-db")
async def fix_db(db: Database = Depends(get_db)):
    await db.execute("""
        ALTER TABLE public.prospects 
        ADD COLUMN IF NOT EXISTS opened BOOLEAN DEFAULT FALSE;
    """)
    return {"message": "DB fixed"}
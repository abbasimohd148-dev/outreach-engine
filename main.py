from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
import uuid
import csv
import io

from services.enrichment import EnrichmentService
from services.generation import GenerationService
from services.email_sender import EmailSender
from utils.db import get_db, Database

app = FastAPI(title="Outreach Engine API", version="1.0.0")

# Root → Docs redirect
@app.get("/")
def root():
    return RedirectResponse(url="/docs")


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ VALID USER ID (must exist in DB)
TEMP_USER_ID = "11111111-1111-1111-1111-111111111111"


# ─────────────────────────────
# CAMPAIGN CREATE
# ─────────────────────────────

class CampaignCreate(BaseModel):
    name: str
    tone: str = "professional"
    offer_override: Optional[str] = None


@app.post("/api/campaigns")
async def create_campaign(
    data: CampaignCreate,
    db: Database = Depends(get_db)
):
    campaign_id = str(uuid.uuid4())

    await db.execute("""
        INSERT INTO public.campaigns (id, user_id, name, status, tone, offer_override, created_at, updated_at)
        VALUES ($1, $2, $3, 'pending', $4, $5, NOW(), NOW())
    """, campaign_id, TEMP_USER_ID, data.name, data.tone, data.offer_override)

    return {"id": campaign_id}


# ─────────────────────────────
# UPLOAD CSV
# ─────────────────────────────

@app.post("/api/campaigns/{campaign_id}/upload")
async def upload_prospects(
    campaign_id: str,
    file: UploadFile = File(...),
    db: Database = Depends(get_db)
):
    content = await file.read()
    decoded = content.decode("utf-8")

    reader = csv.DictReader(io.StringIO(decoded))
    prospects = list(reader)

    if not prospects:
        raise HTTPException(status_code=400, detail="CSV is empty")

    inserted_ids = []

    for p in prospects:
        pid = str(uuid.uuid4())

        await db.execute("""
            INSERT INTO public.prospects 
            (id, campaign_id, user_id, first_name, last_name, email, company, title, linkedin_url, website)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
        """,
            pid,
            campaign_id.strip(),
            TEMP_USER_ID,
            p.get("first_name"),
            p.get("last_name"),
            p.get("email"),
            p.get("company"),
            p.get("title"),
            p.get("linkedin_url"),
            p.get("website")
        )

        inserted_ids.append(pid)

    return {"message": "Uploaded", "count": len(inserted_ids)}


# ─────────────────────────────
# GENERATE EMAILS
# ─────────────────────────────

@app.post("/api/campaigns/{campaign_id}/generate")
async def generate_campaign(
    campaign_id: str,
    db: Database = Depends(get_db)
):
    enrichment = EnrichmentService()
    generation = GenerationService()

    prospects = await db.fetch("""
        SELECT * FROM public.prospects
        WHERE campaign_id = $1 AND user_id = $2
    """, campaign_id.strip(), TEMP_USER_ID)

    if not prospects:
        return {"message": "No prospects found"}

    offer = "We help businesses scale outreach with AI automation."

    for p in prospects:
        try:
            enrichment_data = await enrichment.enrich(p)
            copy = generation.generate(p, enrichment_data, offer)

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

    return {"message": "Generation completed"}


# ─────────────────────────────
# SEND EMAILS
# ─────────────────────────────

@app.post("/api/campaigns/{campaign_id}/send")
async def send_campaign_emails(
    campaign_id: str,
    db: Database = Depends(get_db)
):
    sender = EmailSender()

    prospects = await db.fetch("""
        SELECT * FROM public.prospects
        WHERE campaign_id = $1
        AND user_id = $2
        AND generation_status = 'done'
        LIMIT 20
    """, campaign_id, TEMP_USER_ID)

    if not prospects:
        return {"message": "No emails to send"}

    for p in prospects:
        try:
            subject = p.get("subject_line") or "Quick question"

            body = f"""
{p.get("personalized_first_line") or ""}

{p.get("email_body") or ""}
"""

            sender.send_email(p["email"], subject, body)

            await db.execute("""
                UPDATE public.prospects
                SET generation_status = 'sent'
                WHERE id = $1
            """, p["id"])

        except Exception as e:
            print("❌ SEND ERROR:", e)

            await db.execute("""
                UPDATE public.prospects
                SET generation_status = 'failed'
                WHERE id = $1
            """, p["id"])

    return {"message": "Emails sent", "count": len(prospects)}


# ─────────────────────────────
# VIEW PROSPECTS
# ─────────────────────────────

@app.get("/api/campaigns/{campaign_id}/prospects")
async def get_prospects(
    campaign_id: str,
    db: Database = Depends(get_db)
):
    rows = await db.fetch("""
        SELECT * FROM public.prospects 
        WHERE campaign_id = $1 AND user_id = $2
    """, campaign_id.strip(), TEMP_USER_ID)

    return rows
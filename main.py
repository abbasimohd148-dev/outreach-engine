from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid
import csv
import io

from services.enrichment import EnrichmentService
from services.generation import GenerationService
from services.email_sender import EmailSender
from utils.db import get_db, Database
from utils.auth import get_current_user

app = FastAPI(title="Outreach Engine API", version="1.0.0")

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ ROOT REDIRECT TO DOCS
@app.get("/")
def root():
    return RedirectResponse(url="/docs")


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
    user=Depends(get_current_user),
    db: Database = Depends(get_db)
):
    campaign_id = str(uuid.uuid4())

    await db.execute("""
        INSERT INTO campaigns (id, user_id, name, tone, offer_override)
        VALUES ($1, $2, $3, $4, $5)
    """, campaign_id, user["id"], data.name, data.tone, data.offer_override)

    return {"id": campaign_id}


# ─────────────────────────────
# UPLOAD CSV
# ─────────────────────────────

@app.post("/api/campaigns/{campaign_id}/upload")
async def upload_prospects(
    campaign_id: str,
    file: UploadFile = File(...),
    user=Depends(get_current_user),
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
            INSERT INTO prospects 
            (id, campaign_id, user_id, first_name, last_name, email, company, title, linkedin_url, website)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
        """,
            pid,
            campaign_id.strip(),
            user["id"],
            p.get("first_name"),
            p.get("last_name"),
            p.get("email"),
            p.get("company"),
            p.get("title"),
            p.get("linkedin_url"),
            p.get("website")
        )

        inserted_ids.append(pid)

    print(f"✅ Uploaded {len(inserted_ids)} prospects")

    return {"message": "Uploaded", "count": len(inserted_ids)}


# ─────────────────────────────
# GENERATE (MANUAL)
# ─────────────────────────────

@app.post("/api/campaigns/{campaign_id}/generate")
async def generate_campaign(
    campaign_id: str,
    user=Depends(get_current_user),
    db: Database = Depends(get_db)
):
    enrichment = EnrichmentService()
    generation = GenerationService()

    prospects = await db.fetch("""
        SELECT * FROM prospects
        WHERE campaign_id = $1 AND user_id = $2
    """, campaign_id.strip(), user["id"])

    if not prospects:
        return {"message": "No prospects found"}

    user_row = await db.fetchrow("SELECT * FROM users WHERE id = $1", user["id"])
    offer = user_row["offer_context"]

    for p in prospects:
        try:
            print("\n🚀 START GENERATION")
            print("📧 Prospect:", p["email"])

            enrichment_data = await enrichment.enrich(p)

            copy = generation.generate(p, enrichment_data, offer)

            print("🧠 AI RESULT:", copy)

            await db.execute("""
                UPDATE prospects SET
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
    user=Depends(get_current_user),
    db: Database = Depends(get_db)
):
    sender = EmailSender()

    prospects = await db.fetch("""
        SELECT * FROM prospects
        WHERE campaign_id = $1
        AND user_id = $2
        AND generation_status = 'done'
        LIMIT 20
    """, campaign_id, user["id"])

    if not prospects:
        return {"message": "No emails to send"}

    for p in prospects:
        try:
            print(f"📧 Sending email to {p['email']}")

            subject = p.get("subject_line") or "Quick question"

            body = f"""
{p.get("personalized_first_line") or ""}

{p.get("email_body") or ""}
"""

            sender.send_email(p["email"], subject, body)

            await db.execute("""
                UPDATE prospects
                SET generation_status = 'sent'
                WHERE id = $1
            """, p["id"])

        except Exception as e:
            print("❌ SEND ERROR:", e)

            await db.execute("""
                UPDATE prospects
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
    user=Depends(get_current_user),
    db: Database = Depends(get_db)
):
    rows = await db.fetch("""
        SELECT * FROM prospects 
        WHERE campaign_id = $1 AND user_id = $2
    """, campaign_id.strip(), user["id"])

    return rows
# 🚀 Cold Outreach Personalization Engine

AI-powered SaaS that enriches prospects from LinkedIn, news, funding data, and tech stack — then generates hyper-personalized cold emails automatically.

---

## Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 14 + Tailwind CSS |
| Backend | FastAPI (Python) |
| Database | PostgreSQL + Redis |
| Auth | Clerk |
| Payments | Stripe |
| AI | Anthropic Claude |
| Enrichment | Proxycurl, SerpAPI, BuiltWith |
| Hosting | Railway (backend) + Vercel (frontend) |

---

## Project Structure

```
outreach-engine/
├── backend/
│   ├── main.py                  # FastAPI app + all routes
│   ├── requirements.txt
│   ├── models/
│   │   └── schema.sql           # Full PostgreSQL schema
│   ├── services/
│   │   ├── enrichment.py        # Multi-source data pipeline
│   │   ├── generation.py        # Claude AI copy generation
│   │   └── billing.py           # Stripe integration
│   └── utils/
│       ├── db.py                # asyncpg database utility
│       └── auth.py              # Clerk JWT verification
└── frontend/                    # Next.js app (scaffold separately)
    ├── components/
    ├── pages/
    └── lib/
```

---

## Local Setup

### 1. Clone & install backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Set up PostgreSQL
```bash
createdb outreach_engine
psql outreach_engine < models/schema.sql
```

### 3. Configure environment
```bash
cp .env.example .env
# Fill in all API keys (see API Keys section below)
```

### 4. Run backend
```bash
uvicorn main:app --reload --port 8000
```

### 5. Set up frontend (Next.js)
```bash
npx create-next-app@latest frontend --typescript --tailwind --app
cd frontend
npm install @clerk/nextjs stripe
```

---

## API Keys You Need

| Service | Purpose | Free Tier? | Cost at 1K prospects/mo |
|---------|---------|------------|--------------------------|
| [Anthropic](https://console.anthropic.com) | Email generation | No | ~$10 |
| [Proxycurl](https://nubela.co/proxycurl) | LinkedIn data | No | ~$10 |
| [SerpAPI](https://serpapi.com) | News + Google | 100 free/mo | $50/mo |
| [BuiltWith](https://api.builtwith.com) | Tech stack | No | $49/mo |
| [Clerk](https://clerk.com) | Auth | Yes (10k MAU) | Free |
| [Stripe](https://stripe.com) | Payments | % per txn | % of revenue |

**Total API cost at 1,000 prospects/mo: ~$80–120**

---

## Pricing Model

| Plan | Price | Credits |
|------|-------|---------|
| Starter | $49/mo | 200 prospects |
| Growth | $149/mo | 1,000 prospects |
| Agency | $399/mo | 5,000 prospects |

**Margins at Growth plan:** $149 revenue - ~$80 cost = ~$69/customer **46% margin**

---

## CSV Upload Format

Required columns:
```
first_name, last_name, email, company, title
```

Optional (improves personalization):
```
linkedin_url, website
```

---

## Enrichment Pipeline

For each prospect, the tool runs 4 parallel enrichment layers:

1. **LinkedIn** (Proxycurl) → bio, headline, experiences
2. **Company news** (SerpAPI) → recent press coverage
3. **Tech stack** (BuiltWith) → tools they use (HubSpot, Salesforce, etc.)
4. **Funding** (SerpAPI) → recent rounds/raises

The best 2-3 signals are extracted and passed to Claude for generation.

---

## AI Generation Prompt Strategy

- System: Expert cold email copywriter persona
- Context: Prospect data + top signals
- Output: JSON with `subject_line`, `first_line`, `body`
- Constraints: No "hope this finds you well", under 90 words, one specific signal reference

---

## Deployment

### Backend → Railway
```bash
# railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
```

### Frontend → Vercel
```bash
vercel deploy
```

### Database → Supabase or Railway PostgreSQL

---

## Roadmap to $2K MRR (for Acquire.com sale)

- [ ] Week 1-2: Auth + DB + CSV upload working
- [ ] Week 3-4: Enrichment pipeline live
- [ ] Week 5-6: AI generation + review UI
- [ ] Week 7-8: Stripe billing + export
- [ ] Week 9-10: Beta with 5 free users, get testimonials  
- [ ] Week 11: ProductHunt launch
- [ ] Week 12: AppSumo LTD deal for quick MRR spike
- [ ] Month 3: 15+ paying customers → list on Acquire.com at 3-4x ARR

---

## Selling on Acquire.com

Target metrics before listing:
- $2,000+ MRR
- <5% monthly churn
- 20+ active customers
- Clean codebase with docs
- Documented API costs and margins

Expected sale price: **$60K–$120K** at $2K MRR (30-60x monthly)

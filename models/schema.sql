-- =============================================
-- Cold Outreach Personalization Engine
-- PostgreSQL Schema
-- =============================================

-- Users table (managed by Clerk/Supabase Auth externally)
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_id TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  plan TEXT DEFAULT 'starter' CHECK (plan IN ('starter', 'growth', 'agency')),
  credits_used INTEGER DEFAULT 0,
  credits_limit INTEGER DEFAULT 200,
  stripe_customer_id TEXT,
  stripe_subscription_id TEXT,
  offer_context TEXT,        -- user's elevator pitch / what they're selling
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Campaigns
CREATE TABLE campaigns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'enriching', 'generating', 'ready', 'exported')),
  tone TEXT DEFAULT 'professional' CHECK (tone IN ('professional', 'casual', 'direct', 'friendly')),
  offer_override TEXT,       -- campaign-specific offer (overrides user default)
  total_prospects INTEGER DEFAULT 0,
  enriched_count INTEGER DEFAULT 0,
  generated_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Prospects
CREATE TABLE prospects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,

  -- Input data (from CSV)
  first_name TEXT,
  last_name TEXT,
  email TEXT,
  company TEXT,
  title TEXT,
  linkedin_url TEXT,
  website TEXT,

  -- Enrichment data
  linkedin_bio TEXT,
  linkedin_recent_posts JSONB,
  company_news JSONB,           -- [{title, url, date, snippet}]
  funding_data JSONB,           -- {round, amount, date, investors}
  tech_stack JSONB,             -- [tool names]
  job_postings JSONB,           -- inferred pain points
  company_size TEXT,
  company_industry TEXT,
  enrichment_status TEXT DEFAULT 'pending' CHECK (enrichment_status IN ('pending', 'running', 'done', 'failed')),
  enrichment_signals JSONB,     -- key signals selected for personalization
  enrichment_error TEXT,
  enriched_at TIMESTAMPTZ,

  -- Generated copy
  personalized_first_line TEXT,
  subject_line TEXT,
  email_body TEXT,
  generation_status TEXT DEFAULT 'pending' CHECK (generation_status IN ('pending', 'done', 'failed')),
  generated_at TIMESTAMPTZ,

  -- User edits
  edited_first_line TEXT,
  edited_subject_line TEXT,
  edited_email_body TEXT,
  is_approved BOOLEAN DEFAULT FALSE,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enrichment job queue log
CREATE TABLE enrichment_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  prospect_id UUID REFERENCES prospects(id) ON DELETE CASCADE,
  campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
  status TEXT DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'done', 'failed')),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  error_message TEXT,
  api_calls_made JSONB,         -- log which APIs were hit
  cost_cents INTEGER DEFAULT 0  -- track per-prospect cost
);

-- Usage tracking
CREATE TABLE usage_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,     -- 'enrichment', 'generation', 'export'
  prospect_id UUID,
  campaign_id UUID,
  cost_cents INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_prospects_campaign ON prospects(campaign_id);
CREATE INDEX idx_prospects_enrichment_status ON prospects(enrichment_status);
CREATE INDEX idx_campaigns_user ON campaigns(user_id);
CREATE INDEX idx_usage_user ON usage_events(user_id);
CREATE INDEX idx_jobs_status ON enrichment_jobs(status);

# services/enrichment.py
# Multi-source prospect enrichment pipeline

import httpx
import asyncio
import os
import json
from typing import Optional

PROXYCURL_KEY = os.getenv("PROXYCURL_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
HUNTER_KEY = os.getenv("HUNTER_API_KEY")
BUILTWITH_KEY = os.getenv("BUILTWITH_API_KEY")


class EnrichmentService:

    async def enrich(self, prospect: dict) -> dict:
        """
        Run all enrichment layers in parallel where possible.
        Returns consolidated enrichment data + extracted signals.
        """
        tasks = []

        # Layer 1: LinkedIn (if URL provided)
        if prospect.get("linkedin_url"):
            tasks.append(self._fetch_linkedin(prospect["linkedin_url"]))
        else:
            tasks.append(asyncio.sleep(0))  # placeholder

        # Layer 2: Company news
        if prospect.get("company"):
            tasks.append(self._fetch_company_news(prospect["company"]))
        else:
            tasks.append(asyncio.sleep(0))

        # Layer 3: Tech stack
        if prospect.get("website"):
            tasks.append(self._fetch_tech_stack(prospect["website"]))
        else:
            tasks.append(asyncio.sleep(0))

        # Layer 4: Funding data
        if prospect.get("company"):
            tasks.append(self._fetch_funding(prospect["company"]))
        else:
            tasks.append(asyncio.sleep(0))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        linkedin_data = results[0] if not isinstance(results[0], Exception) else {}
        company_news = results[1] if not isinstance(results[1], Exception) else []
        tech_stack = results[2] if not isinstance(results[2], Exception) else []
        funding_data = results[3] if not isinstance(results[3], Exception) else {}

        # Extract the best personalization signals
        signals = self._extract_signals(
            prospect, linkedin_data, company_news, tech_stack, funding_data
        )

        return {
            "linkedin_bio": linkedin_data.get("summary"),
            "linkedin_recent_posts": linkedin_data.get("recent_posts", []),
            "company_news": company_news,
            "funding_data": funding_data,
            "tech_stack": tech_stack,
            "signals": signals,
        }

    # ─────────────────────────────────────────
    # LAYER 1: LinkedIn via Proxycurl
    # ─────────────────────────────────────────
    async def _fetch_linkedin(self, linkedin_url: str) -> dict:
        """
        Fetch LinkedIn profile data via Proxycurl API.
        Docs: https://nubela.co/proxycurl/docs
        Cost: ~$0.01 per call
        """
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://nubela.co/proxycurl/api/v2/linkedin",
                params={
                    "url": linkedin_url,
                    "use_cache": "if-present",
                    "fallback_to_cache": "on-error",
                },
                headers={"Authorization": f"Bearer {PROXYCURL_KEY}"},
                timeout=15.0,
            )
            if resp.status_code != 200:
                return {}

            data = resp.json()
            return {
                "summary": data.get("summary", ""),
                "headline": data.get("headline", ""),
                "experiences": data.get("experiences", [])[:3],
                "recent_posts": [],  # Proxycurl has separate endpoint for posts
                "skills": [s["name"] for s in data.get("skills", [])[:10]],
            }

    # ─────────────────────────────────────────
    # LAYER 2: Company News via SerpAPI
    # ─────────────────────────────────────────
    async def _fetch_company_news(self, company: str) -> list:
        """
        Search Google News for recent company coverage.
        Docs: https://serpapi.com/news-results
        Cost: $50/mo for 5000 searches
        """
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://serpapi.com/search",
                params={
                    "engine": "google_news",
                    "q": company,
                    "api_key": SERPAPI_KEY,
                    "num": 5,
                },
                timeout=10.0,
            )
            if resp.status_code != 200:
                return []

            results = resp.json().get("news_results", [])
            return [
                {
                    "title": r.get("title"),
                    "snippet": r.get("snippet"),
                    "date": r.get("date"),
                    "source": r.get("source", {}).get("name"),
                }
                for r in results[:5]
            ]

    # ─────────────────────────────────────────
    # LAYER 3: Tech Stack via BuiltWith
    # ─────────────────────────────────────────
    async def _fetch_tech_stack(self, website: str) -> list:
        """
        Detect what tools/tech the company uses.
        Docs: https://api.builtwith.com/
        Cost: Paid plan needed for full data
        Alternative: Use Clearbit Reveal free tier
        """
        domain = website.replace("https://", "").replace("http://", "").split("/")[0]
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.builtwith.com/v21/api.json",
                params={"KEY": BUILTWITH_KEY, "LOOKUP": domain},
                timeout=10.0,
            )
            if resp.status_code != 200:
                return []

            data = resp.json()
            tech_names = []
            try:
                paths = data["Results"][0]["Result"]["Paths"]
                for path in paths:
                    for tech in path.get("Technologies", []):
                        tech_names.append(tech.get("Name"))
            except (KeyError, IndexError):
                pass
            return list(set(tech_names))[:20]

    # ─────────────────────────────────────────
    # LAYER 4: Funding via Crunchbase / Harmonic
    # ─────────────────────────────────────────
    async def _fetch_funding(self, company: str) -> dict:
        """
        Check recent funding rounds.
        Alternative free approach: search SerpAPI for "[company] funding round 2025"
        """
        # MVP approach: use SerpAPI to search for funding news
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://serpapi.com/search",
                params={
                    "engine": "google",
                    "q": f"{company} funding round raised 2024 OR 2025",
                    "api_key": SERPAPI_KEY,
                    "num": 3,
                },
                timeout=10.0,
            )
            if resp.status_code != 200:
                return {}

            results = resp.json().get("organic_results", [])
            if results:
                return {
                    "detected": True,
                    "headline": results[0].get("title"),
                    "snippet": results[0].get("snippet"),
                }
            return {"detected": False}

    # ─────────────────────────────────────────
    # SIGNAL EXTRACTION — pick the best hooks
    # ─────────────────────────────────────────
    def _extract_signals(
        self,
        prospect: dict,
        linkedin: dict,
        news: list,
        tech: list,
        funding: dict,
    ) -> dict:
        """
        Rank and select the top 2-3 personalization signals.
        These get passed to the AI generation prompt.
        Priority: funding > news > linkedin bio > tech stack
        """
        signals = {}

        if funding.get("detected"):
            signals["funding"] = funding.get("headline")

        if news:
            signals["recent_news"] = news[0].get("title")

        if linkedin.get("headline"):
            signals["linkedin_headline"] = linkedin["headline"]

        if linkedin.get("summary"):
            signals["linkedin_summary"] = linkedin["summary"][:300]

        if tech:
            # Flag interesting tools (CRMs, ad tools etc.)
            interesting = ["HubSpot", "Salesforce", "Marketo", "Klaviyo",
                          "Shopify", "Stripe", "Segment", "Intercom"]
            detected = [t for t in tech if any(i.lower() in t.lower() for i in interesting)]
            if detected:
                signals["tech_stack"] = detected[:3]

        return signals

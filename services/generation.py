import os
from groq import Groq

class GenerationService:
    def __init__(self):
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )

    def generate(self, prospect, enrichment, offer):
        try:
            prompt = f"""
Write a highly personalized cold email.

Prospect Name: {prospect.get("first_name")}
Company: {prospect.get("company")}
Job Title: {prospect.get("title")}
Offer: {offer}

Make it:
- Short
- Friendly
- Personalized
- Human-like

Return ONLY valid JSON in this format:
{{
  "first_line": "...",
  "subject": "...",
  "body": "..."
}}
"""

            response = self.client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            text = response.choices[0].message.content.strip()

            # ⚠️ fallback (if model doesn't return clean JSON)
            return {
                "first_line": f"Hi {prospect.get('first_name')},",
                "subject": "Quick question",
                "body": text
            }

        except Exception as e:
            print("❌ GROQ ERROR:", e)

            # safe fallback (so app never crashes)
            return {
                "first_line": f"Hi {prospect.get('first_name')},",
                "subject": "Quick question",
                "body": "We help companies scale outreach using AI. Would love to connect."
            }
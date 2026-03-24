import requests
import json
import re


class GenerationService:

    def generate(self, prospect, enrichment, offer, tone="professional"):

        prompt = f"""
Write a short personalized cold email (max 70 words).

Name: {prospect.get("first_name")}
Company: {prospect.get("company")}
Role: {prospect.get("title")}

Offer: {offer}

Rules:
- Keep it simple and human
- Do NOT invent anything
- Do NOT use placeholders
- Keep sentences short
- End with a simple question

Return ONLY JSON:
{{
  "subject": "...",
  "first_line": "...",
  "body": "..."
}}
"""

        try:
            print("⚡ Sending request to Ollama...")

            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "phi3",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": 200
                    }
                },
                timeout=120
            )

            if response.status_code != 200:
                return self.fallback("HTTP Error")

            data = response.json()
            output = data.get("response", "")

            print("🧠 RAW AI OUTPUT:", output)

            # ───────── CLEAN OUTPUT ─────────
            cleaned = output.strip()
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
            cleaned = re.sub(r'"\s*\+\s*"', '', cleaned)
            cleaned = re.sub(r'"\s*\n\s*"', '",\n"', cleaned)

            print("🧹 CLEANED OUTPUT:", cleaned)

            # ───────── EXTRACT JSON ─────────
            match = re.search(r"\{[\s\S]*\}", cleaned)

            if match:
                try:
                    parsed = json.loads(match.group())

                    subject = parsed.get("subject", "").strip()
                    first_line = parsed.get("first_line", "").strip()
                    body = parsed.get("body", "").strip()

                    # ✅ FIX PLACEHOLDERS
                    body = body.replace("[Name]", prospect.get("first_name") or "")
                    body = body.replace("Hey ,", f"Hey {prospect.get('first_name')},")
                    body = body.replace("Hello there!", f"Hi {prospect.get('first_name')},")

                    # ✅ REMOVE GENERIC LINES
                    if "hope this message finds you well" in first_line.lower():
                        first_line = f"Hi {prospect.get('first_name')},"

                    return {
                        "subject": subject,
                        "first_line": first_line,
                        "body": body
                    }

                except:
                    print("⚠️ JSON parsing failed")

            # ───────── FALLBACK SAFE EMAIL ─────────
            return {
                "subject": "Quick question",
                "first_line": "",
                "body": f"Hi {prospect.get('first_name')}, quick question — would you be open to a short chat about {offer}?"
            }

        except Exception as e:
            return self.fallback(str(e))


    def fallback(self, message):
        return {
            "subject": "Quick question",
            "first_line": "",
            "body": message[:150]
        }
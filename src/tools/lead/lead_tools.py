import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


class LeadTool:
    """Extracts, enriches, validates, and scores lead contact data."""

    EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
    NAME_RE = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b")

    def extract_contacts(self, text: str, source: str = "manual") -> List[Dict[str, str]]:
        emails = sorted(set(self.EMAIL_RE.findall(text or "")))
        phones = sorted(set(match.strip() for match in self.PHONE_RE.findall(text or "")))
        names = sorted(set(match.strip() for match in self.NAME_RE.findall(text or "")))

        leads: List[Dict[str, str]] = []
        for email in emails:
            leads.append({"email": email, "phone": "", "name": "", "source": source})
        for phone in phones:
            if not any(lead["phone"] == phone for lead in leads):
                leads.append({"email": "", "phone": phone, "name": "", "source": source})
        for name in names:
            if not any(lead.get("name") == name for lead in leads):
                leads.append({"email": "", "phone": "", "name": name, "source": source})
        return leads

    def enrich_leads(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        enriched = []
        for lead in leads:
            enriched_lead = lead.copy()
            email = lead.get("email", "")
            if email:
                domain = email.split("@")[-1].lower()
                enriched_lead["company_domain"] = domain
                enriched_lead["email_provider"] = self._classify_email_provider(domain)
                enriched_lead["likely_business"] = not self._is_personal_domain(domain)
            phone = lead.get("phone", "")
            if phone:
                enriched_lead["phone_country"] = self._detect_country_code(phone)
                enriched_lead["phone_formatted"] = self._format_phone(phone)
            enriched.append(enriched_lead)
        return enriched

    def _classify_email_provider(self, domain: str) -> str:
        personal_domains = {
            "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
            "icloud.com", "aol.com", "protonmail.com", "mail.com",
        }
        business_domains = {
            "company.com", "business.com", "corp.com", "inc.com",
        }
        if domain in personal_domains:
            return "personal"
        if domain in business_domains:
            return "business"
        return "unknown"

    def _is_personal_domain(self, domain: str) -> bool:
        personal = {
            "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
            "icloud.com", "aol.com", "protonmail.com", "mail.com",
            "live.com", "msn.com", "ymail.com", "rocketmail.com",
        }
        return domain in personal

    def _detect_country_code(self, phone: str) -> str:
        clean = re.sub(r"\D", "", phone)
        if clean.startswith("1") and len(clean) == 11:
            return "US/CA"
        if clean.startswith("44"):
            return "UK"
        if clean.startswith("61"):
            return "AU"
        if clean.startswith("49"):
            return "DE"
        if clean.startswith("33"):
            return "FR"
        return "unknown"

    def _format_phone(self, phone: str) -> str:
        clean = re.sub(r"\D", "", phone)
        if len(clean) == 10:
            return f"({clean[:3]}) {clean[3:6]}-{clean[6:]}"
        if len(clean) == 11 and clean.startswith("1"):
            return f"+1 ({clean[1:4]}) {clean[4:7]}-{clean[7:]}"
        return phone

    def validate_leads(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        validated = []
        for lead in leads:
            validated_lead = lead.copy()
            email = lead.get("email", "")
            phone = lead.get("phone", "")

            validated_lead["email_valid"] = bool(self.EMAIL_RE.fullmatch(email)) if email else False
            validated_lead["phone_valid"] = bool(self.PHONE_RE.fullmatch(phone)) if phone else False
            validated_lead["has_contact"] = bool(email or phone)
            validated_lead["validation_score"] = sum([
                validated_lead["email_valid"],
                validated_lead["phone_valid"],
                bool(lead.get("name")),
            ])
            validated.append(validated_lead)
        return validated

    def score_leads(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        scored = []
        for lead in leads:
            scored_lead = lead.copy()
            score = 0
            reasons = []

            if lead.get("email_valid"):
                score += 30
                reasons.append("valid_email")
            if lead.get("phone_valid"):
                score += 25
                reasons.append("valid_phone")
            if lead.get("name"):
                score += 20
                reasons.append("has_name")
            if lead.get("likely_business"):
                score += 25
                reasons.append("business_domain")
            elif lead.get("email_provider") == "personal":
                score -= 10
                reasons.append("personal_email")

            scored_lead["lead_score"] = max(0, min(100, score))
            scored_lead["score_reasons"] = reasons
            scored_lead["score_tier"] = self._get_tier(scored_lead["lead_score"])
            scored.append(scored_lead)
        return scored

    def _get_tier(self, score: int) -> str:
        if score >= 80:
            return "hot"
        elif score >= 50:
            return "warm"
        elif score >= 25:
            return "cold"
        return "unqualified"

    def deduplicate_leads(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen_emails = set()
        seen_phones = set()
        deduplicated = []
        for lead in leads:
            email = lead.get("email", "").lower()
            phone = lead.get("phone", "")
            phone_clean = re.sub(r"\D", "", phone)
            if email and email in seen_emails:
                continue
            if phone_clean and phone_clean in seen_phones:
                continue
            if email:
                seen_emails.add(email)
            if phone_clean:
                seen_phones.add(phone_clean)
            deduplicated.append(lead)
        return deduplicated

    def export_leads(
        self,
        leads: List[Dict[str, Any]],
        format: str = "json",
        output_path: str = "leads_export.json",
    ) -> Dict[str, Any]:
        if not leads:
            return {"status": "error", "message": "No leads to export"}

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(leads, f, indent=2, default=str)
            return {"status": "success", "path": output_path, "count": len(leads)}

        if format == "csv":
            fieldnames = sorted({key for lead in leads for key in lead.keys()})
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(leads)
            return {"status": "success", "path": output_path, "count": len(leads)}

        return {"status": "error", "message": f"Unsupported format: {format}"}
import re
from typing import Dict, List


class LeadTool:
    """Extracts basic lead data from provided text."""

    EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")

    def extract_contacts(self, text: str, source: str = "manual") -> List[Dict[str, str]]:
        emails = sorted(set(self.EMAIL_RE.findall(text or "")))
        phones = sorted(set(match.strip() for match in self.PHONE_RE.findall(text or "")))

        leads: List[Dict[str, str]] = []
        for email in emails:
            leads.append({"email": email, "phone": "", "source": source})
        for phone in phones:
            if not any(lead["phone"] == phone for lead in leads):
                leads.append({"email": "", "phone": phone, "source": source})
        return leads

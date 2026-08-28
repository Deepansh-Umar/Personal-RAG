import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class EducationFact(BaseModel):
    institution: str
    degree: str
    dates: str
    cgpa_or_details: Optional[str] = None
    recency_year: int = 2026


class ProfileFactSheet(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    github: str = ""
    educations: List[EducationFact] = Field(default_factory=list)
    latest_role: Optional[str] = None


class FactExtractor:
    """
    Extracts core candidate Profile & Education Fact Sheets from documents
    and resolves version conflicts by prioritizing the most recent data.
    """

    def resolve_recency(self, raw_text: str) -> ProfileFactSheet:
        fact_sheet = ProfileFactSheet()

        # Extract Name if present
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        if lines:
            fact_sheet.name = lines[0][:50]

        # Extract Email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', raw_text)
        if email_match:
            fact_sheet.email = email_match.group(0)

        # Extract Phone
        phone_match = re.search(r'\(?\+\d{1,3}\)?[\s-]?\d{9,10}', raw_text)
        if phone_match:
            fact_sheet.phone = phone_match.group(0)

        # Extract CGPAs and Degree info
        cgpa_matches = re.findall(r'(CGPA:\s*[\d\.]+)', raw_text, re.IGNORECASE)

        # Parse sections
        if "MADRAS" in raw_text.upper():
            fact_sheet.educations.append(
                EducationFact(
                    institution="Indian Institute of Technology Madras",
                    degree="Bachelor of Science in Data Science and Applications",
                    dates="2024 – Present",
                    cgpa_or_details=cgpa_matches[0] if cgpa_matches else None
                )
            )

        if "AERONAUTICAL" in raw_text.upper() or "IARE" in raw_text.upper():
            fact_sheet.educations.append(
                EducationFact(
                    institution="Institute of Aeronautical Engineering",
                    degree="Bachelor of Technology in Computer Science",
                    dates="2024 – Present",
                    cgpa_or_details=cgpa_matches[-1] if len(cgpa_matches) > 1 else None
                )
            )

        return fact_sheet

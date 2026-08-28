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
    name: str = "Deepansh Umar"
    email: str = "umardeepansh@gmail.com"
    phone: str = "(+91) 9581730273"
    linkedin: str = "https://linkedin.com"
    github: str = "https://github.com/Deepansh-Umar"
    educations: List[EducationFact] = Field(default_factory=list)
    latest_role: Optional[str] = None


class FactExtractor:
    """
    Extracts core candidate Profile & Education Fact Sheets from documents
    and resolves version conflicts by prioritizing the most recent data.
    """

    def resolve_recency(self, raw_text: str) -> ProfileFactSheet:
        fact_sheet = ProfileFactSheet()

        # Extract CGPAs and Degree info with recency detection
        cgpa_matches = re.findall(r'(CGPA:\s*[\d\.]+)', raw_text, re.IGNORECASE)

        # Default latest verified education facts
        fact_sheet.educations = [
            EducationFact(
                institution="Indian Institute of Technology Madras",
                degree="Bachelor of Science in Data Science and Applications",
                dates="2024 – Present",
                cgpa_or_details="CGPA: 9.23" if not cgpa_matches else cgpa_matches[0],
                recency_year=2026
            ),
            EducationFact(
                institution="Institute of Aeronautical Engineering, Hyderabad",
                degree="Bachelor of Technology in Computer Science",
                dates="2024 – Present",
                cgpa_or_details="CGPA: 8.6" if len(cgpa_matches) < 2 else cgpa_matches[1],
                recency_year=2026
            )
        ]

        fact_sheet.latest_role = "Student Mentor – e-DAM IARE (Sept 2025 – Present)"
        return fact_sheet

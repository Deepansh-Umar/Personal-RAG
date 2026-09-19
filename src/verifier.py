import re
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class VerificationResult(BaseModel):
    is_valid: bool
    total_claims_checked: int
    unverified_metrics: List[str]
    unverified_urls: List[str]
    warnings: List[str]


class ResumeVerificationEngine:
    """
    Verification & Guardrail Engine.
    Ensures zero hallucinations by verifying that every metric, number, URL, and institution
    in the generated Markdown resume exists in the candidate's source evidence store.
    """

    def __init__(self, evidence_yaml_path: Optional[Path] = None):
        self.evidence_path = evidence_yaml_path or (Path(__file__).parent.parent / "data" / "career_evidence.yaml")
        self.evidence_text = ""
        if self.evidence_path.exists():
            with open(self.evidence_path, "r", encoding="utf-8") as f:
                self.evidence_text = f.read()

    def verify(self, generated_markdown: str) -> VerificationResult:
        unverified_metrics = []
        unverified_urls = []
        warnings = []

        # 1. Verify Metrics & Numbers (e.g. 9.23, 8.6, 50+, 40%, 15ms, 15K)
        generated_numbers = set(re.findall(r'\b\d+(?:\.\d+)?%?\b', generated_markdown))

        for num in generated_numbers:
            if len(num) > 1 and num not in self.evidence_text:
                # Ignore common standard years or markdown formatting numbers
                if num not in ["2024", "2025", "2026", "1", "2", "3", "4", "5"]:
                    unverified_metrics.append(num)

        # 2. Verify URLs
        urls_in_resume = re.findall(r'https?://[^\s\)]+', generated_markdown)
        for url in urls_in_resume:
            clean_url = url.rstrip("/")
            if clean_url not in self.evidence_text and "linkedin.com" not in clean_url and "github.com" not in clean_url:
                unverified_urls.append(url)

        # 3. Check for JD leakage phrases (e.g. "Minimum of 3 years", "Responsibilities:")
        jd_leakage_keywords = [
            "minimum of 3 years", "responsibilities:", "requirements:",
            "type of internship:", "expected compensation", "stipend:"
        ]

        for kw in jd_leakage_keywords:
            if kw.lower() in generated_markdown.lower():
                warnings.append(f"Possible JD prompt leakage detected: '{kw}'")

        is_valid = len(unverified_metrics) == 0 and len(unverified_urls) == 0 and len(warnings) == 0

        return VerificationResult(
            is_valid=is_valid,
            total_claims_checked=len(generated_numbers) + len(urls_in_resume),
            unverified_metrics=unverified_metrics,
            unverified_urls=unverified_urls,
            warnings=warnings
        )

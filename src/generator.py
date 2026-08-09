import os
from typing import List, Dict, Any, Optional
from src.jd_parser import ParsedJobDescription


class CareerRAGGenerator:
    """
    LLM Synthesis Engine for Personal RAG.
    Generates tailored resume bullets, JD match analysis, and cover letter content
    based strictly on retrieved candidate context and target JD requirements.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self.client = None

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except ImportError:
                print("⚠️ `google-genai` package not found. Running generator in template fallback mode.")

    def construct_prompt(
        self,
        parsed_jd: ParsedJobDescription,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> str:
        context_blocks = []
        for idx, chunk in enumerate(retrieved_chunks, 1):
            context_blocks.append(
                f"--- CANDIDATE CONTEXT BLOCK {idx} (Relevance Score: {chunk['similarity_score']}) ---\n"
                f"Title: {chunk['metadata'].get('title', 'N/A')}\n"
                f"Tech Stack: {chunk['metadata'].get('tech_stack', 'N/A')}\n"
                f"Content:\n{chunk['content']}\n"
            )

        context_str = "\n".join(context_blocks)

        prompt = f"""
You are an elite Career & ATS Resume Coach. Your goal is to tailor the candidate's authentic career experiences to best match the target Job Description (JD).

CRITICAL STRICT RULES:
1. NEVER invent or hallucinate false experiences, companies, or technologies not present in the Candidate Context.
2. Highlight real metrics, quantifiable results, and technical keywords where relevant.
3. Output clear, actionable resume bullet points and a concise JD match analysis.

================ TARGET JOB DESCRIPTION ================
Title: {parsed_jd.title}
Company: {parsed_jd.company}
Required Tech/Skills: {', '.join(parsed_jd.required_skills)}
Key Responsibilities:
{chr(10).join('- ' + r for r in parsed_jd.key_responsibilities)}

================ RETRIEVED CANDIDATE CONTEXT ================
{context_str}

================ REQUIRED OUTPUT FORMAT ================
## 🎯 Job Description Match Analysis
- **Estimated Fit Score**: [e.g. 85%]
- **Matching Core Strengths**: [Key areas where candidate strongly aligns]
- **Identified Keyword Gaps**: [Skills in JD not explicitly in context]

## ✍️ Tailored Resume Bullet Points (ATS Optimized)
For each relevant position/project in the context, reframe bullet points to emphasize impact aligned with the JD:

### [Company / Project Name]
- **[Tailored Bullet 1]**: (Using STAR method: Action verb + Context + Tech used + Metric outcome)
- **[Tailored Bullet 2]**

## ✉️ High-Impact Cover Letter Snippet
(A concise 2-paragraph pitch connecting the candidate's top 2 matching projects directly to the company's core mission/JD responsibilities).
"""
        return prompt

    def generate_tailored_content(
        self,
        parsed_jd: ParsedJobDescription,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> str:
        prompt = self.construct_prompt(parsed_jd, retrieved_chunks)

        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                return f"⚠️ LLM API Error: {str(e)}\n\n--- Formatted Prompt Created ---\n\n{prompt}"
        else:
            # Fallback output showing synthesized retrieved context + generated prompt
            return (
                "ℹ️ **Running in Local Demonstration Mode (No GEMINI_API_KEY provided)**\n"
                "Here is the context retrieved by your RAG engine and ready for LLM synthesis:\n\n"
                + prompt
            )

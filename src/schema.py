from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class Profile(BaseModel):
    name: str
    title: str
    email: str
    location: str
    summary: str
    target_roles: List[str] = Field(default_factory=list)
    key_highlights: List[str] = Field(default_factory=list)


class BulletPoint(BaseModel):
    situation_action_result: str
    skills_demonstrated: List[str] = Field(default_factory=list)


class Experience(BaseModel):
    id: str
    company: str
    role: str
    start_date: str
    end_date: str
    location: str
    tech_stack: List[str] = Field(default_factory=list)
    domain_tags: List[str] = Field(default_factory=list)
    bullet_points: List[BulletPoint] = Field(default_factory=list)


class Project(BaseModel):
    id: str
    name: str
    tagline: str
    type: str
    tech_stack: List[str] = Field(default_factory=list)
    category: str
    description: str
    key_achievements: List[str] = Field(default_factory=list)


class Skill(BaseModel):
    name: str
    proficiency: str
    years_experience: Optional[int] = None
    evidence: Optional[str] = None


class SkillCategory(BaseModel):
    category: str
    skills: List[Skill] = Field(default_factory=list)


class Strength(BaseModel):
    trait: str
    description: str
    example_scenario: Optional[str] = None


class Weakness(BaseModel):
    trait: str
    mitigation_strategy: str


class CareerData(BaseModel):
    profile: Optional[Profile] = None
    experiences: List[Experience] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    skill_categories: List[SkillCategory] = Field(default_factory=list)
    strengths: List[Strength] = Field(default_factory=list)
    weaknesses: List[Weakness] = Field(default_factory=list)


class DocumentChunk(BaseModel):
    """
    Unified searchable chunk representation stored in Vector DB.
    Combines text content with structured metadata for hybrid search.
    """
    chunk_id: str
    source_type: Literal["profile", "experience", "project", "skill", "strength", "weakness"]
    title: str
    content: str
    tech_stack: List[str] = Field(default_factory=list)
    domain_tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

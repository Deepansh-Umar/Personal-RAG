from typing import List
from src.schema import CareerData, DocumentChunk


class CareerChunkSerializer:
    """
    Transforms structured CareerData into rich, metadata-enriched DocumentChunks
    optimized for dense vector embedding and hybrid metadata filtering.
    """

    def serialize(self, data: CareerData) -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []

        # 1. Profile Summary Chunk
        if data.profile:
            p = data.profile
            content = f"Professional Bio & Summary for {p.name} ({p.title}):\n{p.summary}\nTarget Roles: {', '.join(p.target_roles)}\nKey Highlights:\n" + "\n".join(f"- {h}" for h in p.key_highlights)
            chunks.append(
                DocumentChunk(
                    chunk_id="profile_summary",
                    source_type="profile",
                    title=f"Bio - {p.name}",
                    content=content,
                    tech_stack=[],
                    domain_tags=p.target_roles,
                    metadata={"email": p.email, "location": p.location}
                )
            )

        # 2. Experience Bullet Point Chunks (Granular per accomplishment)
        for exp in data.experiences:
            for idx, bullet in enumerate(exp.bullet_points):
                content = (
                    f"Work Accomplishment at {exp.company} as {exp.role} ({exp.start_date} - {exp.end_date}):\n"
                    f"{bullet.situation_action_result}\n"
                    f"Technologies & Skills: {', '.join(bullet.skills_demonstrated or exp.tech_stack)}"
                )
                
                # Combine bullet-specific skills with job tech stack
                combined_tech = list(set(exp.tech_stack + bullet.skills_demonstrated))
                
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{exp.id}_bullet_{idx+1}",
                        source_type="experience",
                        title=f"{exp.role} at {exp.company}",
                        content=content,
                        tech_stack=combined_tech,
                        domain_tags=exp.domain_tags,
                        metadata={
                            "company": exp.company,
                            "role": exp.role,
                            "dates": f"{exp.start_date} - {exp.end_date}",
                            "location": exp.location
                        }
                    )
                )

        # 3. Project Chunks
        for proj in data.projects:
            content = (
                f"Project: {proj.name} ({proj.tagline})\n"
                f"Category: {proj.category} | Type: {proj.type}\n"
                f"Description: {proj.description}\n"
                f"Technologies Used: {', '.join(proj.tech_stack)}\n"
                f"Key Accomplishments:\n" + "\n".join(f"- {ach}" for ach in proj.key_achievements)
            )
            chunks.append(
                DocumentChunk(
                    chunk_id=f"proj_{proj.id}",
                    source_type="project",
                    title=f"Project: {proj.name}",
                    content=content,
                    tech_stack=proj.tech_stack,
                    domain_tags=[proj.category],
                    metadata={"type": proj.type, "name": proj.name}
                )
            )

        # 4. Skill Matrix Chunks
        for cat in data.skill_categories:
            skills_text = "\n".join(
                f"- {s.name} (Proficiency: {s.proficiency}, Experience: {s.years_experience or 'N/A'} yrs)"
                + (f": {s.evidence}" if s.evidence else "")
                for s in cat.skills
            )
            content = f"Skill Category - {cat.category}:\n{skills_text}"
            tech_list = [s.name for s in cat.skills]
            chunks.append(
                DocumentChunk(
                    chunk_id=f"skill_cat_{cat.category.lower().replace(' ', '_')}",
                    source_type="skill",
                    title=f"Skills: {cat.category}",
                    content=content,
                    tech_stack=tech_list,
                    domain_tags=[cat.category],
                    metadata={"category": cat.category}
                )
            )

        # 5. Strengths & Weaknesses Chunks
        for idx, s in enumerate(data.strengths):
            content = (
                f"Professional Strength: {s.trait}\n"
                f"Description: {s.description}\n"
                + (f"Example Scenario: {s.example_scenario}" if s.example_scenario else "")
            )
            chunks.append(
                DocumentChunk(
                    chunk_id=f"strength_{idx+1}",
                    source_type="strength",
                    title=f"Strength: {s.trait}",
                    content=content,
                    tech_stack=[],
                    domain_tags=["soft_skills", "behavioral"],
                    metadata={"trait": s.trait}
                )
            )

        for idx, w in enumerate(data.weaknesses):
            content = (
                f"Professional Growth Area / Weakness: {w.trait}\n"
                f"Mitigation & Action Strategy: {w.mitigation_strategy}"
            )
            chunks.append(
                DocumentChunk(
                    chunk_id=f"weakness_{idx+1}",
                    source_type="weakness",
                    title=f"Growth Area: {w.trait}",
                    content=content,
                    tech_stack=[],
                    domain_tags=["soft_skills", "behavioral"],
                    metadata={"trait": w.trait}
                )
            )

        return chunks

import os
import yaml
from pathlib import Path
from typing import Union
from src.schema import (
    CareerData, Profile, Experience, Project,
    SkillCategory, Strength, Weakness
)


class DataIngestionLoader:
    """
    Loads personal career YAML files from a directory into a validated CareerData object.
    """

    def __init__(self, data_dir: Union[str, Path]):
        self.data_dir = Path(data_dir)

    def load_all(self) -> CareerData:
        career_data = CareerData()

        # Load profile.yaml
        profile_file = self.data_dir / "profile.yaml"
        if profile_file.exists():
            with open(profile_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data:
                    career_data.profile = Profile(**data)

        # Load experiences.yaml
        exp_file = self.data_dir / "experiences.yaml"
        if exp_file.exists():
            with open(exp_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and "experiences" in data:
                    career_data.experiences = [Experience(**item) for item in data["experiences"]]

        # Load projects.yaml
        proj_file = self.data_dir / "projects.yaml"
        if proj_file.exists():
            with open(proj_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and "projects" in data:
                    career_data.projects = [Project(**item) for item in data["projects"]]

        # Load skills.yaml
        skills_file = self.data_dir / "skills.yaml"
        if skills_file.exists():
            with open(skills_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and "skill_categories" in data:
                    career_data.skill_categories = [SkillCategory(**cat) for cat in data["skill_categories"]]

        # Load strengths.yaml
        strengths_file = self.data_dir / "strengths.yaml"
        if strengths_file.exists():
            with open(strengths_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data:
                    if "strengths" in data:
                        career_data.strengths = [Strength(**s) for s in data["strengths"]]
                    if "weaknesses" in data:
                        career_data.weaknesses = [Weakness(**w) for w in data["weaknesses"]]

        return career_data

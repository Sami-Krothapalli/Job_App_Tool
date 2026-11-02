"""Load the user's private profile.yaml into checked Python objects."""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict


class Section(BaseModel):
    # A misspelled key should fail loudly rather than leave a form answer blank.
    model_config = ConfigDict(extra="forbid")


class Contact(Section):
    first_name: str
    last_name: str
    email: str
    phone: str
    address: str
    city: str
    state: str
    zip: str
    country: str


class Links(Section):
    linkedin: str = ""
    github: str = ""
    website: str = ""


class Work(Section):
    authorized_to_work_in_us: str = ""
    requires_sponsorship: str = ""
    willing_to_relocate: str = ""
    salary_expectation: str = ""


class Demographics(Section):
    gender: str = ""
    race: str = ""
    hispanic_or_latino: str = ""
    veteran_status: str = ""
    disability_status: str = ""


class JobFilters(Section):
    locations: list[str] = []
    needs_sponsorship: bool = False
    sponsorship_not_needed_in: list[str] = []


class Resume(Section):
    name: str
    file: Path
    use_for: str


class Profile(Section):
    contact: Contact
    links: Links
    work: Work
    demographics: Demographics
    consent: bool
    job_filters: JobFilters
    resumes: list[Resume]
    ai_context: str


def load_profile(path: Path) -> Profile:
    profile = Profile.model_validate(yaml.safe_load(path.read_text()))

    for resume in profile.resumes:
        resume.file = path.parent / resume.file
        if not resume.file.exists():
            raise FileNotFoundError(f"Resume '{resume.name}' not found: {resume.file}")

    return profile

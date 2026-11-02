import shutil
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from job_app_tool.profile import load_profile

EXAMPLE = Path(__file__).parent.parent / "profile.example.yaml"


@pytest.fixture
def profile_path(tmp_path):
    """A copy of the example profile with its resume file in place."""
    path = tmp_path / "profile.yaml"
    shutil.copy(EXAMPLE, path)
    (tmp_path / "resumes").mkdir()
    (tmp_path / "resumes" / "software.pdf").touch()
    return path


def edit(path, change):
    data = yaml.safe_load(path.read_text())
    change(data)
    path.write_text(yaml.safe_dump(data))


def test_complete_example_loads(profile_path):
    profile = load_profile(profile_path)

    assert profile.contact.email == "jane@example.com"
    assert profile.work.requires_sponsorship == "No"
    assert profile.consent is True
    assert profile.job_filters.locations == []
    assert profile.resumes[0].name == "software"
    assert "backend" in profile.ai_context


def test_resume_paths_are_relative_to_the_profile(profile_path):
    profile = load_profile(profile_path)

    assert profile.resumes[0].file == profile_path.parent / "resumes" / "software.pdf"


def test_missing_email_names_the_field(profile_path):
    edit(profile_path, lambda data: data["contact"].pop("email"))

    with pytest.raises(ValidationError, match=r"contact\.email"):
        load_profile(profile_path)


def test_missing_resume_file_names_the_path(profile_path):
    (profile_path.parent / "resumes" / "software.pdf").unlink()

    with pytest.raises(FileNotFoundError, match="software.pdf"):
        load_profile(profile_path)

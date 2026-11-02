# Job App Tool

Finds new-grad jobs from `SimplifyJobs/New-Grad-Positions`, applies where it can, and logs every job to Notion.

## Setup

1. Install everything: `uv sync`, then `uv run playwright install chromium`.
2. Copy `profile.example.yaml` to `profile.yaml` and fill it in. Put your resume PDFs in `resumes/`.
3. Copy `.env.example` to `.env` and add your API keys.

`profile.yaml`, `.env`, `resumes/` and `data/` are ignored by git. Keep personal details there, not in this README.

## Tests

`uv run pytest`

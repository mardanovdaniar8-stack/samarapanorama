# Project

Flask app serving an interactive route viewer. IRF files (zip archives) are stored under `routes/` and extracted on demand into `extracted/`.

## Stack
- Python 3.12, Flask
- Dependencies managed with `uv` (`pyproject.toml`)

## Run
- Dev: `uv run python app.py` (port 5000) — configured as the "Start application" workflow.
- Production: `gunicorn --bind=0.0.0.0:5000 app:app` (autoscale deployment).

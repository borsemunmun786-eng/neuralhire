# Shortlist

A local-first resume ranking app with a browser-based recruiting dashboard and a Python HTTP API. It compares resume text with a job description, then ranks candidates using an explainable score: 70% detected role-skill overlap and 30% job-language overlap.

## Run locally

Requires Python 3.10 or newer. No third-party packages are required.

```powershell
python server.py
```

Open http://127.0.0.1:8000. Use **Load example** to load six fictional, named resumes from `data/resumes/`, paste resumes manually, or drop `.txt` resume files into the upload area. The API and static interface are served by the same local process.

## API

`POST /api/rank`

```json
{
  "jobDescription": "Python engineer with AWS experience...",
  "candidates": [
    {"name": "Maya Chen", "resume": "Python, AWS, and API development..."}
  ]
}
```

The response contains an ordered candidate list, score, matched and missing skills, keyword evidence, and detected role skills. Requests support up to 200 candidates and 2 MB. `GET /api/health` reports service status.

`GET /api/demo` returns the bundled sample job description and candidate dataset.

## Test

```powershell
python -m unittest discover -s tests -v
```

## Ranking notes

The scorer is a transparent baseline, not a hiring decision or a validated selection model. It only analyzes supplied text and a small editable skill vocabulary. It does not parse PDF or Word files, infer experience levels, or score demographic/protected attributes. Review candidates in context and validate any ranking method before using it in employment decisions.
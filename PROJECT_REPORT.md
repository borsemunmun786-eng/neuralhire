# AI Resume Ranking System

## Project Overview

Shortlist is a local-first resume screening prototype. A recruiter provides a job description and candidate resume text; the system compares the text, ranks the candidates, and shows evidence behind each score.

## Objectives

- Reduce the time needed to compare a group of resumes against one role.
- Make the ranking criteria visible and consistent.
- Keep submitted resume text on the recruiter's computer during analysis.
- Present matched skills, missing role skills, keyword signals, and an ordered shortlist.

## Technology

- Frontend: HTML, CSS, and JavaScript
- Backend: Python standard-library HTTP server and JSON API
- Storage: none; ranking results exist only in the current browser session
- Dependencies: none

## How It Works

1. The recruiter enters a job description and adds resume text manually or from `.txt` files.
2. The API detects recognized skills from a built-in vocabulary and identifies job-specific terms.
3. Each resume receives a score based on skill overlap and keyword overlap.
4. The interface sorts candidates by score and displays matched skills, missing skills, and keyword evidence.

The score is calculated as:

`score = 70% x skill-match ratio + 30% x keyword-match ratio`

The result is rounded to a whole-number percentage. When a job description contains no recognized skills or usable keywords, that part contributes zero. Ties are ordered by candidate name.

## Project Structure

```text
aimlproject/
|-- server.py              # Static web server and ranking API
|-- public/
|   |-- index.html         # Recruiter dashboard
|   |-- app.css            # Responsive interface styles
|   `-- app.js             # Candidate entry and results UI
|-- tests/
|   `-- test_ranking.py    # Ranking behavior tests
|-- README.md              # Setup and API usage
`-- PROJECT_REPORT.md     # Submission overview
```

## Run and Test

From the project folder, run:

```powershell
python server.py
```

Open `http://127.0.0.1:8000`. Select **Load example** to populate a sample job and three resumes, then select **Rank candidates**.

Run the tests with:

```powershell
python -m unittest discover -s tests -v
```

## Limitations and Responsible Use

This prototype uses transparent text matching, not a trained or validated employment model. It recognizes a limited skill vocabulary, accepts plain text rather than PDF/DOCX files, and does not evaluate context, seniority, or equivalent experience. Scores must not be used as an automated hiring decision; a human should review every application. The system does not use demographic or protected attributes.
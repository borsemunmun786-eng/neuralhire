import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).parent
PUBLIC_DIR = ROOT / "public"
PORT = 8000
DATA_DIR = ROOT / "data"
RESUMES_DIR = DATA_DIR / "resumes"

SKILL_TERMS = {
    # General engineering
    "python", "javascript", "typescript", "react", "node.js", "sql", "postgresql",
    "mongodb", "aws", "azure", "gcp", "docker", "kubernetes", "fastapi", "django",
    "flask", "pandas", "scikit-learn", "data analysis", "excel", "tableau", "power bi",
    "figma", "product management", "project management", "agile", "scrum", "leadership",
    "salesforce", "marketing", "seo", "accounting", "financial modeling", "communication",
    "java", "c++", "git", "rest api", "linux", "spark", "airflow", "redis", "html", "css",
    # Core ML / AI
    "machine learning", "deep learning", "nlp", "pytorch", "tensorflow",
    "supervised learning", "unsupervised learning", "reinforcement learning",
    "neural network", "convolutional neural network", "recurrent neural network",
    "lstm", "transformer", "attention mechanism", "bert", "gpt", "t5", "llm",
    "large language model", "generative ai", "diffusion model", "gan",
    "feature engineering", "hyperparameter tuning", "model evaluation",
    "cross-validation", "gradient boosting", "xgboost", "lightgbm", "catboost",
    "random forest", "svm", "logistic regression", "linear regression",
    "dimensionality reduction", "pca", "clustering", "k-means", "anomaly detection",
    "time series", "computer vision", "object detection", "image segmentation",
    "speech recognition", "text classification", "named entity recognition",
    "sentiment analysis", "question answering", "summarization", "embedding",
    "vector database", "faiss", "pinecone", "weaviate", "chroma",
    "mlflow", "wandb", "dvc", "model registry", "model serving", "triton",
    "hugging face", "transformers", "datasets", "tokenizer", "fine-tuning",
    "prompt engineering", "few-shot learning", "zero-shot learning",
    "transfer learning", "knowledge distillation", "quantization", "onnx",
    "cuda", "gpu", "tpu", "accelerate", "deepspeed", "lora", "qlora",
    "retrieval augmented generation", "rag", "semantic search", "reranking",
    "knowledge graph", "ontology",
    # Agentic AI
    "agentic ai", "ai agent", "autonomous agent", "multi-agent", "agent framework",
    "langchain", "langgraph", "llamaindex", "autogen", "crewai", "semantic kernel",
    "tool use", "function calling", "tool calling", "tool selection",
    "planning", "reasoning", "chain of thought", "react agent", "reflection",
    "self-correction", "self-refinement", "memory management", "agent memory",
    "short-term memory", "long-term memory", "episodic memory",
    "task decomposition", "subagent", "orchestration", "workflow automation",
    "human-in-the-loop", "hitl", "agent evaluation", "agent benchmarking",
    "openai assistants", "openai functions", "openai tools",
    "anthropic claude", "tool result", "structured output",
}

# AI/ML concept taxonomy used for depth analysis
AI_ML_CONCEPTS = {
    "foundations": {
        "supervised learning", "unsupervised learning", "reinforcement learning",
        "neural network", "gradient boosting", "logistic regression", "linear regression",
        "random forest", "svm", "clustering", "k-means", "pca",
    },
    "deep_learning": {
        "deep learning", "convolutional neural network", "recurrent neural network",
        "lstm", "transformer", "attention mechanism", "bert", "gpt", "t5",
        "diffusion model", "gan", "cuda", "gpu",
    },
    "llm_and_genai": {
        "llm", "large language model", "generative ai", "hugging face", "fine-tuning",
        "lora", "qlora", "prompt engineering", "few-shot learning", "zero-shot learning",
        "quantization", "onnx", "deepspeed", "accelerate",
    },
    "rag_and_retrieval": {
        "retrieval augmented generation", "rag", "semantic search", "vector database",
        "faiss", "pinecone", "weaviate", "chroma", "embedding", "reranking",
        "knowledge graph",
    },
    "agentic_ai": {
        "agentic ai", "ai agent", "autonomous agent", "multi-agent", "agent framework",
        "langchain", "langgraph", "llamaindex", "autogen", "crewai", "semantic kernel",
        "tool use", "function calling", "tool calling", "planning", "reasoning",
        "chain of thought", "react agent", "reflection", "self-correction",
        "task decomposition", "subagent", "orchestration", "human-in-the-loop",
        "agent memory", "memory management", "openai assistants", "openai functions",
        "openai tools", "structured output",
    },
    "mlops": {
        "mlflow", "wandb", "dvc", "model registry", "model serving", "triton",
        "feature engineering", "hyperparameter tuning", "cross-validation",
        "model evaluation", "mlops",
    },
}

# Flat set of all agentic AI terms for quick lookup
AGENTIC_AI_TERMS = AI_ML_CONCEPTS["agentic_ai"]

STOP_WORDS = {
    "about", "after", "also", "and", "are", "because", "been", "being", "both", "build",
    "candidate", "candidates", "company", "demonstrated", "experience", "for", "from", "have",
    "into", "including", "looking", "must", "our", "role", "should", "skills", "strong", "that",
    "their", "this", "through", "using", "very", "will", "with", "work", "years", "your",
}

# ─────────────────────────────────────────────────────────────────────────────
# SmartATS: section detection patterns
# ─────────────────────────────────────────────────────────────────────────────
SECTION_PATTERNS = {
    "contact":     re.compile(r"(?:email|phone|linkedin|github|contact|address|@|\+1)", re.I),
    "summary":     re.compile(r"^\s*(?:summary|profile|objective|about\s+me|overview|professional\s+summary)\s*$", re.I | re.M),
    "education":   re.compile(r"(?:^\s*education\s*$|b\.?s\.?|m\.?s\.?|ph\.?d|bachelor|master|degree|university|college|gpa)", re.I | re.M),
    "experience":  re.compile(r"^\s*(?:experience|work\s+history|employment|career|professional\s+experience|work\s+experience)\s*$", re.I | re.M),
    "skills":      re.compile(r"^\s*(?:skills|technical\s+skills|core\s+skills|competencies|technologies|tools\s+&\s+technologies)\s*$", re.I | re.M),
    "projects":    re.compile(r"^\s*(?:projects|technical\s+projects|portfolio|open.?source|side\s+projects|personal\s+projects)\s*$", re.I | re.M),
    "certifications": re.compile(r"^\s*(?:certifications?|licenses?|credentials?|awards?|achievements?)\s*$", re.I | re.M),
}

# Bullet-point patterns: detect quantified achievements
METRIC_PATTERN = re.compile(r"\d+[\+%xX]|\$\d|\d+[kKmMbB]\b|\d+\s*(?:percent|million|billion|thousand|users|requests|models)", re.I)
ACTION_VERBS = {
    "built", "designed", "developed", "implemented", "deployed", "created", "led", "managed",
    "optimized", "reduced", "increased", "improved", "architected", "engineered", "delivered",
    "launched", "automated", "integrated", "migrated", "scaled", "trained", "fine-tuned",
    "collaborated", "mentored", "researched", "published", "achieved", "established",
}

# Weak verbs that should be strengthened
WEAK_VERBS = {
    "worked on", "helped with", "assisted", "involved in", "participated in",
    "responsible for", "tasked with", "part of", "contributed to",
    "was involved", "had experience", "used", "utilized",
}

# Readability: ideal resume length range
IDEAL_LENGTH_MIN = 400
IDEAL_LENGTH_MAX = 2500


def tokenize(text):
    return set(re.findall(r"[a-z][a-z0-9+#.-]{1,}", text.lower()))


def extract_skills(text):
    lowered = text.lower()
    return sorted(skill for skill in SKILL_TERMS if re.search(r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])", lowered))


# Role-relevant agentic AI criteria: a focused set of distinct capabilities
# (not the full vocabulary) used for scoring so candidates are not penalised
# for every possible framework they haven't named.
_AGENTIC_ROLE_CRITERIA = {
    "planning",           # deliberate multi-step planning
    "tool use",           # using/calling external tools
    "reasoning",          # chain-of-thought / structured reasoning
    "memory management",  # agent memory (short/long term)
    "orchestration",      # coordinating multiple agents/steps
    "reflection",         # self-correction / self-refinement
    "task decomposition", # breaking goals into subtasks
    "human-in-the-loop",  # HITL / oversight
}


def analyze_aiml_depth(resume_text):
    """Return per-category matched AI/ML concepts and an overall depth label.

    Depth is measured by *category breadth* (how many of the 6 AI/ML concept
    categories have at least one match) rather than raw term count, which
    avoids inflating the score by naming many synonyms from one category.

    Agentic AI score is computed against a focused set of role-relevant
    capabilities (_AGENTIC_ROLE_CRITERIA) rather than the full vocabulary.
    """
    lowered = resume_text.lower()
    matched_by_category = {}
    for category, terms in AI_ML_CONCEPTS.items():
        hits = sorted(term for term in terms if re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", lowered))
        if hits:
            matched_by_category[category] = hits

    # Depth is driven by breadth across categories, not sheer term count
    categories_hit = len(matched_by_category)
    total_categories = len(AI_ML_CONCEPTS)
    if categories_hit == 0:
        depth_label = "none"
    elif categories_hit == 1:
        depth_label = "basic"
    elif categories_hit <= 3:
        depth_label = "intermediate"
    elif categories_hit <= 5:
        depth_label = "advanced"
    else:
        depth_label = "expert"

    # Agentic AI score: matched role criteria / total role criteria (capped 0–100)
    all_agentic_hits = set(matched_by_category.get("agentic_ai", []))
    matched_criteria = _AGENTIC_ROLE_CRITERIA & all_agentic_hits
    agentic_score = round(len(matched_criteria) / len(_AGENTIC_ROLE_CRITERIA) * 100)

    return {
        "matchedConcepts": matched_by_category,
        "categoriesHit": categories_hit,
        "totalConceptHits": sum(len(v) for v in matched_by_category.values()),
        "aimlDepth": depth_label,
        "agenticAI": {
            "detected": len(all_agentic_hits) > 0,
            "matchedTerms": sorted(all_agentic_hits),
            "matchedCriteria": sorted(matched_criteria),
            "score": agentic_score,
        },
    }


def rank_candidates(job_description, candidates):
    job_tokens = tokenize(job_description)
    job_skills = extract_skills(job_description)
    keyword_pool = job_tokens - STOP_WORDS - {token for skill in job_skills for token in tokenize(skill)}
    keywords = sorted(keyword_pool, key=lambda word: (-len(word), word))[:12]

    # Detect whether job description itself is agentic-AI-focused
    jd_aiml = analyze_aiml_depth(job_description)
    job_is_agentic = jd_aiml["agenticAI"]["detected"]

    ranked = []

    for candidate in candidates:
        name = str(candidate.get("name", "Candidate")).strip()[:100] or "Candidate"
        resume = str(candidate.get("resume", ""))[:50000]
        resume_tokens = tokenize(resume)
        resume_skills = extract_skills(resume)
        matched_skills = [skill for skill in job_skills if skill in resume_skills]
        missing_skills = [skill for skill in job_skills if skill not in resume_skills]
        matched_keywords = [word for word in keywords if word in resume_tokens]

        skill_score = len(matched_skills) / len(job_skills) if job_skills else 0
        keyword_score = len(matched_keywords) / len(keywords) if keywords else 0

        aiml_depth = analyze_aiml_depth(resume)

        # If the job description mentions agentic AI, blend an agentic-AI factor
        # into the composite score (replaces a portion of the keyword component)
        # so the final result always stays within 0–100.
        if job_is_agentic:
            agentic_factor = aiml_depth["agenticAI"]["score"] / 100
            # 60% skill match · 20% keywords · 20% agentic capability
            raw = 0.60 * skill_score + 0.20 * keyword_score + 0.20 * agentic_factor
        else:
            raw = 0.70 * skill_score + 0.30 * keyword_score
        score = min(100, round(raw * 100))
        ranked.append({
            "name": name,
            "score": score,
            "matchedSkills": matched_skills,
            "missingSkills": missing_skills,
            "matchedKeywords": matched_keywords[:6],
            "resumeLength": len(resume),
            "aimlDepth": aiml_depth["aimlDepth"],
            "aimlConcepts": aiml_depth["matchedConcepts"],
            "agenticAI": aiml_depth["agenticAI"],
        })

    ranked.sort(key=lambda item: (-item["score"], item["name"].casefold()))
    for index, candidate in enumerate(ranked, start=1):
        candidate["rank"] = index
    return {
        "candidates": ranked,
        "jobSkills": job_skills,
        "analyzed": len(ranked),
        "jobAimlDepth": jd_aiml["aimlDepth"],
        "jobAgenticAI": jd_aiml["agenticAI"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# SmartATS: resume structure extraction
# ─────────────────────────────────────────────────────────────────────────────

def detect_sections(text):
    """Detect which standard resume sections are present."""
    found = {}
    for section, pattern in SECTION_PATTERNS.items():
        found[section] = bool(pattern.search(text))
    return found


def extract_bullets(text):
    """Extract bullet point lines from the resume text."""
    lines = text.split("\n")
    bullets = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^[-•*▸►‣◦]\s+.{15,}", stripped):
            bullets.append(stripped.lstrip("-•*▸►‣◦ ").strip())
        elif re.match(r"^[A-Z][a-z]+\w+.{20,}", stripped) and any(
            stripped.lower().startswith(v) for v in ACTION_VERBS
        ):
            bullets.append(stripped)
    return bullets[:40]  # cap at 40 bullets


def score_bullet(bullet):
    """Return a quality assessment for a single bullet point."""
    has_metric = bool(METRIC_PATTERN.search(bullet))
    words = bullet.lower().split()
    has_action = words[0] if words and words[0] in ACTION_VERBS else None
    is_weak = any(w in bullet.lower() for w in WEAK_VERBS)
    length_ok = 20 <= len(bullet) <= 180
    return {
        "text": bullet,
        "hasMetric": has_metric,
        "hasActionVerb": bool(has_action),
        "isWeak": is_weak,
        "lengthOk": length_ok,
        "quality": (
            "strong" if (has_metric and has_action and not is_weak and length_ok)
            else "weak" if (is_weak or not has_action or not length_ok)
            else "average"
        ),
    }


def suggest_improvement(bullet):
    """
    Suggest a stronger rewrite of a weak bullet — rule-based, never fabricates metrics.
    Strategy:
      1. Replace weak openers with action verbs.
      2. Append guidance to add a metric if none exists.
    """
    improved = bullet

    # Replace weak openers
    replacements = [
        (r"(?i)^(?:was )?responsible for\s+", "Led "),
        (r"(?i)^(?:was )?tasked with\s+", "Executed "),
        (r"(?i)^(?:was )?involved in\s+", "Contributed to "),
        (r"(?i)^participated in\s+", "Collaborated on "),
        (r"(?i)^(?:helped|assisted)\s+(?:with\s+)?", "Supported "),
        (r"(?i)^worked on\s+", "Developed "),
        (r"(?i)^(?:had experience|utilized|used)\s+(?:with\s+)?", "Applied "),
        (r"(?i)^part of\s+", "Member of team that "),
        (r"(?i)^contributed to\s+", "Drove "),
    ]
    for pattern, repl in replacements:
        new = re.sub(pattern, repl, improved, count=1)
        if new != improved:
            improved = new[0].upper() + new[1:] if new else new
            break

    # If it doesn't end with metric guidance and has no number, add a note
    has_metric = bool(METRIC_PATTERN.search(improved))
    note = ""
    if not has_metric:
        note = " [Add a measurable outcome, e.g. 'reducing latency by X%' or 'serving N users']"

    return (improved + note).strip()


def analyze_readability(text):
    """Score document readability: length, structure, density, and heading presence.

    Four sub-scores (weighted):
      - Length score   (35%) – word count within the ideal 400–2500 word range
      - Structure score(30%) – bullet density as a proxy for structured formatting
      - Density score  (20%) – average words per line (lower = tighter, more scannable)
      - Heading score  (15%) – whether the resume contains recognised section headings
    """
    word_count = len(text.split())
    char_count = len(text)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    line_count = len(lines)
    bullet_lines = sum(1 for l in lines if re.match(r"^[-•*▸►‣◦]", l))
    avg_words = word_count / max(line_count, 1)
    bullet_density = bullet_lines / max(line_count, 1)

    length_score = (
        100 if IDEAL_LENGTH_MIN <= word_count <= IDEAL_LENGTH_MAX
        else max(0, 100 - abs(word_count - IDEAL_LENGTH_MIN) // 5)
        if word_count < IDEAL_LENGTH_MIN
        else max(0, 100 - (word_count - IDEAL_LENGTH_MAX) // 10)
    )
    structure_score = min(100, round(bullet_density * 200))
    density_score = 100 if avg_words <= 18 else max(0, 100 - round((avg_words - 18) * 5))

    # Heading score: reward presence of recognised section headings
    detected = detect_sections(text)
    required_headings = ["contact", "education", "experience", "skills"]
    optional_headings = ["summary", "projects", "certifications"]
    req_found = sum(1 for s in required_headings if detected.get(s))
    opt_found = sum(1 for s in optional_headings if detected.get(s))
    heading_score = round((req_found / len(required_headings)) * 70 + (opt_found / len(optional_headings)) * 30)

    readability = round(
        length_score * 0.35
        + structure_score * 0.30
        + density_score * 0.20
        + heading_score * 0.15
    )

    return {
        "wordCount": word_count,
        "charCount": char_count,
        "lineCount": line_count,
        "bulletLines": bullet_lines,
        "avgWordsPerLine": round(avg_words, 1),
        "bulletDensity": round(bullet_density * 100),
        "lengthScore": length_score,
        "structureScore": structure_score,
        "densityScore": density_score,
        "headingScore": heading_score,
        "readabilityScore": readability,
        "lengthLabel": (
            "Too short" if word_count < IDEAL_LENGTH_MIN
            else "Too long" if word_count > IDEAL_LENGTH_MAX
            else "Ideal"
        ),
    }


def compute_ats_score(resume_text, job_description):
    """
    Estimated ATS compatibility score broken into three sub-scores.
    This is a heuristic approximation — not the output of any specific ATS platform.

      - Keyword Coverage     (50%) – how many job skills appear in the resume
      - Section Completeness (30%) – presence of key resume sections
      - Readability          (20%) – document length, structure, density, headings
    """
    # 1. Keyword coverage
    job_skills = extract_skills(job_description)
    resume_skills = extract_skills(resume_text)
    matched = [s for s in job_skills if s in resume_skills]
    missing = [s for s in job_skills if s not in resume_skills]
    keyword_score = round(len(matched) / len(job_skills) * 100) if job_skills else 0

    # bonus keyword tokens
    job_tokens = tokenize(job_description)
    resume_tokens = tokenize(resume_text)
    keyword_pool = job_tokens - STOP_WORDS - {t for s in job_skills for t in tokenize(s)}
    bonus_kws = sorted(keyword_pool, key=lambda w: (-len(w), w))[:15]
    matched_bonus = [w for w in bonus_kws if w in resume_tokens]
    bonus_score = round(len(matched_bonus) / len(bonus_kws) * 100) if bonus_kws else 0

    # blend: 70% hard skills, 30% keyword bonus
    keyword_coverage = round(0.7 * keyword_score + 0.3 * bonus_score)

    # 2. Section completeness
    sections = detect_sections(resume_text)
    required = ["contact", "education", "experience", "skills"]
    recommended = ["summary", "projects", "certifications"]
    req_found = sum(1 for s in required if sections.get(s))
    rec_found = sum(1 for s in recommended if sections.get(s))
    section_score = round((req_found / len(required)) * 70 + (rec_found / len(recommended)) * 30)

    # 3. Readability
    readability = analyze_readability(resume_text)
    readability_score = readability["readabilityScore"]

    # Final ATS score
    ats_score = round(
        keyword_coverage * 0.50 +
        section_score * 0.30 +
        readability_score * 0.20
    )

    return {
        "atsScore": ats_score,
        "breakdown": {
            "keywordCoverage": keyword_coverage,
            "sectionCompleteness": section_score,
            "readability": readability_score,
        },
        "matchedSkills": matched,
        "missingSkills": missing,
        "matchedBonusKeywords": matched_bonus[:8],
        "sections": sections,
        "readability": readability,
    }


def analyze_resume(resume_text):
    """
    Agent Step 1 — Full structural extraction of a single resume.
    Returns: education, skills, projects, experience bullets, contact presence,
             AI/ML depth, readability stats.
    """
    lines = resume_text.split("\n")
    non_empty = [l.strip() for l in lines if l.strip()]

    # Infer name (first non-empty line that is title-cased & short)
    name = ""
    for l in non_empty[:5]:
        if len(l.split()) <= 5 and l.istitle():
            name = l
            break
    if not name and non_empty:
        name = non_empty[0][:60]

    skills = extract_skills(resume_text)
    aiml = analyze_aiml_depth(resume_text)
    sections = detect_sections(resume_text)
    bullets = extract_bullets(resume_text)
    scored_bullets = [score_bullet(b) for b in bullets]
    readability = analyze_readability(resume_text)

    # Shared stop pattern for section-boundary detection (recognises common aliases)
    _SEC_STOP = re.compile(
        r"^\s*(?:education|experience|work\s+history|employment|professional\s+experience|"
        r"work\s+experience|skills|technical\s+skills|core\s+skills|"
        r"projects|technical\s+projects|portfolio|open.?source|"
        r"certifications?|licenses?|credentials?|awards?|achievements?|"
        r"summary|profile|objective|about\s+me|overview)\s*$",
        re.I,
    )

    # Education: grab lines near the education section header
    edu_lines = []
    in_edu = False
    for line in lines:
        stripped = line.strip()
        if re.match(r"(?i)^\s*education\s*$", stripped):
            in_edu = True
            continue
        if in_edu:
            if _SEC_STOP.match(stripped):
                break
            if stripped:
                edu_lines.append(stripped)
    education = edu_lines[:8]

    # Experience: grab lines near the experience section (all common aliases)
    exp_lines = []
    in_exp = False
    for line in lines:
        stripped = line.strip()
        if re.match(r"(?i)^\s*(?:experience|work\s+history|employment|professional\s+experience|work\s+experience)\s*$", stripped):
            in_exp = True
            continue
        if in_exp:
            if _SEC_STOP.match(stripped):
                break
            if stripped:
                exp_lines.append(stripped)
    experience = exp_lines[:20]

    # Projects: lines near projects section (all common aliases)
    proj_lines = []
    in_proj = False
    for line in lines:
        stripped = line.strip()
        if re.match(r"(?i)^\s*(?:projects|technical\s+projects|portfolio|open.?source|side\s+projects|personal\s+projects)\s*$", stripped):
            in_proj = True
            continue
        if in_proj:
            if _SEC_STOP.match(stripped):
                break
            if stripped:
                proj_lines.append(stripped)
    projects = proj_lines[:12]

    return {
        "name": name,
        "skills": skills,
        "education": education,
        "experience": experience,
        "projects": projects,
        "sections": sections,
        "bullets": scored_bullets,
        "readability": readability,
        "aimlDepth": aiml["aimlDepth"],
        "aimlConcepts": aiml["matchedConcepts"],
        "agenticAI": aiml["agenticAI"],
        "wordCount": readability["wordCount"],
    }


def generate_improvements(bullets, missing_skills, resume_text):
    """
    Agent Step 3 — Suggest bullet rewrites and skill gap guidance.
    Returns a list of improvement items (before/after pairs + skill gaps).
    """
    improvements = []

    # Bullet rewrites
    for b in bullets:
        if b["quality"] in ("weak", "average"):
            improved = suggest_improvement(b["text"])
            if improved != b["text"]:
                improvements.append({
                    "type": "bullet",
                    "before": b["text"],
                    "after": improved,
                    "reason": (
                        "Missing action verb" if not b["hasActionVerb"]
                        else "Uses passive/weak language" if b["isWeak"]
                        else "No quantifiable outcome"
                        if not b["hasMetric"] else "Could be stronger"
                    ),
                })

    # Skill gap suggestions (top 10 missing)
    for skill in missing_skills[:10]:
        improvements.append({
            "type": "skill_gap",
            "skill": skill,
            "suggestion": f"Add '{skill}' to your Skills section and mention it in relevant experience bullets if you have this knowledge.",
        })

    # Summary section tip
    sections = detect_sections(resume_text)
    if not sections.get("summary"):
        improvements.append({
            "type": "section",
            "section": "Summary / Profile",
            "suggestion": "Add a 2–3 sentence professional summary at the top that highlights your key expertise and matches the job description keywords.",
        })

    if not sections.get("projects"):
        improvements.append({
            "type": "section",
            "section": "Projects",
            "suggestion": "Add a Projects section showcasing hands-on work. Even personal or open-source projects demonstrate practical skills to ATS systems.",
        })

    if not sections.get("certifications"):
        improvements.append({
            "type": "section",
            "section": "Certifications",
            "suggestion": "Consider adding relevant certifications (e.g. AWS, Google Cloud, Coursera AI/ML) to improve ATS keyword coverage.",
        })

    return improvements[:30]


def run_smartats_agent(resume_text, job_description):
    """
    Agentic AI workflow coordinator:
      Step 1 → analyze_resume (extract structure)
      Step 2 → compute_ats_score (score against JD)
      Step 3 → generate_improvements (suggest rewrites & gaps)
    Returns a unified result object.
    """
    # Step 1: Resume extraction
    analysis = analyze_resume(resume_text)

    # Step 2: ATS scoring against the job description
    ats = compute_ats_score(resume_text, job_description)

    # Step 3: Generate improvement suggestions
    improvements = generate_improvements(
        analysis["bullets"],
        ats["missingSkills"],
        resume_text,
    )

    # Summarize bullet quality counts
    bullet_quality = {"strong": 0, "average": 0, "weak": 0}
    for b in analysis["bullets"]:
        bullet_quality[b["quality"]] = bullet_quality.get(b["quality"], 0) + 1

    return {
        # Meta
        "name": analysis["name"],
        "wordCount": analysis["wordCount"],
        # Step 1 outputs
        "structure": {
            "skills": analysis["skills"],
            "education": analysis["education"],
            "experience": analysis["experience"],
            "projects": analysis["projects"],
            "sections": analysis["sections"],
        },
        # Step 2 outputs
        "atsScore": ats["atsScore"],
        "scoreBreakdown": ats["breakdown"],
        "matchedSkills": ats["matchedSkills"],
        "missingSkills": ats["missingSkills"],
        "matchedKeywords": ats["matchedBonusKeywords"],
        "readability": ats["readability"],
        # AI/ML
        "aimlDepth": analysis["aimlDepth"],
        "aimlConcepts": analysis["aimlConcepts"],
        "agenticAI": analysis["agenticAI"],
        # Step 3 outputs
        "bullets": analysis["bullets"],
        "bulletQuality": bullet_quality,
        "improvements": improvements,
    }


# ─────────────────────────────────────────────────────────────────────────────
# NeuralHire helpers (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

def extract_pdf_text(path: Path) -> str:
    """Extract plain text from a PDF using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            pages.append(text)
        return "\n".join(pages)
    except Exception:
        return ""


def read_resume_file(path: Path) -> str:
    """Read a resume file — supports .pdf and .txt."""
    if path.suffix.lower() == ".pdf":
        return extract_pdf_text(path)
    return path.read_text(encoding="utf-8")


def load_demo_dataset():
    dataset = json.loads((DATA_DIR / "demo_dataset.json").read_text(encoding="utf-8"))
    resumes_root = RESUMES_DIR.resolve()
    candidates = []
    for candidate in dataset["candidates"]:
        resume_path = (DATA_DIR / candidate["file"]).resolve()
        if not resume_path.is_relative_to(resumes_root):
            raise ValueError("Demo resume path must stay inside the resumes directory")
        candidates.append({
            "name": candidate["name"],
            "resume": read_resume_file(resume_path),
        })
    return {"jobDescription": dataset["jobDescription"], "candidates": candidates}


# ─────────────────────────────────────────────────────────────────────────────
# HTTP server
# ─────────────────────────────────────────────────────────────────────────────

class AppHandler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type="application/json; charset=utf-8"):
        encoded = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path == "/api/health":
            self._send(200, json.dumps({"status": "ok"}))
            return
        if path == "/api/demo":
            try:
                demo_data = load_demo_dataset()
            except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
                self._send(500, json.dumps({"error": "Demo dataset is unavailable"}))
                return
            self._send(200, json.dumps(demo_data))
            return
        relative = "index.html" if path in ("/", "/index.html") else path.lstrip("/")
        target = (PUBLIC_DIR / relative).resolve()
        if not target.is_relative_to(PUBLIC_DIR.resolve()) or not target.is_file():
            self._send(404, "Not found", "text/plain; charset=utf-8")
            return
        content_types = {
            ".html": "text/html; charset=utf-8",
            ".css":  "text/css; charset=utf-8",
            ".js":   "text/javascript; charset=utf-8",
        }
        self._send(200, target.read_bytes(), content_types.get(target.suffix, "application/octet-stream"))

    def do_POST(self):
        api_path = urlparse(self.path).path

        # ── NeuralHire: candidate ranking ──────────────────────────────────────
        if api_path == "/api/rank":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 2_000_000:
                    raise ValueError("Request must be between 1 byte and 2 MB")
                payload = json.loads(self.rfile.read(length))
                job_description = str(payload.get("jobDescription", "")).strip()
                candidates = payload.get("candidates", [])
                if len(job_description) < 20:
                    raise ValueError("Add a job description of at least 20 characters")
                if not isinstance(candidates, list) or not candidates:
                    raise ValueError("Add at least one candidate resume")
                if len(candidates) > 200:
                    raise ValueError("Rank up to 200 resumes at a time")
                if any(not isinstance(item, dict) or not str(item.get("resume", "")).strip() for item in candidates):
                    raise ValueError("Every candidate needs resume text")
                result = rank_candidates(job_description, candidates)
                self._send(200, json.dumps(result))
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError, TypeError) as error:
                self._send(400, json.dumps({"error": str(error)}))
            return

        # ── SmartATS: full agentic analysis ────────────────────────────────────
        if api_path == "/api/ats/analyze":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 1_000_000:
                    raise ValueError("Request must be between 1 byte and 1 MB")
                payload = json.loads(self.rfile.read(length))
                resume_text = str(payload.get("resumeText", "")).strip()
                job_description = str(payload.get("jobDescription", "")).strip()
                if len(resume_text) < 50:
                    raise ValueError("Resume must be at least 50 characters")
                if len(job_description) < 20:
                    raise ValueError("Job description must be at least 20 characters")
                result = run_smartats_agent(resume_text, job_description)
                self._send(200, json.dumps(result))
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError, TypeError) as error:
                self._send(400, json.dumps({"error": str(error)}))
            return

        # ── SmartATS: standalone ATS score (no full agent workflow) ────────────
        if api_path == "/api/ats/score":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 1_000_000:
                    raise ValueError("Request must be between 1 byte and 1 MB")
                payload = json.loads(self.rfile.read(length))
                resume_text = str(payload.get("resumeText", "")).strip()
                job_description = str(payload.get("jobDescription", "")).strip()
                if len(resume_text) < 50:
                    raise ValueError("Resume must be at least 50 characters")
                if len(job_description) < 20:
                    raise ValueError("Job description must be at least 20 characters")
                result = compute_ats_score(resume_text, job_description)
                self._send(200, json.dumps(result))
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError, TypeError) as error:
                self._send(400, json.dumps({"error": str(error)}))
            return

        # ── SmartATS: improve a single bullet ──────────────────────────────────
        if api_path == "/api/ats/improve-bullet":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 10_000:
                    raise ValueError("Request too large")
                payload = json.loads(self.rfile.read(length))
                bullet = str(payload.get("bullet", "")).strip()[:500]
                if len(bullet) < 10:
                    raise ValueError("Bullet must be at least 10 characters")
                scored = score_bullet(bullet)
                improved = suggest_improvement(bullet)
                self._send(200, json.dumps({
                    "original": bullet,
                    "improved": improved,
                    "quality": scored["quality"],
                    "hasMetric": scored["hasMetric"],
                    "hasActionVerb": scored["hasActionVerb"],
                    "isWeak": scored["isWeak"],
                }))
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError, TypeError) as error:
                self._send(400, json.dumps({"error": str(error)}))
            return

        self._send(404, json.dumps({"error": "Endpoint not found"}))

    def log_message(self, format, *args):
        print("%s - %s" % (self.address_string(), format % args))



if __name__ == "__main__":
    import os

    PORT = int(os.environ.get("PORT", 8000))

    server = ThreadingHTTPServer(("0.0.0.0", PORT), AppHandler)
    print(f"NeuralHire is running on port {PORT}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        server.server_close()

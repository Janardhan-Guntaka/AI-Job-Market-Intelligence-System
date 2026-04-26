"""
Resume Parser Service
=====================
Extracts plain text, skills, experience level, and likely job titles
from PDF or DOCX resume files.

Dependencies: PyPDF2, python-docx
"""

from __future__ import annotations

import io
import json
import logging
import re
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Known skill taxonomy (extensible)
# ---------------------------------------------------------------------------

SKILL_KEYWORDS = [
    # Languages
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust",
    "Ruby", "PHP", "Kotlin", "Swift", "Scala", "R", "MATLAB", "Bash", "Shell",
    # Web & Frameworks
    "React", "Vue", "Angular", "Next.js", "Svelte", "Django", "Flask", "FastAPI",
    "Spring Boot", "Express", "Node.js", "NestJS", "Laravel", "Rails",
    # Data & ML
    "PyTorch", "TensorFlow", "Scikit-learn", "Keras", "XGBoost", "LightGBM",
    "Pandas", "NumPy", "Spark", "Kafka", "Airflow", "dbt", "Tableau", "Power BI",
    "LangChain", "OpenAI", "HuggingFace", "FAISS", "ChromaDB",
    # Databases
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra",
    "DynamoDB", "SQLite", "Oracle", "Snowflake", "BigQuery", "Redshift",
    # DevOps / Cloud
    "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform", "Ansible",
    "Jenkins", "GitHub Actions", "CircleCI", "Prometheus", "Grafana",
    # Concepts
    "REST API", "GraphQL", "gRPC", "Microservices", "CI/CD", "Agile", "Scrum",
    "TDD", "System Design", "Machine Learning", "Deep Learning", "NLP",
    "Computer Vision", "Data Engineering", "MLOps", "DevOps",
    # Tools
    "Git", "Linux", "Jira", "Figma", "Postman",
]

EXPERIENCE_PATTERNS = [
    (r"(\d+)\+?\s*years?\s+(?:of\s+)?(?:professional\s+)?experience", 1),
    (r"(\d+)[\-–](\d+)\s*years?\s+(?:of\s+)?experience", 2),
    (r"over\s+(\d+)\s+years?", 1),
]

SENIOR_SIGNALS = ["senior", "lead", "principal", "staff", "director", "head of", "vp ", "architect"]
ENTRY_SIGNALS = ["junior", "jr.", "associate", "graduate", "intern", "entry-level", "entry level", "fresher"]


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

def _extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract all text from a PDF file."""
    try:
        import PyPDF2  # noqa: PLC0415
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)
    except Exception as exc:
        logger.error("PDF extraction failed: %s", exc)
        raise ValueError(f"Could not read PDF: {exc}") from exc


def _extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract all text from a DOCX file."""
    try:
        from docx import Document  # noqa: PLC0415
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
    except Exception as exc:
        logger.error("DOCX extraction failed: %s", exc)
        raise ValueError(f"Could not read DOCX: {exc}") from exc


def extract_raw_text(file_bytes: bytes, filename: str) -> str:
    """Dispatch to the correct extractor based on file extension."""
    fname = filename.lower()
    if fname.endswith(".pdf"):
        return _extract_text_from_pdf(file_bytes)
    elif fname.endswith((".docx", ".doc")):
        return _extract_text_from_docx(file_bytes)
    elif fname.endswith(".txt"):
        return file_bytes.decode("utf-8", errors="ignore")
    else:
        raise ValueError(f"Unsupported file type: {filename}. Please upload PDF, DOCX, or TXT.")


def extract_skills(text: str) -> List[str]:
    """Extract known skills from resume text using word-boundary matching."""
    found = []
    text_lower = text.lower()
    for skill in SKILL_KEYWORDS:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill)
    # Deduplicate preserving order
    return list(dict.fromkeys(found))


def extract_years_experience(text: str) -> Tuple[int, str]:
    """
    Try to detect years of experience from resume text.
    Returns (years_int, label_string).
    """
    text_lower = text.lower()
    for pattern, group in EXPERIENCE_PATTERNS:
        match = re.search(pattern, text_lower)
        if match:
            try:
                years = int(match.group(group))
                if group == 2:
                    # Range — take the higher bound
                    years = max(int(match.group(1)), int(match.group(2)))
                return years, _years_to_label(years)
            except (ValueError, IndexError):
                continue
    return 0, "Unknown"


def _years_to_label(years: int) -> str:
    if years == 0:
        return "Unknown"
    if years <= 1:
        return "0-1 years"
    if years <= 3:
        return "1-3 years"
    if years <= 5:
        return "3-5 years"
    if years <= 8:
        return "5-8 years"
    return "8+ years"


def infer_experience_level(text: str, years: int = 0) -> str:
    """Infer seniority level from keywords and years."""
    text_lower = text.lower()
    if any(signal in text_lower for signal in SENIOR_SIGNALS):
        return "Senior"
    if any(signal in text_lower for signal in ENTRY_SIGNALS) or years <= 1:
        return "Entry"
    if years <= 3:
        return "Mid"
    if years <= 6:
        return "Senior"
    return "Lead"


def extract_likely_job_titles(text: str) -> List[str]:
    """
    Heuristic extraction of likely target/current job titles from resume.
    Looks for common title patterns near the top of the document.
    """
    common_titles = [
        "Software Engineer", "Software Developer", "Full Stack Developer",
        "Frontend Developer", "Backend Developer", "Data Scientist",
        "Data Engineer", "ML Engineer", "Machine Learning Engineer",
        "DevOps Engineer", "Platform Engineer", "Site Reliability Engineer",
        "Product Manager", "Engineering Manager", "Solutions Architect",
        "Cloud Architect", "Security Engineer", "QA Engineer",
        "Mobile Developer", "iOS Developer", "Android Developer",
        "Web Developer", "Python Developer", "Java Developer",
    ]
    text_lower = text.lower()
    found = []
    for title in common_titles:
        if title.lower() in text_lower:
            found.append(title)
    return found[:5]  # cap at 5 likely titles


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def parse_resume(file_bytes: bytes, filename: str) -> Dict:
    """
    Full resume parse pipeline.

    Returns:
        {
          "raw_text": str,
          "skills": List[str],
          "experience_level": str,
          "years_experience": str,
          "job_titles": List[str],
        }
    """
    raw_text = extract_raw_text(file_bytes, filename)

    if len(raw_text.strip()) < 50:
        raise ValueError("Resume appears to be empty or could not be read. Please check the file.")

    skills = extract_skills(raw_text)
    years_int, years_label = extract_years_experience(raw_text)
    experience_level = infer_experience_level(raw_text, years_int)
    job_titles = extract_likely_job_titles(raw_text)

    logger.info(
        "Resume parsed: %d skills found, %s experience, level=%s",
        len(skills), years_label, experience_level,
    )

    return {
        "raw_text": raw_text,
        "skills": skills,
        "experience_level": experience_level,
        "years_experience": years_label,
        "job_titles": job_titles,
    }

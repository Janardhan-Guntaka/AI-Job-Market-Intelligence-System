"""
RAG Pipeline — Resume-to-Job Matching
======================================
Uses LangChain + FAISS for semantic similarity search across job descriptions.
Then uses GPT-3.5-turbo (or HuggingFace fallback) to generate a concise
"why this job fits you" explanation for each top match.

Environment variables:
  OPENAI_API_KEY   — Required for OpenAI embeddings + GPT explanations
                     If absent, falls back to HuggingFace sentence-transformers
                     and no LLM explanations (keyword score only).

Design:
  1. At match-time, all jobs in DB are embedded into an in-memory FAISS index.
  2. Resume text is used as the query vector.
  3. Top-K similar jobs are retrieved.
  4. For each retrieved job, GPT writes a 1-sentence explanation.
  5. Results are returned sorted by similarity score.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
USE_OPENAI = bool(OPENAI_API_KEY)


# ---------------------------------------------------------------------------
# Lazy import helpers — we don't crash if heavy deps are missing
# ---------------------------------------------------------------------------

def _get_openai_embeddings():
    from langchain_openai import OpenAIEmbeddings  # noqa: PLC0415
    return OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)


def _get_hf_embeddings():
    from langchain_community.embeddings import HuggingFaceEmbeddings  # noqa: PLC0415
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def _get_embeddings():
    if USE_OPENAI:
        try:
            return _get_openai_embeddings()
        except Exception as exc:
            logger.warning("OpenAI embeddings failed (%s), falling back to HuggingFace", exc)
    return _get_hf_embeddings()


# ---------------------------------------------------------------------------
# Keyword scoring fallback (no embeddings needed)
# ---------------------------------------------------------------------------

def _keyword_overlap_score(resume_text: str, job_description: str, job_skills: List[str]) -> float:
    """
    Simple TF/overlap score between resume text and job.
    Returns a 0–1 float.
    """
    resume_lower = resume_text.lower()
    # Score based on matching skills
    if not job_skills:
        return 0.0
    matches = sum(1 for skill in job_skills if skill.lower() in resume_lower)
    return round(matches / len(job_skills), 4)


# ---------------------------------------------------------------------------
# LLM Explanation generator
# ---------------------------------------------------------------------------

def _generate_explanation(
    resume_summary: str,
    job_title: str,
    company: str,
    job_skills: List[str],
    similarity_score: float,
) -> str:
    """
    Uses GPT-3.5-turbo to write a 1-sentence personalized explanation.
    Falls back to a template-based explanation if OpenAI is unavailable.
    """
    if not USE_OPENAI:
        matched_skills = [s for s in job_skills if s.lower() in resume_summary.lower()]
        if matched_skills:
            skills_str = ", ".join(matched_skills[:3])
            return f"Your experience with {skills_str} closely matches what {company} is looking for in this role."
        return f"This {job_title} role at {company} aligns with your background based on overall profile similarity."

    try:
        from openai import OpenAI  # noqa: PLC0415
        client = OpenAI(api_key=OPENAI_API_KEY)

        prompt = (
            f"You are a career coach. Based on this candidate's resume summary:\n"
            f'"{resume_summary[:500]}"\n\n'
            f'Write ONE concise sentence (max 25 words) explaining why the role '
            f'"{job_title}" at "{company}" is a great fit for them. '
            f"The job requires: {', '.join(job_skills[:8])}. "
            f"Be specific and encouraging. Do not start with 'This role' or 'This job'."
        )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    except Exception as exc:
        logger.warning("GPT explanation failed: %s", exc)
        # Template fallback
        matched = [s for s in job_skills if s.lower() in resume_summary.lower()]
        if matched:
            return f"Your {', '.join(matched[:2])} skills align with the requirements at {company}."
        return f"Your profile has strong overlap with this {job_title} position at {company}."


# ---------------------------------------------------------------------------
# FAISS-based semantic matching
# ---------------------------------------------------------------------------

def _build_faiss_index(job_docs: List[dict]):
    """Build an in-memory FAISS vector store from job description documents."""
    from langchain_community.vectorstores import FAISS  # noqa: PLC0415
    from langchain_core.documents import Document  # noqa: PLC0415

    embeddings = _get_embeddings()
    docs = [
        Document(
            page_content=f"{j['title']} at {j['company']}. {j['description'][:500]}",
            metadata={"job_id": j["id"]},
        )
        for j in job_docs
        if j.get("description")
    ]

    if not docs:
        return None, embeddings

    vector_store = FAISS.from_documents(docs, embeddings)
    return vector_store, embeddings


def semantic_match(
    resume_text: str,
    job_docs: List[dict],
    top_k: int = 15,
) -> List[Dict]:
    """
    Perform semantic similarity matching between resume text and job docs.

    Args:
        resume_text: Full parsed resume text.
        job_docs: List of dicts with keys: id, title, company, description, skills.
        top_k: Number of top matches to return.

    Returns:
        List of dicts with job data + `match_score` + `ai_explanation`.
    """
    if not job_docs:
        return []

    try:
        vector_store, _ = _build_faiss_index(job_docs)
    except Exception as exc:
        logger.warning("FAISS index build failed (%s), using keyword fallback", exc)
        vector_store = None

    job_by_id = {j["id"]: j for j in job_docs}
    scored_jobs = []

    if vector_store is not None:
        try:
            results_with_scores = vector_store.similarity_search_with_score(
                resume_text[:2000],  # FAISS works best with concise queries
                k=top_k,
            )
            for doc, distance in results_with_scores:
                job_id = doc.metadata.get("job_id")
                if job_id in job_by_id:
                    # Convert L2 distance to 0–1 similarity score
                    score = round(max(0.0, 1.0 - distance / 4.0), 4)
                    scored_jobs.append((job_by_id[job_id], score))
        except Exception as exc:
            logger.warning("FAISS search failed (%s), using keyword fallback", exc)
            vector_store = None

    if vector_store is None:
        # Keyword fallback: score all jobs, take top_k
        for job in job_docs:
            skills = json.loads(job.get("skills", "[]")) if isinstance(job.get("skills"), str) else job.get("skills", [])
            score = _keyword_overlap_score(resume_text, job.get("description", ""), skills)
            scored_jobs.append((job, score))
        scored_jobs.sort(key=lambda x: x[1], reverse=True)
        scored_jobs = scored_jobs[:top_k]

    # Build final result with AI explanations
    results = []
    # Create a short resume summary for the LLM (first 300 chars of raw text)
    resume_summary = resume_text[:300].replace("\n", " ").strip()

    for job, score in scored_jobs:
        skills = json.loads(job.get("skills", "[]")) if isinstance(job.get("skills"), str) else job.get("skills", [])
        explanation = _generate_explanation(
            resume_summary=resume_summary,
            job_title=job.get("title", ""),
            company=job.get("company", ""),
            job_skills=skills,
            similarity_score=score,
        )
        results.append({
            **job,
            "match_score": score,
            "match_pct": int(score * 100),
            "ai_explanation": explanation,
        })

    return sorted(results, key=lambda x: x["match_score"], reverse=True)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def match_jobs_to_resume(
    resume_text: str,
    resume_skills: List[str],
    db_jobs: List[dict],
    top_k: int = 15,
) -> List[Dict]:
    """
    Main entry point called by the API route.

    Args:
        resume_text: Full extracted text from the uploaded resume.
        resume_skills: List of skills parsed from the resume.
        db_jobs: List of job dicts from the database.
        top_k: How many ranked results to return.

    Returns:
        Ranked list of jobs with match_score and ai_explanation.
    """
    logger.info(
        "Starting job match: %d resume skills, %d candidate jobs, top_k=%d, openai=%s",
        len(resume_skills), len(db_jobs), top_k, USE_OPENAI,
    )

    # Enrich query with skills for better matching
    skill_query = " ".join(resume_skills)
    enriched_query = f"{resume_text[:1500]}\n\nKey skills: {skill_query}"

    results = semantic_match(enriched_query, db_jobs, top_k=top_k)
    logger.info("Matching complete — returning %d results", len(results))
    return results

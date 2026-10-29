
from datetime import datetime
from threading import Lock
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


app = FastAPI(
    title="BrandGuardAI API",
    description="Rule-based brand content review prototype.",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ReviewRequest(BaseModel):
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Brand content to review",
    )


reviews = {}
next_review_id = 1
review_lock = Lock()


def detect_findings(content: str):
    findings = []
    text = content.lower()

    # Rule 1: Guarantee-related claims
    guarantee_phrases = [
        "guarantee",
        "guaranteed",
        "100% results",
        "instant results",
        "risk-free",
        "risk free",
    ]

    if any(phrase in text for phrase in guarantee_phrases):
        findings.append({
            "issue": "Guarantee claim",
            "severity": "Medium",
            "explanation": (
                "A guarantee-related statement needs verification "
                "against approved brand evidence."
            ),
            "suggested_fix": (
                "Check approved terms and conditions and rewrite "
                "the claim if it is not supported."
            ),
            "evidence": [],
            "evidence_status": "No matching reference found",
        })

    # Rule 2: Broad superiority claims
    superiority_phrases = [
        "best in the world",
        "best product",
        "number one",
        "number 1",
        "no. 1",
        "world's best",
        "world’s best",
        "greatest product",
        "the best",
    ]

    if any(phrase in text for phrase in superiority_phrases):
        findings.append({
            "issue": "Unverifiable superiority claim",
            "severity": "Medium",
            "explanation": (
                "A broad superiority claim may require objective "
                "supporting evidence from approved brand sources."
            ),
            "suggested_fix": (
                "Replace the broad claim with a specific, "
                "verifiable benefit supported by evidence."
            ),
            "evidence": [],
            "evidence_status": "No matching reference found",
        })

    # Rule 3: Absolute claims
    absolute_phrases = [
        "always works",
        "works for everyone",
        "100% effective",
        "zero side effects",
        "completely safe",
        "never fails",
    ]

    if any(phrase in text for phrase in absolute_phrases):
        findings.append({
            "issue": "Absolute or unqualified claim",
            "severity": "High",
            "explanation": (
                "An absolute claim may be misleading if it lacks "
                "reliable evidence and appropriate qualifications."
            ),
            "suggested_fix": (
                "Verify the claim with approved evidence and add "
                "necessary limitations or qualifications."
            ),
            "evidence": [],
            "evidence_status": "No matching reference found",
        })

    return findings


@app.get("/")
def home():
    return {
        "message": "BrandGuardAI API is running.",
        "docs": "/docs",
        "review_endpoint": "POST /review",
        "history_endpoint": "GET /history/{review_id}",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/review")
def review_content(request: ReviewRequest):
    global next_review_id

    content = request.content.strip()

    if not content:
        raise HTTPException(
            status_code=422,
            detail="Please paste some content before starting a review.",
        )

    findings = detect_findings(content)

    with review_lock:
        review_id = next_review_id
        next_review_id += 1

        report = {
            "report_type": "BrandGuardAI Review Report",
            "review_id": review_id,
            "created_at": datetime.now().astimezone().isoformat(
                timespec="seconds"
            ),
            "content": content,
            "findings": findings,
            "message": (
                "Potential issues found."
                if findings
                else "No demo-rule matches found. "
                     "Human review is still required."
            ),
            "disclaimer": (
                "Rule-based preliminary review only. Evidence matches "
                "do not prove a claim is true. No detected issue does "
                "not guarantee that content is safe. Human verification "
                "is required."
            ),
        }

        reviews[review_id] = report

    return report


@app.get("/history/{review_id}")
def get_review_history(review_id: int):
    with review_lock:
        report = reviews.get(review_id)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Review not found. Create a review first.",
        )

    return report

@app.get("/history")
def list_review_history():
    with review_lock:
        history = list(reviews.values())

    return {
        "total_reviews": len(history),
        "reviews": history,
    }

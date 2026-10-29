
from datetime import datetime
from threading import Lock
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


app = FastAPI(
    title="BrandGuardAI API",
    description=(
        "Rule-based brand content review with configurable "
        "guidelines, evidence matching, history and report export."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------- REQUEST MODELS --------------------

class ReviewRequest(BaseModel):
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Brand content to review",
    )


class ReferenceMaterial(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=5000)


class GuidelinesRequest(BaseModel):
    approved_claims: List[str] = Field(default_factory=list)
    prohibited_phrases: List[str] = Field(default_factory=list)
    reference_materials: List[ReferenceMaterial] = Field(
        default_factory=list
    )


# -------------------- IN-MEMORY STORAGE --------------------
# Note: Data resets when the server restarts.

reviews = {}
next_review_id = 1

brand_guidelines = {
    "approved_claims": [],
    "prohibited_phrases": [],
    "reference_materials": [],
}

review_lock = Lock()
guidelines_lock = Lock()


# -------------------- TEXT HELPERS --------------------

def contains_phrase(text: str, phrase: str) -> bool:
    phrase = phrase.strip().casefold()
    return bool(phrase) and phrase in text.casefold()


def match_evidence(content: str, references: list):
    """
    Finds exact phrase matches between the submitted content
    and approved reference material.

    A match is not proof that a claim is true.
    """
    matches = []
    normalized_content = content.casefold()

    for reference in references:
        source_text = reference["content"]
        normalized_source = source_text.casefold()

        # Match a complete reference phrase appearing in the content,
        # or submitted content appearing in the reference.
        matched = (
            normalized_content in normalized_source
            or normalized_source in normalized_content
        )

        if matched:
            matches.append({
                "title": reference["title"],
                "matched_text": source_text,
            })

    return matches


# -------------------- REVIEW RULES --------------------

def detect_findings(content: str):
    findings = []
    text = content.casefold()

    with guidelines_lock:
        guidelines = {
            "approved_claims": list(
                brand_guidelines["approved_claims"]
            ),
            "prohibited_phrases": list(
                brand_guidelines["prohibited_phrases"]
            ),
            "reference_materials": list(
                brand_guidelines["reference_materials"]
            ),
        }

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

    # Rule 4: User-configured prohibited phrases
    for phrase in guidelines["prohibited_phrases"]:
        phrase = phrase.strip()

        if contains_phrase(text, phrase):
            findings.append({
                "issue": "Prohibited brand phrase",
                "severity": "High",
                "explanation": (
                    f"The content contains a phrase listed in "
                    f"the configured brand guidelines: '{phrase}'."
                ),
                "suggested_fix": (
                    "Remove or rewrite this phrase according to "
                    "the brand's approved guidelines."
                ),
                "evidence": [],
                "evidence_status": "Matched configured brand rule",
            })

    # Rule 5: Evidence matching against configured references
    evidence_matches = match_evidence(
        content,
        guidelines["reference_materials"],
    )

    if evidence_matches:
        evidence_status = (
            "Matching reference found; manual verification required"
        )
    else:
        evidence_status = "No matching reference found"

    # Attach matched references to detected findings.
    for finding in findings:
        finding["evidence"] = evidence_matches
        finding["evidence_status"] = evidence_status

    # Rule 6: Claims explicitly listed as approved
    approved_matches = [
        claim.strip()
        for claim in guidelines["approved_claims"]
        if contains_phrase(text, claim)
    ]

    for claim in approved_matches:
        findings.append({
            "issue": "Configured approved claim detected",
            "severity": "Informational",
            "explanation": (
                "This phrase matches a claim listed in the "
                "configured approved-claims list. This does not "
                "independently establish that the claim is true."
            ),
            "suggested_fix": (
                "Confirm the claim is used in its approved context "
                "and that supporting evidence is still valid."
            ),
            "evidence": evidence_matches,
            "evidence_status": (
                evidence_status if evidence_matches
                else "Approved-list match only; no reference matched"
            ),
        })

    return findings


# -------------------- BASIC ENDPOINTS --------------------

@app.get("/")
def home():
    return {
        "message": "BrandGuardAI API is running.",
        "version": app.version,
        "docs": "/docs",
        "health": "/health",
        "review_endpoint": "POST /review",
        "history_endpoint": "GET /history/{review_id}",
        "history_list_endpoint": "GET /history",
        "guidelines_endpoint": "/guidelines",
        "report_download_endpoint": "/report/{review_id}/download",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


# -------------------- BRAND GUIDELINES --------------------

@app.get("/guidelines")
def get_guidelines():
    with guidelines_lock:
        return {
            "approved_claims": list(
                brand_guidelines["approved_claims"]
            ),
            "prohibited_phrases": list(
                brand_guidelines["prohibited_phrases"]
            ),
            "reference_materials": list(
                brand_guidelines["reference_materials"]
            ),
        }


@app.put("/guidelines")
def update_guidelines(request: GuidelinesRequest):
    # Limit list sizes and ignore blank phrases.
    if (
        len(request.approved_claims) > 100
        or len(request.prohibited_phrases) > 100
        or len(request.reference_materials) > 100
    ):
        raise HTTPException(
            status_code=422,
            detail="A maximum of 100 items is allowed per list.",
        )

    approved_claims = [
        item.strip()
        for item in request.approved_claims
        if item.strip()
    ]

    prohibited_phrases = [
        item.strip()
        for item in request.prohibited_phrases
        if item.strip()
    ]

    references = [
        item.model_dump()
        for item in request.reference_materials
    ]

    with guidelines_lock:
        brand_guidelines["approved_claims"] = approved_claims
        brand_guidelines["prohibited_phrases"] = prohibited_phrases
        brand_guidelines["reference_materials"] = references

    return {
        "message": "Brand guidelines updated successfully.",
        "approved_claims_count": len(approved_claims),
        "prohibited_phrases_count": len(prohibited_phrases),
        "reference_materials_count": len(references),
        "storage": "in-memory; resets on server restart",
    }


# -------------------- CREATE A REVIEW --------------------

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


# -------------------- REVIEW HISTORY --------------------

@app.get("/history")
def list_review_history():
    with review_lock:
        history = [
            dict(report)
            for report in reviews.values()
        ]

    history.sort(
        key=lambda item: item["review_id"],
        reverse=True,
    )

    return {
        "total_reviews": len(history),
        "reviews": history,
        "storage": "in-memory; resets on server restart",
    }


@app.get("/history/{review_id}")
def get_review_history(review_id: int):
    with review_lock:
        report = reviews.get(review_id)

        if report is not None:
            report = dict(report)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Review not found. Create a review first.",
        )

    return report


# -------------------- DOWNLOAD REPORT --------------------

@app.get("/report/{review_id}/download")
def download_report(review_id: int):
    with review_lock:
        report = reviews.get(review_id)

        if report is not None:
            report = dict(report)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Review not found. Create a review first.",
        )

    filename = f"brandguardai_report_{review_id}.json"

    return JSONResponse(
        content=report,
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            )
        },
    )


from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="BrandGuardAI API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ReviewRequest(BaseModel):
    content: str


@app.get("/")
def home():
    return {
        "message": "BrandGuardAI backend is running!"
    }


@app.post("/review")
@app.post("/review")
def review_content(request: ReviewRequest):
    content = request.content.strip()

    if not content:
        return {
            "findings": [],
            "message": "Please provide content to review."
        }

    findings = []
    lower_content = content.lower()

    risky_phrases = [
        "best product in the world",
        "guaranteed results",
        "100% guaranteed"
    ]

    for phrase in risky_phrases:
        if phrase in lower_content:
            findings.append({
                "issue": phrase,
                "severity": "Medium",
                "explanation": (
                    "This claim may be difficult to verify "
                    "without approved supporting evidence."
                ),
                "suggested_fix": (
                    "Provide approved evidence for this claim, "
                    "or replace it with a specific, verifiable benefit."
                )
            })

    if "guarantee" in lower_content and not any(
        "guarantee" in finding["issue"].lower()
        for finding in findings
    ):
        findings.append({
            "issue": "Guarantee claim",
            "severity": "Medium",
            "explanation": (
                "A guarantee-related statement needs verification "
                "against approved brand evidence."
            ),
            "suggested_fix": (
                "Check the approved terms and conditions, "
                "and rewrite the claim if it is not supported."
            )
        })

    return {
        "findings": findings,
        "message": (
            "Potential issues found."
            if findings
            else "No demo-rule matches found. Human review is still required."
        ),
        "review_type": "Rule-based prototype",
        "human_review_required": True
    }


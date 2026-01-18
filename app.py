from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= HELPERS =================
def extract_text_from_pdf(uploaded_file: UploadFile):
    pdf_bytes = uploaded_file.file.read()
    pdf_stream = io.BytesIO(pdf_bytes)

    text = ""
    with pdfplumber.open(pdf_stream) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text

    return text if text.strip() else "No readable text found"


def calculate_ats_score(resume_text, jd_text):
    resume_words = set(resume_text.lower().split())
    jd_words = set(jd_text.lower().split())

    matched = resume_words.intersection(jd_words)
    score = int((len(matched) / len(jd_words)) * 100) if jd_words else 0

    return {
        "ats_score": min(score, 100),
        "matched_keywords": list(matched)[:10],
        "missing_keywords": list(jd_words - resume_words)[:10],
    }


def ai_analysis_stub(resume_text, jd_text):
    return (
        "AI Feedback:\n"
        "- Your resume matches the job description well.\n"
        "- Consider adding more cloud and deployment-related skills.\n"
        "- Improve bullet points with measurable impact.\n"
        "- Overall profile is suitable for entry-level roles."
    )

# ================= API =================
@app.post("/analyze")
async def analyze_resume(
    resume: UploadFile,
    job_description: str = Form(...)
):
    resume_text = extract_text_from_pdf(resume)
    ats = calculate_ats_score(resume_text, job_description)
    ai_feedback = ai_analysis_stub(resume_text, job_description)

    return {
        "ats_analysis": ats,
        "ai_feedback": ai_feedback,
    }


@app.get("/")
def root():
    return {"status": "AI Resume Analyzer API running"}

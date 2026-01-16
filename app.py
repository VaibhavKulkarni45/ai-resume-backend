from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import os
from openai import OpenAI

# ================= CONFIG =================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # set this in environment
client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= HELPERS =================
def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text


def calculate_ats_score(resume_text, jd_text):
    resume_words = set(resume_text.lower().split())
    jd_words = set(jd_text.lower().split())

    matched = resume_words.intersection(jd_words)
    score = int((len(matched) / len(jd_words)) * 100) if jd_words else 0

    return {
        "ats_score": min(score, 100),
        "matched_keywords": list(matched)[:10],
        "missing_keywords": list(jd_words - resume_words)[:10]
    }


def ai_analysis(resume_text, jd_text):
    prompt = f"""
You are an ATS resume analyzer.

Resume:
{resume_text}

Job Description:
{jd_text}

Give:
1. ATS match percentage
2. Missing skills
3. Resume improvement suggestions
4. Rewrite 2 resume bullet points professionally
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


# ================= API =================
@app.post("/analyze")
async def analyze_resume(
    resume: UploadFile,
    job_description: str = Form(...)
):
    resume_text = extract_text_from_pdf(resume.file)
    ats = calculate_ats_score(resume_text, job_description)
    ai_feedback = ai_analysis(resume_text, job_description)

    return {
        "ats_analysis": ats,
        "ai_feedback": ai_feedback
    }


@app.get("/")
def root():
    return {"status": "AI Resume Analyzer API running"}

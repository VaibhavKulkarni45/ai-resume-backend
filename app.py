from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import io
import os
import openai

# ================= CONFIG =================
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= HELPERS =================
def extract_text_from_pdf(uploaded_file: UploadFile):
    try:
        pdf_bytes = uploaded_file.file.read()
        pdf_stream = io.BytesIO(pdf_bytes)

        text = ""
        with pdfplumber.open(pdf_stream) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text

        if not text.strip():
            return "No readable text found in resume."

        return text

    except Exception as e:
        return f"PDF_READ_ERROR: {str(e)}"


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

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    return response["choices"][0]["message"]["content"]


# ================= API =================
@app.post("/analyze")
async def analyze_resume(
    resume: UploadFile,
    job_description: str = Form(...)
):
    resume_text = extract_text_from_pdf(resume)
    ats = calculate_ats_score(resume_text, job_description)
    ai_feedback = ai_analysis(resume_text, job_description)

    return {
        "ats_analysis": ats,
        "ai_feedback": ai_feedback
    }


@app.get("/")
def root():
    return {"status": "AI Resume Analyzer API running"}

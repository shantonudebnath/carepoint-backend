import os
import pandas as pd

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from dotenv import load_dotenv

import google.generativeai as genai

from database import get_db, LabTest
from my_model import generate_summary_from_report_df


# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()

# -----------------------------
# Configure Gemini
# -----------------------------
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")


# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI(title="Smart Emergency AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# 1️⃣ LAB SUMMARY ENDPOINT
# =====================================================

@app.get("/summary/{patient_id}")
def get_summary(patient_id: str, db: Session = Depends(get_db)):

    result_rows = (
        db.query(LabTest)
        .filter(LabTest.Patient_ID == patient_id)
        .all()
    )

    if not result_rows:
        return {"summary": f"⚠️ No lab report found for Patient ID: {patient_id}"}

    df = pd.DataFrame([
        {
            "Patient_Name": r.Patient_Name,
            "Patient_Age_Years": r.Patient_Age_Years,
            "Patient_Gender": r.Patient_Gender,
            "Report_Title": r.Report_Title,
            "Lab": r.Lab,
            "Department": r.Department,
            "Sample_Type": r.Sample_Type,
            "Sample_Date": str(r.Sample_Date),
            "Report_Date": str(r.Report_Date),
            "Patient_id": r.Patient_ID,
            "Test_Name": r.Test_Name,
            "Result": r.Result,
            "Unit": r.Unit,
            "Reference_Range": r.Reference_Range,
            "Method": r.Method,
        }
        for r in result_rows
    ])

    try:
        summary_text = generate_summary_from_report_df(df)

    except Exception as e:
        return {"summary": f"Model Error: {e}"}

    return {"summary": summary_text}


# =====================================================
# 2️⃣ AI SUGGESTION REQUEST MODEL
# =====================================================

class AISuggestionRequest(BaseModel):
    patient_summary: str
    doctor_notes: str


# =====================================================
# 3️⃣ GEMINI AI SUGGESTION ENDPOINT
# =====================================================

@app.post("/ai-suggestion")
def ai_suggestion(req: AISuggestionRequest):

    prompt = f"""
You are a clinical decision-support assistant for emergency medicine.

Important Rules:
- Do NOT give final diagnosis
- Provide only tentative clinical suggestions
- Focus on emergency stabilization
- Be concise and medically structured

AI LAB SUMMARY:
{req.patient_summary}

DOCTOR OBSERVATION:
{req.doctor_notes}

Provide the following:

1. Immediate risk assessment
2. Possible clinical concerns
3. Suggested immediate supportive actions
4. Medication categories (generic classes only)
5. Disclaimer that final decision is doctor's responsibility
"""

    try:

        response = model.generate_content(prompt)

        return {
            "ai_suggestion": response.text
        }

    except Exception as e:

        return {
            "ai_suggestion": f"Gemini AI error: {str(e)}"
        }
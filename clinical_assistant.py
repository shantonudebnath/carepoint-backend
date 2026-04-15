# clinical_assistant.py

def build_prompt(abnormalities, patient_problem, patient_name):
    abnormal_text = "\n".join(f"- {a}" for a in abnormalities)

    prompt = f"""
Patient Name: {patient_name}

Abnormal laboratory findings:
{abnormal_text}

Current patient problem:
{patient_problem}

Generate output strictly in the format below.

FORMAT:

Patient Name: {patient_name}

Probable Clinical Concerns:
- ...

Recommended Immediate Considerations:
- ...

Suggested Confirmatory Tests:
- ...

Rules:
- Do not mention AI or models
- Do not claim diagnosis
- Do not suggest medications or dosage
- Do not add any extra text
"""
    return prompt


def generate_clinical_insight(abnormalities, patient_problem, patient_name):
    """
    TEMP MOCK RESPONSE
    (Later you can replace with OpenAI / BioGPT / local LLM)
    """

    response = f"""
Patient Name: {patient_name}

Probable Clinical Concerns:
- Possible acute metabolic or cardiovascular stress

Recommended Immediate Considerations:
- Monitor vital signs closely
- Correlate laboratory findings with clinical examination

Suggested Confirmatory Tests:
- ECG
- Repeat relevant laboratory investigations
"""
    return response.strip()

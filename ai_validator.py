"""
AI Photo Standard Auditor Module
Evaluates submission photos against clean baseline standards using Google Gemini.
"""
import streamlit as st
from google import genai
import io
from PIL import Image

def validate_photo_with_ai(baseline_image_bytes, submission_photo_bytes, strictness_level):
    """
    Compares a submission photo against a baseline using Gemini 1.5.
    Returns status ('PASS'/'FAIL') and reasoning.
    """
    # If no baseline is provided, default to PASS per user request
    if not baseline_image_bytes:
        return {
            "status": "PASS",
            "confidence": 1.0,
            "reason": "No baseline reference image assigned. Auto-passed."
        }

    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            return {
                "status": "PASS",
                "confidence": 1.0,
                "reason": "AI Verification skipped (No API key found)."
            }

        client = genai.Client(api_key=api_key)

        # Prepare images for Gemini
        img_baseline = Image.open(io.BytesIO(baseline_image_bytes))
        img_submission = Image.open(io.BytesIO(submission_photo_bytes))

        # Map strictness (1-10) to prompt instructions
        if strictness_level >= 8:
            strictness_prompt = "You must be EXTREMELY STRICT. If there is even a single crumb, speck of grease, or minor difference in cleanliness, you must FAIL the submission."
        elif strictness_level <= 3:
            strictness_prompt = "You should be VERY LOOSE. Only FAIL the submission if the station is visibly trashed, very dirty, or obviously not cleaned at all. Ignore minor details."
        else:
            strictness_prompt = "Use a NORMAL level of strictness. The station should look generally clean and comparable to the reference, but minor, negligible imperfections are okay."

        prompt = f"""
        You are a strict restaurant manager auditing a closing shift.
        I am providing you with two images:
        Image 1: The clean reference standard.
        Image 2: The employee's submitted photo.

        Your job is to compare Image 2 to Image 1 and determine if the employee cleaned the station properly.

        Strictness Level Instruction: {strictness_prompt}

        You must return your response in EXACTLY this format, with no markdown formatting or other words:
        RESULT: PASS or FAIL
        REASON: A one-sentence explanation of why it passed or failed.
        FEEDBACK: If the result is FAIL, provide a highly specific, granular observation of exactly what is dirty or out of place (e.g., "There is a crumb on the left side of the cutting board"). If PASS, say "None".
        """

        # Use gemini-1.5-flash as it is fast and supports multimodal inputs
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=[prompt, img_baseline, img_submission]
        )
        response_text = response.text.strip()

        # Parse response
        status = "FAIL"
        reason = "AI failed to provide a reason."
        feedback = ""

        for line in response_text.split('\n'):
            line = line.strip()
            if line.startswith("RESULT:"):
                result_str = line.replace("RESULT:", "").strip().upper()
                if "PASS" in result_str:
                    status = "PASS"
            elif line.startswith("REASON:"):
                reason = line.replace("REASON:", "").strip()
            elif line.startswith("FEEDBACK:"):
                feedback_str = line.replace("FEEDBACK:", "").strip()
                if feedback_str.lower() != "none":
                    feedback = feedback_str

        return {
            "status": status,
            "confidence": 0.95,
            "reason": reason,
            "feedback": feedback
        }

    except Exception as e:
        return {
            "status": "PASS", # Fail open if API errors out
            "confidence": 0.0,
            "reason": f"AI error occurred, auto-passed: {str(e)}"
        }

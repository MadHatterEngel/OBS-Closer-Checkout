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
    Compares a submission photo against a baseline using Gemini 3.6.
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

        # Use gemini-3.6-flash as it is fast and supports multimodal inputs
        chat = client.chats.create(model='gemini-3.6-flash')
        response = chat.send_message([prompt, img_baseline, img_submission])
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

def validate_bulk_photos_with_ai(tasks_list, station_name, references_dict, submission_bytes_list):
    """
    Takes a list of tasks for a station and a raw list of uploaded photo bytes.
    Uses Gemini to holistically analyze all photos and figure out which photo
    satisfies which task, grading them simultaneously.
    """
    if not submission_bytes_list:
        results = {}
        for t in tasks_list:
            task_key = f"{station_name}_{t['task']}"
            results[task_key] = {
                "status": "FAIL",
                "confidence": 1.0,
                "reason": "No photos were uploaded.",
                "feedback": "Please upload photos of the station."
            }
        return results, {}

    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            # Fake pass for local dev if no key
            results = {}
            fake_photos = {}
            for i, t in enumerate(tasks_list):
                task_key = f"{station_name}_{t['task']}"
                results[task_key] = {
                    "status": "PASS",
                    "confidence": 1.0,
                    "reason": "AI Verification skipped (No API key).",
                    "feedback": "None"
                }
                fake_photos[task_key] = submission_bytes_list[i % len(submission_bytes_list)]
            return results, fake_photos

        client = genai.Client(api_key=api_key)

        # Prepare all images for Gemini
        submission_images = []
        for b in submission_bytes_list:
            submission_images.append(Image.open(io.BytesIO(b)))

        # Build task descriptions
        tasks_text = "Here is the checklist of tasks that needed to be completed:\n"
        for t in tasks_list:
            tasks_text += f"- {t['task']}\n"

        prompt = f"""
        You are a strict restaurant manager auditing a closing shift for the '{station_name}' station.
        I am providing you with {len(submission_images)} photos taken by the employee of their completed station.

        {tasks_text}

        Your job is to look at ALL the photos collectively and determine if EACH task on the checklist was completed properly.
        Because these are bulk photos, you must figure out which photo(s) show the equipment/area for each task.
        If a task requires cleaning a specific item, and that item is NOT visible in ANY of the photos, you must FAIL that task.

        Use a NORMAL level of strictness. The station should look generally clean, but minor, negligible imperfections are okay.

        You must return your response in EXACTLY this format, with one block per task exactly matching the task name:

        TASK: [Exact Task Name]
        RESULT: PASS or FAIL
        REASON: A one-sentence explanation of why it passed or failed.
        FEEDBACK: If the result is FAIL, provide a highly specific observation of what is dirty or missing. If PASS, say "None".
        MATCHED_PHOTO_INDEX: The index (1 to {len(submission_images)}) of the photo that best proves this task. If none prove it, say 1.

        (Repeat this block for every single task on the checklist).
        """

        contents = [prompt] + submission_images

        chat = client.chats.create(model='gemini-3.6-flash')
        response = chat.send_message(contents)
        response_text = response.text.strip()

        # Parse response
        results = {}
        mapped_photos = {}

        # Default all to fail initially
        for t in tasks_list:
            task_key = f"{station_name}_{t['task']}"
            results[task_key] = {
                "status": "FAIL",
                "confidence": 0.0,
                "reason": "AI failed to grade this task.",
                "feedback": "No grading block found in AI response."
            }
            # Give it a random photo by default so it doesn't crash
            mapped_photos[task_key] = submission_bytes_list[0]

        # Very basic parsing
        current_task_key = None

        for line in response_text.split('\n'):
            line = line.strip()
            if line.startswith("TASK:"):
                task_name = line.replace("TASK:", "").strip()
                current_task_key = f"{station_name}_{task_name}"
                if current_task_key in results:
                    results[current_task_key] = {"status": "FAIL", "reason": "", "feedback": ""}
            elif line.startswith("RESULT:") and current_task_key and current_task_key in results:
                result_str = line.replace("RESULT:", "").strip().upper()
                if "PASS" in result_str:
                    results[current_task_key]["status"] = "PASS"
                else:
                    results[current_task_key]["status"] = "FAIL"
            elif line.startswith("REASON:") and current_task_key and current_task_key in results:
                results[current_task_key]["reason"] = line.replace("REASON:", "").strip()
            elif line.startswith("FEEDBACK:") and current_task_key and current_task_key in results:
                fb = line.replace("FEEDBACK:", "").strip()
                if fb.lower() != "none":
                    results[current_task_key]["feedback"] = fb
            elif line.startswith("MATCHED_PHOTO_INDEX:") and current_task_key and current_task_key in results:
                idx_str = line.replace("MATCHED_PHOTO_INDEX:", "").strip()
                try:
                    idx = int(idx_str) - 1
                    if 0 <= idx < len(submission_bytes_list):
                        mapped_photos[current_task_key] = submission_bytes_list[idx]
                except:
                    pass

        return results, mapped_photos

    except Exception as e:
        results = {}
        fake_photos = {}
        for i, t in enumerate(tasks_list):
            task_key = f"{station_name}_{t['task']}"
            results[task_key] = {
                "status": "FAIL",
                "confidence": 0.0,
                "reason": f"AI error occurred: {str(e)}",
                "feedback": ""
            }
            fake_photos[task_key] = submission_bytes_list[0]
        return results, fake_photos

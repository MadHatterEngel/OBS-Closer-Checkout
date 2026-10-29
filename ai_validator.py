"""
AI Photo Standard Auditor Module
Evaluates submission photos against clean baseline standards using Google Gemini.
"""
import streamlit as st
from google import genai
import io
from PIL import Image

def validate_photo_with_ai(baseline_image_bytes, submission_photo_bytes, strictness_level, task_name="the task", task_details=""):
    """
    Evaluates a submission photo using Gemini 3.6.
    If a baseline is provided, it compares the submission to the baseline.
    If no baseline is provided, it evaluates if the task_name was completed based on the photo.
    Returns status ('PASS'/'FAIL') and reasoning.
    baseline_image_bytes can be a single byte string or a list of byte strings.
    submission_photo_bytes can be a single byte string or a list of byte strings.
    """
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            return {
                "status": "PASS",
                "confidence": 1.0,
                "reason": "AI Verification skipped (No API key found)."
            }

        client = genai.Client(api_key=api_key)

        if not isinstance(submission_photo_bytes, list):
            submission_photo_bytes = [submission_photo_bytes]

        img_submissions = [Image.open(io.BytesIO(b)) for b in submission_photo_bytes]

        # Map strictness (1-10) to prompt instructions
        if strictness_level >= 8:
            strictness_prompt = "You must be EXTREMELY STRICT. If there is even a single crumb, speck of grease, or minor difference in cleanliness, you must FAIL the submission."
        elif strictness_level <= 3:
            strictness_prompt = "You should be VERY LOOSE. Only FAIL the submission if the station is visibly trashed, very dirty, or obviously not cleaned at all. Ignore minor details."
        else:
            strictness_prompt = "Use a NORMAL level of strictness. The station should look generally clean, but minor, negligible imperfections are okay."

        details_text = f"Task Details: {task_details}\n" if task_details else ""

        if baseline_image_bytes:
            if not isinstance(baseline_image_bytes, list):
                baseline_image_bytes = [baseline_image_bytes]

            img_baselines = [Image.open(io.BytesIO(b)) for b in baseline_image_bytes]
            prompt = f"""
            You are a strict restaurant manager auditing a closing shift.
            I am providing you with {len(img_baselines) + len(img_submissions)} images:
            Image(s) 1 through {len(img_baselines)}: The clean reference standard(s) for the task "{task_name}". The submission photo MUST look exactly like these references to pass.
            Image(s) {len(img_baselines) + 1} through {len(img_baselines) + len(img_submissions)}: The employee's submitted photo(s).

            {details_text}

            Your job is to strictly compare the employee's submitted photo(s) to the reference standard(s) and determine if the employee cleaned the station properly.
            CRITICAL REFERENCE CHECK: The submitted photo(s) MUST clearly show the exact same workspace, equipment, or area depicted in the reference image(s). If the submitted photo shows a completely different area, or if it is impossible to verify that it is the same area shown in the reference, you MUST FAIL the submission.
            If multiple reference photos are provided, the employee's photo(s) should be compared against all aspects shown in the references.
            If multiple submission photos are provided, they collectively prove the task was completed. Do not just read the task name, look at what the reference image is actually showing you is supposed to be clean or completed.

            Strictness Level Instruction: {strictness_prompt}

            You must return your response in EXACTLY this format, with no markdown formatting or other words:
            RESULT: PASS or FAIL
            REASON: A one-sentence explanation of why it passed or failed.
            FEEDBACK: If the result is FAIL, provide a highly specific, granular observation of exactly what is dirty or out of place (e.g., "There is a crumb on the left side of the cutting board"), or state if the submitted photo does not show the correct area. If PASS, say "None".
            """
            contents = [prompt] + img_baselines + img_submissions
        else:
            prompt = f"""
            You are a strict restaurant manager auditing a closing shift.
            I am providing you with {len(img_submissions)} photo(s) submitted by an employee.

            Your job is to look at the photo(s) and determine if the task "{task_name}" was completed properly.

            {details_text}

            Strictness Level Instruction: {strictness_prompt}

            You must return your response in EXACTLY this format, with no markdown formatting or other words:
            RESULT: PASS or FAIL
            REASON: A one-sentence explanation of why it passed or failed.
            FEEDBACK: If the result is FAIL, provide a highly specific, granular observation of exactly what is dirty or out of place (e.g., "There is a crumb on the left side of the cutting board"). If PASS, say "None".
            """
            contents = [prompt] + img_submissions

        # Use gemini-3.1-flash-lite as it is fast and supports multimodal inputs
        chat = client.chats.create(model='gemini-3.1-flash-lite')
        response = chat.send_message(contents)
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
    satisfies which task, grading them simultaneously against reference images if provided.
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
        import streamlit as st
        from google import genai
        import io
        from PIL import Image

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

        # Prepare all submission images for Gemini
        submission_images = []
        for b in submission_bytes_list:
            submission_images.append(Image.open(io.BytesIO(b)))

        # Prepare reference images and build tasks text
        contents = []
        tasks_text = "Here is the checklist of tasks that needed to be completed:\n"

        has_references = False
        ref_text_block = "Reference Standard Images:\n"

        # We will keep a separate list of images to append to contents
        reference_images = []
        ref_counter = 1

        # Overall strictness calculation
        total_strictness = 0
        strictness_count = 0

        for t in tasks_list:
            task_name = t['task']
            task_details = t.get('details', '')
            task_key = f"{station_name}_{task_name}"

            strictness = 5
            ref_data = references_dict.get(task_key, {})
            if isinstance(ref_data, dict):
                strictness = ref_data.get('strictness', 5)
                ref_bytes_list = ref_data.get('photo_data')
            else:
                ref_bytes_list = None

            total_strictness += strictness
            strictness_count += 1

            task_description_with_details = f"- {task_name}"
            if task_details:
                task_description_with_details += f" (Details: {task_details})"
            tasks_text += task_description_with_details + "\n"

            if ref_bytes_list:
                if not isinstance(ref_bytes_list, list):
                    ref_bytes_list = [ref_bytes_list]
                has_references = True
                for rb in ref_bytes_list:
                    reference_images.append(Image.open(io.BytesIO(rb)))
                    ref_text_block += f"Image {len(submission_images) + ref_counter}: This is a clean reference standard for '{task_name}'. The submission photo MUST look like this reference to pass.\n"
                    ref_counter += 1

        avg_strictness = total_strictness / max(1, strictness_count)

        if avg_strictness >= 8:
            strictness_prompt = "You should be EXTREMELY STRICT. If there is even a single crumb, speck of grease, or minor difference in cleanliness compared to the reference, you must FAIL the submission."
        elif avg_strictness <= 3:
            strictness_prompt = "You should be VERY LOOSE. Only FAIL the submission if the station is visibly trashed, very dirty, or obviously not cleaned at all. Ignore minor details."
        else:
            strictness_prompt = "Use a NORMAL level of strictness. The station should look generally clean, but minor, negligible imperfections are okay."


        prompt = f"""
        You are a strict restaurant manager auditing a closing shift for the '{station_name}' station.
        I am providing you with {len(submission_images)} photos taken by the employee of their completed station (Images 1 through {len(submission_images)}).

        {ref_text_block if has_references else ""}

        {tasks_text}

        Your job is to look at ALL the employee's submitted photos collectively and determine if EACH task on the checklist was completed properly.
        Because these are bulk photos, you must figure out which submitted photo(s) show the equipment/area for each task.
        If a task requires cleaning a specific item, and that item is NOT visible in ANY of the submitted photos, you must FAIL that task.

        If clean reference standard images are provided for a task, you MUST strictly compare the employee's submitted photos against ALL specific reference standards for that task to determine if they cleaned it properly. The submitted photos must satisfy the visual requirements of all references for that task, as well as any specific requirements in the 'Details' text for that task. Do not just read the task name, look at what the reference image is actually showing you is supposed to be clean or completed.
        CRITICAL REFERENCE CHECK: When matching employee photos to a task with a reference standard, the employee photo(s) MUST clearly show the exact same workspace, equipment, or area depicted in the reference image(s). If no submitted photo clearly shows the same area as the reference, you MUST FAIL the task.

        Strictness Level Instruction: {strictness_prompt}

        You must return your response in EXACTLY this format, with one block per task exactly matching the task name:

        TASK: [Exact Task Name]
        RESULT: PASS or FAIL
        REASON: A one-sentence explanation of why it passed or failed.
        FEEDBACK: If the result is FAIL, provide a highly specific observation of what is dirty, missing, or if the submitted photos do not show the correct area. If PASS, say "None".
        MATCHED_PHOTO_INDEXES: A comma-separated list of the indexes (1 to {len(submission_images)}) of the EMPLOYEE photos that best prove this task. If none prove it, say 1.

        (Repeat this block for every single task on the checklist).
        """

        # Put prompt first, then submission images, then reference images
        contents = [prompt] + submission_images + reference_images

        chat = client.chats.create(model='gemini-3.1-flash-lite')
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
            mapped_photos[task_key] = [submission_bytes_list[0]]

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
            elif line.startswith("MATCHED_PHOTO_INDEXES:") and current_task_key and current_task_key in results:
                idx_str = line.replace("MATCHED_PHOTO_INDEXES:", "").strip()
                indexes = []
                for part in idx_str.split(','):
                    try:
                        idx = int(part.strip()) - 1
                        if 0 <= idx < len(submission_bytes_list):
                            indexes.append(idx)
                    except:
                        pass

                if indexes:
                    mapped_photos[current_task_key] = [submission_bytes_list[i] for i in indexes]

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
            fake_photos[task_key] = [submission_bytes_list[0]]
        return results, fake_photos

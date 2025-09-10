from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import openai
import os
import json
from sleep_scoring import calculate_sleep_score
#uvicorn main:app --reload

openai.api_key = os.environ.get("OPENAI_API_KEY")
app = FastAPI()

# Parenting style detail map
PARENTING_STYLE_DETAILS = {
    "crunchy": {
        "name": "Crunchy",
        "description": """Philosophy: Natural, holistic, low-intervention.
Wants: No cry-it-out, no vaccines, cloth diapers, essential oils.
Plan Style: Gentle, slow-paced, organic/natural methods, trust intuition.
Good for: Sleep plans, feeding, potty training with a gentle tone.
Sample Language: “Let’s follow your baby’s natural rhythms and support with organic options.”"""
    },
    "routine-based": {
        "name": "Routine-Based",
        "description": """Philosophy: Structure and consistency = success.
Wants: Clear nap/feeding schedules, predictable plans, measurable progress.
Plan Style: Time-blocked schedules, visual routines, charts.
Good for: Sleep training, toddler behavior, milestone tracking.
Sample Language: “Here’s a structured, step-by-step routine to help your child thrive.”"""
    },
    "attachment-focused": {
        "name": "Attachment-Focused",
        "description": """Philosophy: Emotional bonding over behavior correction.
Wants: Babywearing, co-sleeping, responsive parenting.
Plan Style: Emotion-first, low-separation strategies, parent connection.
Good for: Sleep, tantrums, communication milestones.
Sample Language: “Let’s support emotional safety while gently guiding new habits.”"""
    },
    "modern balanced": {
        "name": "Modern Balanced",
        "description": """Philosophy: Mix of traditional and modern — what works, works.
Wants: Flexible tips, evidence-based but realistic for working moms.
Plan Style: Combination of structure + empathy + tech tools.
Good for: Every plan — this is your mainstream or “default”.
Sample Language: “Here’s a plan that blends gentle steps with practical strategies.”"""
    },
    "high-achiever": {
        "name": "High-Achiever",
        "description": """Philosophy: Wants results — fast, efficient, proven.
Wants: Expert-backed plans, timelines, coaching, tracking.
Plan Style: Goal-based, data-driven, milestone maps.
Good for: Coaching upsell, tracking features, faster transitions.
Sample Language: “We’ll guide you through a proven 3-day method with expert tips and check-ins.”"""
    }
}

# Check for unsafe input
def is_valid_input(specific_answers: dict) -> bool:
    block_keywords = ["code", "test", "api", "python", "java", "debug"]
    flat_text = " ".join(str(v).lower() for v in specific_answers.values())
    return not any(keyword in flat_text for keyword in block_keywords)

# Input model
class ParentingRequest(BaseModel):
    parent_name: str
    child_name: str
    child_age: str
    focus_area: str
    parenting_style: Optional[str] = None
    sleeping_arrangement: Optional[str] = None
    additional_needs: Optional[List[str]] = []
    specific_answers: Optional[dict] = {}

# Output model
class ParentingResponse(BaseModel):
    parenting_plan: dict

@app.post("/generate-parenting-plan", response_model=ParentingResponse)
async def generate_plan(request: ParentingRequest):
    try:
        # If focus is sleep → run scoring logic
        sleep_result = None
        if "sleep" in request.focus_area.lower():
            intake = {
                "child_age": request.child_age,
                "sleeping_arrangement": request.sleeping_arrangement,
                "parent_preference": request.specific_answers.get("parent_preference"),
                "comforting_style": request.specific_answers.get("comforting_style"),
                "temperament": request.specific_answers.get("temperament"),
                "current_issues": request.specific_answers.get("current_issues", []),
                "overrides": request.specific_answers.get("overrides", [])
            }
            raw_result = calculate_sleep_score(intake)
            # Drop score before sending to GPT
            sleep_result = {
                "method": raw_result["method"],
                "recommendations": raw_result["recommendations"]
            }

        # Parenting style description
        style_key = (request.parenting_style or "").lower()
        style_info = PARENTING_STYLE_DETAILS.get(style_key)
        style_description = style_info["description"] if style_info else "No specific parenting style mentioned."

        # Add sleep scoring result to prompt if available
        scoring_text = f"""
        Sleep report suggestions:
        - Recommended Method: {sleep_result['method']}
        - Additional Notes: {sleep_result['recommendations']}
        """ if sleep_result else ""

        prompt = f"""
You are a parenting expert. Produce a **single valid JSON object** only (no backticks, no markdown outside the JSON).
Use the schema exactly as shown below. Bullet lists must be arrays of strings (2–3 bullets per section).
Daily routine must be structured JSON with 6–8 rows, each having "time" and "activity".

RESPONSE JSON SCHEMA (fill all fields):
{{
  "summary": 
    "Write a supportive intro directly to {request.parent_name}, thank them for sharing {request.child_name}'s journey, acknowledge the challenge, reassure their effort, and explain how the plan will gently guide them. Keep it encouraging and personal. (250-300 characters)"
  ,
  "title": "{{plan title with child's name (20-30 characters)}}",
  "focus": "{{focus summary (100-120 characters)}}",
  "goal": "{{goal summary (100-120 characters)}}",
  "method": "{{method summary (300-350 characters)}}",
  "key_points": ["5 concise, actionable bullets, totaling 200-250 characters"],

  "detailed_plan": {{
    "**Heading**": ["3 actionable bullets, 7-10 words each, using {request.child_name}'s name when natural"],
    "**Heading**": ["3 actionable bullets, 7-10 words each"],
    "**Heading**": ["3 actionable bullets, 7-10 words each"],
    "**Avoid**": ["2 to 3 actionable bullets, 7-10 words each"],
    "**Heading**": ["3 actionable bullets, 7-10 words each"]
  }},

  "suggested_path_for_week": {{
    "Step 1 / Day 1-3": ["2-3 specific actions for this stage"],
    "Step 2 / Day 4-6": ["2-3 specific actions for this stage"],
    "Step 3 / Day 7": ["2-3 specific actions for this stage"]
  }},
  
  "daily_routine": {{
    "schedule": [
      {{"time": "07:00 AM", "activity": "Example activity"}},
      ... 6–8 rows total ...
    ],
    "notes": ["optional brief notes about timing or flexibility"]
  }},
  
  "End_notes": 
    "Make the note for parent to support and encouragement, and add to seek help from our Experts Consultants if needed. (300 characters)"
  ,
}}

DETAILS TO USE:
- Parent Name: {request.parent_name}
- Child Name: {request.child_name}
- Child Age: {request.child_age}
- Focus Area: {request.focus_area}
- Sleeping Arrangement: {request.sleeping_arrangement}
- Additional Needs: {", ".join(request.additional_needs or [])}
- Specific Answers: {request.specific_answers}

PARENTING STYLE (tone/approach guidance):
{style_description}

{scoring_text}

HARD REQUIREMENTS:
- Return ONLY the JSON object; no preface/suffix, no code fences.
- Keep arrays within the specified ranges (key_points 3–5 items; each detailed section 2–3 items).
- Avoid placeholders; make items specific and immediately actionable.
- Use {request.child_name}'s name naturally in at least 3 bullets across the plan.
"""

        print(prompt)

        # Call OpenAI
        resp = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        print(resp)
        raw = resp.choices[0].message.content.strip()
        print(raw)
        # print("characters:", len(raw))

        # Parse JSON output
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Model returned invalid JSON")

        return ParentingResponse(parenting_plan=data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
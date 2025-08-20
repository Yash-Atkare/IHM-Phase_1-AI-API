from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import openai
import os
import json
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
        # Validate inputs
        if not is_valid_input(request.specific_answers or {}):
            raise HTTPException(status_code=400, detail="Input contains unrelated content like code/test.")

        style_key = (request.parenting_style or "").lower()
        style_info = PARENTING_STYLE_DETAILS.get(style_key)

        style_description = style_info["description"] if style_info else "No specific parenting style mentioned."

#         prompt = f"""
# You are a parenting expert. Based on the details below, create a clear and supportive parenting plan. 
# The plan should be written in a warm, encouraging tone for the parent, and always use the child’s name.

# ### Report Structure:

# 1. **Summary**  
#    - Supportive intro (encourage the parent).  
#    - Focus (state the main goal).  
#    - Method (how the plan will help).  
#    - Expected Outcome (what the parent can expect if followed consistently).  

# 2. **Sample Daily Routine**  
#    Present as a table (Time | Activity) with activities relevant to the focus area.  

# 3. **Key Points**  
#    Provide 3–5 key techniques or strategies in bullet points (e.g., “Drowsy but awake placement” or “Offer potty before bedtime”).  

# 4. **Detailed Plan Sections**  
#    Create **five sections**, customized to the focus area.  
#    Each section should have:  
#    - A bold heading  
#    - 2–3 bullet points with actionable advice   

# ### Details:
# Parent Name: {request.parent_name}  
# Child Name: {request.child_name}  
# Child Age: {request.child_age}  
# Focus Area: {request.focus_area}  
# Sleeping Arrangement: {request.sleeping_arrangement}  
# Additional Needs: {", ".join(request.additional_needs or [])}  
# Specific Answers: {request.specific_answers}  

# Parenting Style: {style_description}  

# ### Notes:
# - Always use the child’s name in explanations.  
# - Make the plan supportive, practical, and encouraging.  
# - Do not add any unrelated content or introductry text.  
# """

        prompt = f"""
You are a parenting expert. Produce a **single valid JSON object** only (no backticks, no markdown outside the JSON).
Use the schema exactly as shown below. Bullet lists must be arrays of strings (2–3 bullets per section).
Daily routine must be a markdown table with header: "Time | Activity". Include 6–8 rows relevant to the focus area.

RESPONSE JSON SCHEMA (fill all fields):
{{
  "summary": {
    "Supportive intro (encourage the parent),Focus (state the main goal), Method (how the plan will help), Expected Outcome (what the parent can expect if followed consistently). "},
  "daily_routine": {{
    "table_markdown": "| Time | Activity |\\n|---|---|\\n... six to eight rows ...",
    "notes": ["optional brief notes about timing or flexibility"]
  }},
  "key_points": [" 5 concise, actionable bullets"],
  "detailed_plan": {{
    "**Heading**": ["3 actionable bullets, 8–20 words each, using {request.child_name}'s name when natural"],
    "**Heading**": ["3 actionable bullets"],
    "**Heading**": ["3 actionable bullets"],
    "**Avoid**": ["2 to 3 actionable bullets"],
    "**Heading**": ["3 actionable bullets"]
  }}
  "End_notes": {"Make the note for parent to support and encouragement, and add to seek help from our Experts Consultants if needed."},
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

HARD REQUIREMENTS:
- Return ONLY the JSON object; no preface/suffix, no code fences.
- Keep arrays within the specified ranges (key_points 3–5 items; each detailed section 2–3 items).
- Avoid placeholders; make items specific and immediately actionable.
- Use {request.child_name}'s name naturally in at least 3 bullets across the plan.
"""



        # Call OpenAI
        resp = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        print(resp)
        raw = resp.choices[0].message.content.strip()
        print(raw)

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
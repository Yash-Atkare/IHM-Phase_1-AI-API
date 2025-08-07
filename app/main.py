from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import openai
import os

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
    block_keywords = ["code", "script", "test", "api", "python", "java", "debug"]
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
    parenting_plan: str

@app.post("/generate-parenting-plan", response_model=ParentingResponse)
async def generate_plan(request: ParentingRequest):
    try:
        # Validate inputs
        if not is_valid_input(request.specific_answers or {}):
            raise HTTPException(status_code=400, detail="Input contains unrelated content like code/test.")

        style_key = (request.parenting_style or "").lower()
        style_info = PARENTING_STYLE_DETAILS.get(style_key)

        style_description = style_info["description"] if style_info else "No specific parenting style mentioned."

        prompt = f"""
You are a parenting expert. Create a clear, personalized parenting plan in the format below based on the provided details.

### Format:
1. **Summary** (Focus, Method, Expected Outcome)
2. **Sample Daily Routine** (Table format: Time | Activity)
3. **Key Tips by Focus Area** (Bullet points)

### Details:
Parent Name: {request.parent_name}
Child Name: {request.child_name}
Child Age: {request.child_age}
Focus Area: {request.focus_area}
Sleeping Arrangement: {request.sleeping_arrangement}
Additional Needs: {", ".join(request.additional_needs or [])}
Specific Answers: {request.specific_answers}

Parenting Style: {style_description}

Use the child’s name in the plan. Keep the tone supportive and practical. Avoid giving any unrelated output.
"""

        # Call OpenAI API (GPT)
        response = openai.chat.completions.create(
            model="gpt-4o",  # You can also use gpt-3.5-turbo or others
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        answer = response.choices[0].message.content
        return ParentingResponse(parenting_plan=answer)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# sleep_scoring.py

from typing import Dict, Any

def calculate_sleep_score(intake: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate sleep recommendation based on scoring table.
    Intake must include:
        - child_age
        - sleeping_arrangement
        - parent_preference (crying tolerance)
        - comforting_style
        - temperament
        - current_issues
        - overrides
    """

    total_score = 0
    recommendations = []
    method = None

    # STEP 1: Child Age
    age = intake.get("child_age")
    if age in ["0-3 months", "4-6 months"]:
        # No restriction, all methods valid
        pass
    elif age in ["7-12 months", "1-2 years"]:
        pass
    elif age == "3+ years":
        pass

    # STEP 2: Sleeping Arrangement
    sleeping_arrangement = intake.get("sleeping_arrangement")
    if sleeping_arrangement == "bedsharing":
        recommendations.append("Force Gentle only")
    # Open room, sibling room → all valid

    # STEP 3: Parent Preference (crying tolerance)
    parent_pref = intake.get("parent_preference")
    if parent_pref == "no crying":
        total_score -= 2
    elif parent_pref == "some crying":
        total_score -= 1
    elif parent_pref == "quick results":
        total_score += 2

    # STEP 4: Comforting Style
    comforting_style = intake.get("comforting_style")
    if comforting_style == "feed/rock":
        total_score -= 1
    elif comforting_style == "leave alone":
        total_score += 1

    # STEP 5: Child Temperament
    temperament = intake.get("temperament")
    if temperament == "sensitive/anxious":
        total_score -= 2
    elif temperament == "strong-willed":
        total_score += 2

    # STEP 6: Current Sleep Issues
    current_issues = intake.get("current_issues", [])
    for issue in current_issues:
        if issue in ["gentle leaning", "structured issues"]:
            total_score -= 1
        elif issue in ["night waking", "naps short", "regression"]:
            total_score -= 1
        # twins/special → handled in overrides

    # STEP 7: Overrides (force apply)
    overrides = intake.get("overrides", [])
    if "medical" in overrides or "premature" in overrides:
        method = "Gentle / PUPD"
    elif "sensory" in overrides:
        method = "Gentle / No Tears"
    elif "twins_quick" in overrides:
        method = "Ferber / Fading"
    elif "twins_preference" in overrides:
        method = "Force Chair / Override"

    # FINAL: Score Band → Method Match
    if method is None:  # If no overrides
        if total_score <= -2:
            method = "Gentle / PUPD"
        elif -1 <= total_score <= 1:
            method = "Chair / Fading"
        elif total_score >= 2:
            method = "Ferber / Fading"
    print(f"Score: {total_score}, Method: {method}, Recommendations: {recommendations}")
    return {
        "score": total_score,
        "method": method,
        "recommendations": recommendations
    }
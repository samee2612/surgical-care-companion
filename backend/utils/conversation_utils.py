"""
Conversation Utilities
Helper functions for conversation analysis and area detection
"""

from typing import Dict, List, Any

def get_covered_areas(history: List[Dict[str, str]], call_type: str = "initial_clinical_assessment") -> Dict[str, Any]:
    """
    Check which conversation areas have been covered based on call type
    
    Args:
        history: List of conversation turns with role and content
        call_type: Type of call ("preparation" or "initial_clinical_assessment")
    
    Returns:
        Dictionary mapping area names to coverage status and question counts
    """
    if call_type == "preparation":
        # Preparation call areas with question tracking
        covered = {
            "home_safety": {"covered": False, "questions_asked": 0, "questions_answered": 0},
            "equipment_supplies": {"covered": False, "questions_asked": 0, "questions_answered": 0},
            "medical_preparation": {"covered": False, "questions_asked": 0, "questions_answered": 0},
            "support_verification": {"covered": False, "questions_asked": 0, "questions_answered": 0}
        }
        
        current_area = None
        for i, turn in enumerate(history):
            content = turn["content"].lower()
            role = turn["role"]
            
            # Track assistant questions per area
            if role == "assistant":
                # Detect which area the question is about
                # Check equipment/supplies first (more specific keywords)
                equipment_keywords = ["equipment", "supplies", "toilet seat", "grabber", "walker", "crutches", "mobility", "aids", "shower chair", "bath bench", "raised toilet", "grabber tool", "useful tools", "helpful tools", "useful items", "helpful items", "grab bars", "non-slip", "non slip", "mats", "strips", "handrails", "secure"]
                home_safety_keywords = ["home", "safety", "trip", "hazard", "pathway", "lighting", "rug", "obstacle", "space", "recovery space", "clutter", "clear", "walking areas", "well-lit", "well lit"]
                
                # Check equipment/supplies first (more specific keywords)
                if any(word in content for word in equipment_keywords):
                    current_area = "equipment_supplies"
                    covered["equipment_supplies"]["questions_asked"] += 1
                elif any(word in content for word in home_safety_keywords):
                    current_area = "home_safety"
                    covered["home_safety"]["questions_asked"] += 1
                elif any(word in content for word in ["medication", "blood", "thinning", "aspirin", "warfarin", "eliquis", "medical", "clearance", "appointment"]):
                    current_area = "medical_preparation"
                    covered["medical_preparation"]["questions_asked"] += 1
                elif any(word in content for word in ["support", "help", "caregiver", "family", "friend", "someone", "assist", "partner", "spouse", "who will help"]):
                    current_area = "support_verification"
                    covered["support_verification"]["questions_asked"] += 1
            
            # Track user answers for current area
            elif role == "user" and current_area:
                # Check if this is a valid answer (yes, no, or substantive response)
                content_lower = content.lower().strip()
                if (content_lower in ["yes", "no", "y", "n"] or 
                    len(content.split()) > 2):  # More than just yes/no
                    covered[current_area]["questions_answered"] += 1
                    
                    # Mark area as covered if we have 2-3 questions answered
                    if covered[current_area]["questions_answered"] >= 2:
                        covered[current_area]["covered"] = True
                        current_area = None  # Move to next area
        
        # Convert to simple boolean format for backward compatibility
        result = {}
        for area, data in covered.items():
            result[area] = data["covered"]
            result[f"{area}_questions_asked"] = data["questions_asked"]
            result[f"{area}_questions_answered"] = data["questions_answered"]
        
        return result
    else:
        # Clinical assessment areas (default) - keep existing logic
        covered = {
            "surgery_confirmation": False,
            "pain_level": False,
            "activity_limitations": False,
            "support_system": False
        }
        for turn in history:
            content = turn["content"].lower()
            if not covered["surgery_confirmation"] and any(word in content for word in ["surgery", "date", "operation", "scheduled", "upcoming"]) and (
                "confirm" in content or "yes" in content or "right" in content or "correct" in content
            ):
                covered["surgery_confirmation"] = True
            if not covered["pain_level"] and any(word in content for word in ["pain", "1 to 10", "scale", "rate your pain", "how much pain", "8", "7", "6", "5", "4", "3", "2", "1", "9", "10"]):
                covered["pain_level"] = True
            if not covered["activity_limitations"] and any(word in content for word in ["activity", "limit", "walk", "move", "mobility", "stairs", "standing", "daily tasks", "trouble", "difficulty"]):
                covered["activity_limitations"] = True
            if not covered["support_system"] and any(word in content for word in ["support", "help", "caregiver", "family", "friend", "someone", "assist", "partner", "spouse"]) and (
                "who will help" in content or "who will be helping" in content or "who can help" in content or "support person" in content or "caregiver" in content or "family member" in content or "friend" in content or "partner" in content or "spouse" in content or "someone who will" in content or "help you out" in content or "take care of" in content
            ):
                covered["support_system"] = True
        return covered 
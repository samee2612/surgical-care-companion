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
    else: # Initial Clinical Assessment
        coverage = {
            "surgery_date_confirmation": False,
            "feelings_assessment": False,
            "pain_level": False,
            "activity_limitations": False,
            "support_system": False,
        }
        
        assistant_text = " ".join([msg.get("content", "") or "" for msg in history if msg['role'] == 'assistant']).lower()
        user_text = " ".join([msg.get("content", "") or "" for msg in history if msg['role'] == 'user']).lower()

        # More robust checks for Q&A patterns
        if "surgery scheduled for" in assistant_text and ("correct" in assistant_text or "right" in assistant_text):
            if "yes" in user_text or "right" in user_text or "correct" in user_text:
                coverage["surgery_date_confirmation"] = True

        feeling_keywords = ["anxious", "nervous", "worried", "scared", "excited", "concerned", "feeling", "fine", "good", "bad"]
        if "how are you feeling" in assistant_text and any(keyword in user_text for keyword in feeling_keywords):
            coverage["feelings_assessment"] = True

        if "on a scale of 1 to 10" in assistant_text and "pain" in assistant_text:
            if any(char.isdigit() for char in user_text):
                coverage["pain_level"] = True

        if "activities" in assistant_text and ("difficult" in assistant_text or "challenging" in assistant_text):
            # Check if user mentioned any activity (simple heuristic)
            if len(user_text.split()) > 2 and "nothing" not in user_text:
                coverage["activity_limitations"] = True
        
        support_keywords = ["husband", "wife", "friend", "family", "yes", "daughter", "son", "partner", "spouse", "right", "correct", "yep", "sure"]
        if "someone to help" in assistant_text or "who can help" in assistant_text:
            if any(keyword in user_text for keyword in support_keywords):
                coverage["support_system"] = True
    
    return coverage 
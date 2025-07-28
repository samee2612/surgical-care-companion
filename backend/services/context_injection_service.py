"""
Context Injection Service
Converts call contexts into structured prompts for AI conversations.
Handles prompt generation and context formatting for the LLM.
"""

from typing import Dict, List, Any
from dataclasses import asdict
from datetime import datetime

from .call_context_service import CallContext, CallType, ConversationSection


class ContextInjectionService:
    """Service for injecting call context into AI prompts"""
    
    def __init__(self):
        """Initialize the context injection service"""
        self.initial_clinical_assessment_prompt_template = self._build_initial_clinical_assessment_prompt_template()
    
    def generate_llm_prompt(self, call_context: CallContext, is_initial_call: bool = True) -> Dict[str, Any]:
        """Generate LLM prompt with injected context"""
        
        if call_context.call_type == CallType.INITIAL_CLINICAL_ASSESSMENT:
            return self._generate_initial_clinical_assessment_prompt(call_context, is_initial_call)
        elif call_context.call_type == CallType.PREPARATION:
            return self._generate_preparation_prompt(call_context, is_initial_call)
        else:
            return self._generate_default_prompt(call_context, is_initial_call)
    
    def _generate_initial_clinical_assessment_prompt(self, context: CallContext, is_initial_call: bool = True) -> Dict[str, Any]:
        """Generate initial clinical assessment-specific prompt"""
        
        # Extract patient data
        patient = context.patient_data
        s_date = datetime.fromisoformat(patient['surgery_date']) if isinstance(patient['surgery_date'], str) else patient['surgery_date']
        patient['surgery_date_str'] = s_date.strftime('%B %d, %Y')

        if is_initial_call:
            system_prompt = f"""
You are a caring AI healthcare assistant conducting a 3-minute initial clinical assessment call for {patient['name']}'s upcoming knee replacement surgery.

PATIENT: {patient['name']} | Surgery: {patient['surgery_date_str']} ({patient['days_until_surgery']} days away)

5 REQUIRED AREAS (must cover in order, one question at a time):
1. Surgery Date Confirmation
2. Feelings Assessment
3. Pain Level
4. Activity Limitations
5. Support System

STRICT CONVERSATION FLOW:
- Your FIRST task is 'Surgery Date Confirmation'. Ask ONLY: "I have your surgery scheduled for {patient['surgery_date_str']}, is that correct?"
- After they respond, your SECOND task is 'Feelings Assessment'. Ask ONLY: "Thank you. And how are you feeling about the surgery as it approaches?"
- Proceed through the remaining areas ONE BY ONE.
- After the user provides a direct answer for an area, you MUST move to the next area. DO NOT ask clarifying or follow-up questions.

STRICT CONVERSATION RULES:
- After the patient confirms it's a good time to talk, your first response MUST be ONLY this question: "I have your surgery scheduled for {patient['surgery_date_str']}. Is that correct?"
- DO NOT ask for their feelings or anything else in that first question.
- AFTER they confirm the date is correct, your SECOND question MUST be ONLY: "Thank you for confirming. How are you feeling about the surgery as it approaches?"
- Then, proceed through the remaining areas in order.
- Ask ONLY ONE question at a time
- Wait for response before asking next question
- Cover areas in exact order listed above
- NO skipping or combining areas
- NO wrap-up until ALL 4 areas are covered
- Once area answered → move to next area immediately
- NEVER ask about surgery date again after it's confirmed

AUTOMATIC WRAP-UP TRIGGER:
When ALL 4 areas are answered → Use this EXACT script:
"Thank you so much, {patient['name']}. I have all the information I need for now. We'll be in touch with more details as your surgery approaches. Do you have any immediate questions before we finish?"

TONE: Warm but efficient. Get essential info and end call naturally.
"""
        else:
            # History-aware prompt for ongoing conversations with automatic termination
            system_prompt = f"""
You are a caring AI healthcare assistant continuing a 3-minute clinical assessment call with {patient['name']}.

PATIENT: {patient['name']} | Surgery: {patient['surgery_date_str']} ({patient['days_until_surgery']} days away)

CRITICAL CONVERSATION ANALYSIS:
Before responding, analyze conversation history and check off what's been covered:
□ Surgery confirmation (confirmedsurgery date)
□ Feelings before surgery (asked about feelings)
□ Pain level (asked for 1-10 pain rating)
□ Activity limitations (asked what activities are difficult)
□ Support system (asked who will help after surgery)

RESPONSE DECISION TREE:
1. If ALL 4 boxes checked → END CALL with wrap-up script below
2. If any unchecked → Ask about ONLY the next unchecked area
3. NEVER ask about already-covered topics
4. NEVER ask multiple questions in one response
5. NO skipping or combining areas
6. NO wrap-up until ALL 4 areas are covered
7. Ask about each area in exact order
8. NEVER ask about surgery date again if already discussed

WRAP-UP SCRIPT (use when all 4 areas covered):
"Thank you so much, {patient['name']}. I have all the information I need for now. We'll be in touch with more details as your surgery approaches. Do you have any immediate questions before we finish?"

ESCALATION: Only flag if no support system or extreme anxiety (9-10 level).

TONE: Efficient, caring, natural conversation flow without repetition.
"""

        # Build user prompt based on whether this is initial call or ongoing conversation
        if is_initial_call:
            user_prompt = f"""
Begin the initial clinical assessment call with {patient['name']}.

Start with ONLY this greeting:
"Hello {patient['name']}, this is your healthcare assistant calling about your upcoming knee replacement surgery. Is this a good time to talk?"

DO NOT mention the surgery date yet. After they confirm it's a good time, your first question should be to confirm the surgery date.
"""
        else:
            user_prompt = f"""
Continue the clinical assessment conversation with {patient['name']}.

CRITICAL INSTRUCTIONS:
- This is NOT the start of the call - continue from where we left off
- Review conversation history to identify what's already been covered
- Ask ONLY about the next uncovered area from the 4 required areas
- If all 4 areas covered → Use wrap-up script immediately
- ONE question at a time - be conversational and acknowledge their previous responses
- NEVER repeat questions about surgery date if already discussed

Continue with the appropriate next step based on conversation history.
"""

        return {
            "system_prompt": system_prompt.strip(),
            "user_prompt": user_prompt.strip(),
            "context_metadata": {
                "call_type": context.call_type.value,
                "patient_id": patient['patient_id'],
                "days_from_surgery": context.days_from_surgery,
                "estimated_duration": context.estimated_duration_minutes,
                "focus_areas": context.focus_areas,
                "escalation_triggers": context.escalation_triggers
            }
        }
    
    def _generate_preparation_prompt(self, context: CallContext, is_initial_call: bool = True) -> Dict[str, Any]:
        """Generate preparation call-specific prompt"""
        
        # Extract patient data
        patient = context.patient_data
        structure = context.conversation_structure
        
        # Build different system prompts for initial vs ongoing conversations
        if is_initial_call:
            # Streamlined prompt for starting the preparation conversation
            system_prompt = f"""
You are a caring AI healthcare assistant conducting a 5-minute preparation assessment call for {patient['name']}'s upcoming knee replacement surgery.

PATIENT: {patient['name']} | Surgery: {patient['surgery_date']} ({patient['days_until_surgery']} days away)

CALL OBJECTIVE: Weekly preparation check-in covering exactly 4 areas, then wrap-up.

4 REQUIRED AREAS (must cover in order, one question at a time):
1. Home safety and trip hazard removal
2. Equipment and supplies (raised toilet seat, grabber tool)
3. Medical preparation and blood-thinning medications
4. Support system verification

STRICT CONVERSATION RULES:
- Ask ONLY ONE question at a time
- Wait for response before asking next question
- Cover areas in exact order listed above
- Ask EXACTLY 2-3 questions within each area before moving to next area
- NO additional topics or explanations
- Once area has 2-3 questions answered → move to next area immediately
- Focus on practical preparation status
- Track question count per area and ensure thorough coverage

AUTOMATIC WRAP-UP TRIGGER:
When ALL 4 areas are answered → Use this EXACT script:
"Great progress. Your next call will be closer to your surgery date to confirm final logistics."

TONE: Supportive and practical. Focus on preparation readiness and identify any gaps.
"""
        else:
            # History-aware prompt for ongoing conversations with automatic termination
            system_prompt = f"""
You are a caring AI healthcare assistant continuing a 5-minute preparation assessment call with {patient['name']}.

PATIENT: {patient['name']} | Surgery: {patient['surgery_date']} ({patient['days_until_surgery']} days away)

CRITICAL CONVERSATION ANALYSIS:
Before responding, analyze conversation history and check off what's been covered:
□ Home safety and trip hazard removal
□ Equipment and supplies (raised toilet seat, grabber tool)
□ Medical preparation and blood-thinning medications
□ Support system verification

RESPONSE DECISION TREE:
1. If ALL 4 boxes checked → END CALL with wrap-up script below
2. If any unchecked → Ask about ONLY the next unchecked area
3. NEVER ask about already-covered topics
4. NEVER ask multiple questions in one response
5. Ask EXACTLY 2-3 questions per area before moving to next area
6. Focus on practical preparation status

WRAP-UP SCRIPT (use when all 4 areas covered):
"Great progress. Your next call will be closer to your surgery date to confirm final logistics."

ESCALATION: Flag if unsafe home environment, missing medical clearances, equipment not available, or inadequate support system.

TONE: Supportive, practical, focused on preparation readiness.
"""

        # Build user prompt based on whether this is initial call or ongoing conversation
        if is_initial_call:
            user_prompt = f"""
Begin the preparation assessment call with {patient['name']}.

Start with this EXACT greeting:
"Hello {patient['name']}, this is your healthcare assistant calling about your upcoming knee replacement surgery on {patient['surgery_date']}. This is your weekly preparation check-in to make sure everything is ready for your surgery. Is this a good time to talk?"

DO NOT ask any assessment questions yet. Wait for their response to confirm good timing first.
"""
        else:
            user_prompt = f"""
Continue the preparation assessment conversation with {patient['name']}.

CRITICAL INSTRUCTIONS:
- This is NOT the start of the call - continue from where we left off
- Review conversation history to identify what's already been covered
- Ask ONLY about the next uncovered area from the 4 required areas
- If all 4 areas covered → Use wrap-up script immediately
- ONE question only - be conversational and acknowledge their previous responses
- Focus on practical preparation status

Continue with the appropriate next step based on conversation history.
"""

        return {
            "system_prompt": system_prompt.strip(),
            "user_prompt": user_prompt.strip(),
            "context_metadata": {
                "call_type": context.call_type.value,
                "patient_id": patient['patient_id'],
                "days_from_surgery": context.days_from_surgery,
                "estimated_duration": context.estimated_duration_minutes,
                "focus_areas": context.focus_areas,
                "escalation_triggers": context.escalation_triggers
            }
        }
    
    # Removed _generate_education_prompt and all education call handling
    
    def _get_week_specific_structure(self, days_from_surgery: int) -> str:
        """Get detailed conversation structure for specific week"""
        
        if days_from_surgery == -28:  # Week 4
            return """
1. CHECK-IN SINCE ASSESSMENT
   - How are you feeling since our initial clinical assessment conversation?
   - Any new questions or concerns that have come up?
   - What's been on your mind about the surgery?

2. SURGERY PROCEDURE OVERVIEW
   - Explain what happens during knee replacement surgery
   - Timeline: procedure takes 1-2 hours
   - What the surgeon will do (remove damaged parts, place new implant)
   - Address specific concerns they mentioned

3. RECOVERY TIMELINE EXPECTATIONS
   - Hospital stay: typically 2-3 days
   - Home recovery phases: weeks 1-6, months 2-6
   - Return to activities timeline
   - What improvement they can expect

4. ADDRESS SURGERY CONCERNS
   - Common worries and realistic reassurance
   - Success rates and outcomes
   - How this will improve their current pain/limitations

5. NEXT WEEK PREVIEW
   - Explain next week will focus on home preparation
   - What they should start thinking about
   - Any immediate steps they can take
"""
        elif days_from_surgery == -21:  # Week 3
            return """
1. PROGRESS CHECK FROM WEEK 4
   - How did last week's surgery overview feel?
   - Any additional questions about the procedure?
   - Comfort level with surgery decision

2. HOME SAFETY MODIFICATIONS
   - Based on their home assessment from initial clinical assessment
   - Specific recommendations for their living situation
   - Timeline for making changes

3. EQUIPMENT AND SUPPLIES NEEDED
   - Medical equipment (walker, raised toilet seat, etc.)
   - Comfort items and supplies
   - Where to obtain items

4. ACCESSIBILITY PLANNING
   - Bedroom and bathroom setup
   - Stair safety or alternatives
   - Daily living area organization

5. PREPARATION TIMELINE
   - What to do this week vs. next week
   - Priority items vs. nice-to-have
   - Who can help with preparations
"""
        elif days_from_surgery == -14:  # Week 2
            return """
1. HOME PREPARATION PROGRESS CHECK
   - What home modifications have been completed?
   - Any challenges or concerns with preparations?
   - Equipment acquisition status

2. PAIN MANAGEMENT OVERVIEW
   - Types of pain to expect after surgery
   - How post-surgery pain differs from current pain
   - Timeline for pain improvement

3. MEDICATION PLANNING
   - Prescription pain medications
   - Schedule and dosing guidelines
   - Side effects and precautions
   - Integration with current medications

4. NON-MEDICATION STRATEGIES
   - Ice therapy techniques
   - Elevation and positioning
   - Breathing and relaxation techniques
   - Activity pacing

5. PAIN EXPECTATIONS TIMELINE
   - Days 1-7: acute phase
   - Weeks 2-6: improvement phase
   - When to call doctor vs. normal discomfort
"""
        else:  # Week 1 (-7 days)
            return """
1. FINAL PREPARATION CHECK
   - Home setup completion status
   - Pain management plan understanding
   - Any last-minute concerns

2. HOSPITAL ADMISSION PROCESS
   - When and where to arrive
   - What to bring and what to leave home
   - Pre-surgery preparations

3. SURGERY DAY TIMELINE
   - Morning routine and restrictions
   - Family waiting and updates
   - What happens during surgery

4. IMMEDIATE POST-OP EXPECTATIONS
   - Waking up from anesthesia
   - First 24-48 hours in hospital
   - Early mobility and physical therapy

5. DISCHARGE PLANNING OVERVIEW
   - When they'll likely go home
   - Discharge instructions preview
   - Transition to home care
"""
    
    def _format_objectives(self, objectives: list) -> str:
        """Format educational objectives as bullet points"""
        if not objectives:
            return "- Provide relevant educational content\n- Address patient questions and concerns"
        
        return "\n".join([f"- {obj}" for obj in objectives])
    
    def _generate_default_prompt(self, context: CallContext, is_initial_call: bool = True) -> Dict[str, Any]:
        """Generate generic prompt for other call types"""
        
        return {
            "system_prompt": f"You are conducting a {context.call_type.value} call.",
            "user_prompt": "Begin the conversation.",
            "context_metadata": asdict(context)
        }
    
    def _build_initial_clinical_assessment_prompt_template(self) -> str:
        """Build the initial clinical assessment prompt template"""
        # This can be expanded with more sophisticated templating
        return "initial_clinical_assessment_template"
    
    def extract_conversation_data(self, conversation_text: str, call_context: CallContext) -> Dict[str, Any]:
        """Extract structured data from completed conversation"""
        
        if call_context.call_type == CallType.INITIAL_CLINICAL_ASSESSMENT:
            return self._extract_initial_clinical_assessment_data(conversation_text)
        else:
            return {"raw_conversation": conversation_text}
    
    def _extract_initial_clinical_assessment_data(self, conversation_text: str) -> Dict[str, Any]:
        """Extract initial clinical assessment-specific data points from conversation"""
        
        # This would use LLM to parse the conversation and extract structured data
        # For now, return a template of what should be extracted
        return {
            "baseline_assessment": {
                "current_pain_level": None,
                "mobility_limitations": [],
                "current_walking_aids": None,
                "walking_distance": None
            },
            "home_environment": {
                "home_type": None,  # single/multi story
                "entrance_stairs": None,
                "bedroom_location": None,
                "safety_hazards": [],
                "bathroom_accessibility": None
            },
            "support_system": {
                "primary_caregiver": None,
                "overnight_support": None,
                "errand_assistance": [],
                "comfort_asking_help": None
            },
            "medical_status": {
                "chronic_conditions": [],
                "medications": [],
                "last_physical_exam": None,
                "conditions_controlled": None,
                "clearances_needed": []
            },
            "transportation": {
                "surgery_day_transport": None,
                "discharge_transport": None,
                "followup_transport": None,
                "transport_challenges": []
            },
            "overall_assessment": {
                "anxiety_level": None,
                "readiness_concerns": [],
                "escalation_needed": False,
                "escalation_reasons": []
            }
        } 

# Global instance
_context_injection_service = None

def get_context_injection_service() -> ContextInjectionService:
    """Get context injection service instance"""
    global _context_injection_service
    if _context_injection_service is None:
        _context_injection_service = ContextInjectionService()
    return _context_injection_service
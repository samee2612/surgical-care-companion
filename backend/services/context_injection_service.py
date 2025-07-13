"""
Context Injection Service
Converts call contexts into structured prompts for AI conversations.
Handles prompt generation and context formatting for the LLM.
"""

from typing import Dict, List, Any
from dataclasses import asdict

from .call_context_service import CallContext, CallType, ConversationSection


class ContextInjectionService:
    """Service for injecting call context into AI prompts"""
    
    def __init__(self):
        self.enrollment_prompt_template = self._build_enrollment_prompt_template()
    
    def generate_llm_prompt(self, call_context: CallContext, is_initial_call: bool = True) -> Dict[str, Any]:
        """Generate structured prompt for LLM based on call context"""
        
        if call_context.call_type == CallType.ENROLLMENT:
            return self._generate_enrollment_prompt(call_context, is_initial_call)
        elif call_context.call_type == CallType.EDUCATION:
            return self._generate_education_prompt(call_context, is_initial_call)
        else:
            return self._generate_generic_prompt(call_context)
    
    def _generate_enrollment_prompt(self, context: CallContext, is_initial_call: bool = True) -> Dict[str, Any]:
        """Generate enrollment-specific prompt"""
        
        # Extract patient data
        patient = context.patient_data
        structure = context.conversation_structure
        
        # Build the main system prompt
        system_prompt = f"""
You are a caring and professional AI healthcare assistant conducting an enrollment call for {patient['name']}'s upcoming knee replacement surgery scheduled for {patient['surgery_date']}.

CALL PURPOSE: {structure['call_purpose']}

PATIENT INFORMATION:
- Name: {patient['name']}
- Surgery Date: {patient['surgery_date']} ({patient['days_until_surgery']} days from today)
- Current Compliance Score: {patient['current_compliance_score']}
- Primary Physician: {patient['physician']}

CONVERSATION APPROACH:
- Tone: {context.tone} - Be warm, reassuring, and thorough
- Estimated Duration: {context.estimated_duration_minutes} minutes
- Opening: {structure['opening_approach']}

YOUR ROLE:
- Conduct a comprehensive baseline assessment
- Collect critical information for surgery preparation
- Identify potential risks or concerns
- Provide initial education and reassurance
- Schedule next call and explain the process

CONVERSATION STRUCTURE:
You must cover these sections in order:

1. WELCOME & INTRODUCTION
   Purpose: Establish rapport and confirm surgery details
   Key Questions:
   - Start with: "Hello {patient['name']}, this is your healthcare assistant calling about your upcoming knee replacement surgery. Is this a good time to talk?"
   - WAIT for response, then: "Can you confirm your surgery is scheduled for {patient['surgery_date']}?"
   - WAIT for response, then: "How are you feeling about the upcoming procedure?"
   
2. BASELINE MOBILITY ASSESSMENT
   Purpose: Establish current functional status
   Key Questions:
   - "Let's start by understanding your current situation. On a scale of 1-10, how would you rate your knee pain today?"
   - "What daily activities are most difficult for you right now?"
   - "Are you using any walking aids like a cane or walker currently?"
   - "How far can you walk before the pain becomes significant?"
   
3. HOME ENVIRONMENT ASSESSMENT
   Purpose: Evaluate post-surgery safety needs
   Key Questions:
   - "Let's talk about your home setup. Do you live in a single-story home or are there multiple floors?"
   - "Are there stairs to enter your home?"
   - "Where is your bedroom located relative to stairs?"
   - "Do you notice any trip hazards like loose rugs, clutter, or poor lighting?"
   - "Is your bathroom easily accessible from where you'll be recovering?"
   
4. SUPPORT SYSTEM MAPPING
   Purpose: Identify available help and support
   Key Questions:
   - "Who will be your primary helper after surgery?"
   - "Will someone be staying with you for the first few days?"
   - "Do you have family or friends who can help with shopping, cooking, or errands?"
   - "Are you comfortable asking for help when you need it?"
   
5. MEDICAL OPTIMIZATION REVIEW
   Purpose: Ensure medical conditions are controlled
   Key Questions:
   - "Let's review your health conditions. Do you have diabetes, high blood pressure, or heart conditions?"
   - "Are you taking any blood thinners or other medications that might affect surgery?"
   - "When was your last comprehensive physical exam?"
   - "Are all your chronic conditions well-controlled right now?"
   - "Has your surgeon mentioned any medical clearances you need?"
   
6. TRANSPORTATION PLANNING
   Purpose: Ensure safe transportation arrangements
   Key Questions:
   - "How will you get to the hospital on surgery day?"
   - "Who will drive you home after surgery? Remember, you cannot drive yourself."
   - "Do you have reliable transportation for follow-up appointments?"
   - "Are there any transportation challenges we should help you solve?"

ESCALATION TRIGGERS - IMMEDIATELY FLAG AND ESCALATE IF:
- Patient has no support system or inadequate immediate help
- Unsafe home environment with major accessibility issues
- No transportation plan or unreliable arrangements
- Uncontrolled medical conditions or concerning symptoms
- Extreme anxiety or confusion about surgery details

CONVERSATION GUIDELINES:
- CRITICAL: Ask only ONE question at a time and wait for patient response before continuing
- Never ask multiple questions in a single message
- Use active listening and acknowledge their concerns
- Provide reassurance when appropriate
- If they seem anxious, slow down and provide more support
- Take notes on all responses for documentation
- End with summary and next steps

CLOSING APPROACH:
- Summarize key findings and any concerns
- Explain what happens next and when the next call will be
- Provide contact information for urgent questions
- Thank them for their time and cooperation

Remember: This is their first formal interaction with the surgical care team. Set a positive, caring tone while being thorough and professional.
"""

        # Build user prompt based on whether this is initial call or ongoing conversation
        if is_initial_call:
            user_prompt = f"""
Begin the enrollment call with {patient['name']}. Start with ONLY the initial greeting.

Current context:
- This is the initial enrollment call
- Patient surgery is in {patient['days_until_surgery']} days
- No previous call history
- Focus on comprehensive baseline assessment

Start with ONLY: "Hello {patient['name']}, this is your healthcare assistant calling about your upcoming knee replacement surgery. Is this a good time to talk?"

DO NOT ask any other questions yet. Wait for their response first.
"""
        else:
            user_prompt = f"""
Continue the enrollment conversation with {patient['name']}. 

CRITICAL INSTRUCTIONS:
- This is an ONGOING enrollment call (NOT the start)
- Review the conversation history to see what has already been discussed
- DO NOT repeat questions that have already been answered
- DO NOT restart with greetings or introductions
- Continue naturally from where the conversation left off
- Move to the next logical question in the enrollment process
- Ask only ONE question at a time
- Be conversational and acknowledge their previous responses

Based on the conversation history, continue with the appropriate next step in the enrollment assessment.
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
    
    def _generate_education_prompt(self, context: CallContext, is_initial_call: bool = True) -> Dict[str, Any]:
        """Generate education-specific prompt based on week/topic"""
        
        patient = context.patient_data
        structure = context.conversation_structure
        week = structure.get("week", "Unknown")
        focus_topic = structure.get("focus_topic", "Educational Content")
        
        system_prompt = f"""
You are a caring and professional AI healthcare assistant conducting {week} educational call with {patient['name']} about their upcoming knee replacement surgery in {patient['days_until_surgery']} days.

CALL PURPOSE: {structure['call_purpose']}
FOCUS TOPIC: {focus_topic}

PATIENT INFORMATION:
- Name: {patient['name']}
- Surgery Date: {patient['surgery_date']} ({patient['days_until_surgery']} days from today)
- Days from Surgery: {context.days_from_surgery}
- Current Compliance Score: {patient['current_compliance_score']}
- Primary Physician: {patient['physician']}

EDUCATIONAL APPROACH:
- Tone: {structure.get('tone', 'educational_encouraging')} - Be warm, informative, and supportive
- Duration: {context.estimated_duration_minutes} minutes
- Build on previous conversations and check progress since last call
- Focus on practical, actionable information
- Encourage questions and provide clear explanations

THIS WEEK'S FOCUS: {focus_topic}

CONVERSATION STRUCTURE:
{self._get_week_specific_structure(context.days_from_surgery)}

CONVERSATION GUIDELINES:
- Start with a brief, simple greeting - do NOT be verbose in your opening message
- Ask ONE question at a time and wait for responses
- Provide information in digestible chunks
- Use examples relevant to their situation
- Reference and build upon previous conversations naturally
- Encourage questions throughout the conversation
- End with clear next steps and what to expect next week

EDUCATIONAL OBJECTIVES:
{self._format_objectives(structure.get('expected_outcomes', []))}

Remember: This is an educational conversation, not an assessment. Focus on teaching, clarifying, and building confidence for their upcoming surgery.
"""

        if is_initial_call:
            user_prompt = f"""
Begin the {week} educational call with {patient['name']}. 

Start with a simple, warm greeting and ask how they're feeling since your last conversation. Keep it brief and natural.

DO NOT launch into educational content immediately or explain what you'll cover today. Just establish rapport first.
"""
        else:
            user_prompt = f"""
Continue the {week} educational conversation with {patient['name']} about {focus_topic.lower()}.

CRITICAL INSTRUCTIONS:
- Review conversation history to see what's been covered
- Continue naturally from where you left off
- Do not repeat information already provided
- Ask follow-up questions to ensure understanding
- Progress through the educational content systematically
- Reference their specific responses when building on topics
"""

        return {
            "system_prompt": system_prompt.strip(),
            "user_prompt": user_prompt.strip(),
            "context_metadata": {
                "call_type": context.call_type.value,
                "patient_id": patient['patient_id'],
                "days_from_surgery": context.days_from_surgery,
                "week": week,
                "focus_topic": focus_topic,
                "estimated_duration": context.estimated_duration_minutes,
                "educational_objectives": structure.get('expected_outcomes', [])
            }
        }
    
    def _get_week_specific_structure(self, days_from_surgery: int) -> str:
        """Get detailed conversation structure for specific week"""
        
        if days_from_surgery == -28:  # Week 4
            return """
1. CHECK-IN SINCE ENROLLMENT
   - How are you feeling since our enrollment conversation?
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
   - Based on their home assessment from enrollment
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
    
    def _generate_generic_prompt(self, context: CallContext) -> Dict[str, Any]:
        """Generate generic prompt for other call types"""
        
        return {
            "system_prompt": f"You are conducting a {context.call_type.value} call.",
            "user_prompt": "Begin the conversation.",
            "context_metadata": asdict(context)
        }
    
    def _build_enrollment_prompt_template(self) -> str:
        """Build the enrollment prompt template"""
        # This can be expanded with more sophisticated templating
        return "enrollment_template"
    
    def extract_conversation_data(self, conversation_text: str, call_context: CallContext) -> Dict[str, Any]:
        """Extract structured data from completed conversation"""
        
        if call_context.call_type == CallType.ENROLLMENT:
            return self._extract_enrollment_data(conversation_text)
        else:
            return {"raw_conversation": conversation_text}
    
    def _extract_enrollment_data(self, conversation_text: str) -> Dict[str, Any]:
        """Extract enrollment-specific data points from conversation"""
        
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
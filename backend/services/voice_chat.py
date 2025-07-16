"""
Enhanced Voice Chat Service for TKA Patients
Supports contextual conversations based on call types and patient data
"""

import google.generativeai as genai
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from config import settings

logger = logging.getLogger(__name__)

class TKAVoiceChat:
    """Enhanced TKA Voice Chat Assistant with contextual support"""
    
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            # For demo - use environment variable
            import os
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                # Mock mode for testing
                self.model = None
                self.mock_mode = True
                logger.info("TKA Voice Chat initialized in MOCK MODE (no API key)")
                return
            genai.configure(api_key=api_key)
        else:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        self.mock_mode = False
        logger.info("TKA Voice Chat initialized with contextual support")
    
    def get_patient_context(self, patient_id: str = "demo") -> str:
        """Get patient context for conversation (legacy method)"""
        return f"""
        Patient Information:
        - Name: John Smith (Demo Patient)
        - Surgery Date: 2024-01-15 (2 weeks post-op)
        - Surgery Type: Total Knee Arthroplasty (Right Knee)
        - Current Stage: Early Recovery
        - Call Type: Follow-up check
        """
    
    async def generate_response(self, user_message: str, patient_id: str = "demo") -> str:
        """Generate contextual response for TKA patient (legacy method)"""
        
        patient_context = self.get_patient_context(patient_id)
        
        # Check if this is an outbound call initiation
        if "Begin this outbound" in user_message or "outbound call" in user_message:
            system_prompt = f"""
            You are a compassionate AI healthcare assistant making an OUTBOUND CALL to a post-surgical TKA patient.
            
            {patient_context}
            
            IMPORTANT: You are calling the patient, not the other way around.
            
            Guidelines:
            - Start with proper outbound call introduction: "Hello [Name], this is your healthcare assistant calling..."
            - Identify yourself and your purpose clearly
            - Explain why you're calling (follow-up check)
            - Be warm but professional
            - Ask how they're doing with recovery
            - Keep initial greeting under 80 words
            
            Begin the outbound call now with an appropriate introduction.
            """
            
            try:
                response = self.model.generate_content(system_prompt)
                return response.text.strip()
                
            except Exception as e:
                logger.error(f"Error generating outbound call: {e}")
                return "Hello John, this is your healthcare assistant calling to check on your recovery after your knee replacement surgery two weeks ago. How are you feeling today?"
        
        else:
            # Regular conversation response
            system_prompt = f"""
            You are a compassionate AI healthcare assistant for post-surgical Total Knee Arthroplasty (TKA) patients.
            
            {patient_context}
            
            Guidelines:
            - Be empathetic and supportive
            - Ask relevant follow-up questions about recovery
            - Monitor pain levels, mobility, and compliance
            - Provide encouragement and medical guidance
            - Keep responses conversational and under 100 words
            - If patient reports severe pain (8+) or concerning symptoms, recommend contacting their physician
            
            Current conversation context: This is a routine follow-up call to check on recovery progress.
            """
            
            try:
                full_prompt = f"{system_prompt}\n\nPatient says: '{user_message}'\n\nYour response:"
                
                response = self.model.generate_content(full_prompt)
                return response.text.strip()
                
            except Exception as e:
                logger.error(f"Error generating response: {e}")
                return "I'm sorry, I'm having trouble connecting right now. How are you feeling today after your knee surgery?"
    
    async def generate_contextual_response(
        self, 
        user_message: str, 
        system_prompt: str, 
        context_metadata: Dict[str, Any],
        conversation_history: Optional[list] = None
    ) -> str:
        """Generate response using full call context with conversation history"""
        
        try:
            # Build conversation history string
            history_text = ""
            if conversation_history:
                for msg in conversation_history:
                    speaker = "Assistant" if msg.get("role") == "assistant" else "Patient"
                    history_text += f"\n{speaker}: {msg.get('content', '')}"
            
            # Build the conversation prompt with history
            if history_text:
                full_prompt = f"{system_prompt}\n\nCONVERSATION HISTORY:{history_text}\n\nPatient: '{user_message}'\n\nAssistant:"
            else:
                full_prompt = f"{system_prompt}\n\nPatient: '{user_message}'\n\nAssistant:"
            
            response = self.model.generate_content(full_prompt)
            generated_text = response.text.strip()
            
            # Log the interaction for monitoring
            logger.info(f"Contextual response generated for call type: {context_metadata.get('call_type', 'unknown')}")
            
            return generated_text
            
        except Exception as e:
            logger.error(f"Error generating contextual response: {e}")
            
            # Fallback response based on call type
            call_type = context_metadata.get('call_type', 'unknown')
            if call_type == 'initial_clinical_assessment':
                return "I'm sorry, I'm having some technical difficulties. Let me start over - I'm calling to help you prepare for your upcoming knee replacement surgery. How are you feeling about the procedure?"
            else:
                return "I'm sorry, I'm having trouble connecting right now. Let me know how I can help you today."
    
    async def start_contextual_conversation(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        context_metadata: Dict[str, Any]
    ) -> str:
        """Start a new contextual conversation"""
        
        try:
            # Combine system and user prompts for initial conversation start
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            response = self.model.generate_content(full_prompt)
            generated_text = response.text.strip()
            
            # Log the conversation start
            logger.info(f"Started contextual conversation for call type: {context_metadata.get('call_type', 'unknown')}")
            
            return generated_text
            
        except Exception as e:
            logger.error(f"Error starting contextual conversation: {e}")
            
            # Fallback opening based on call type
            call_type = context_metadata.get('call_type', 'unknown')
            patient_name = context_metadata.get('patient_name', 'there')
            
            if call_type == 'initial_clinical_assessment':
                return f"Hello {patient_name}, this is your healthcare assistant calling about your upcoming knee replacement surgery. I'm having some technical difficulties, but I'd still love to talk with you about preparing for your procedure. Is this a good time to chat?"
            else:
                return f"Hello {patient_name}, this is your healthcare assistant. I'm having some connection issues, but I'm here to help. How are you doing today?"
    
    async def extract_conversation_insights(
        self, 
        conversation_text: str, 
        call_type: str
    ) -> Dict[str, Any]:
        """Extract structured insights from completed conversation"""
        
        extraction_prompt = f"""
        Analyze this healthcare conversation and extract key information:

        Call Type: {call_type}
        Conversation: {conversation_text}

        Extract and structure the following information in JSON format:
        - Patient responses to key questions
        - Concerns or issues identified
        - Compliance indicators
        - Any escalation triggers mentioned
        - Overall sentiment and anxiety level
        - Action items or follow-ups needed

        Return only valid JSON.
        """
        
        try:
            response = self.model.generate_content(extraction_prompt)
            # This would parse the JSON response in a real implementation
            return {"raw_analysis": response.text.strip()}
            
        except Exception as e:
            logger.error(f"Error extracting conversation insights: {e}")
            return {"error": "Could not analyze conversation", "raw_text": conversation_text}

# Global instance
_chat_service = None

def get_chat_service() -> TKAVoiceChat:
    """Get chat service instance"""
    global _chat_service
    if _chat_service is None:
        _chat_service = TKAVoiceChat()
    return _chat_service 
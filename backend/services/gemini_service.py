"""
Gemini AI Service for intent extraction and clinical analysis
"""

import os
import json
from typing import Dict, List, Optional
import google.generativeai as genai
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class GeminiService:
    """
    Handles AI processing using Google Gemini for clinical analysis
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    async def analyze_conversation(self, transcript: str, conversation_history: List[Dict] = None) -> Dict:
        """
        Analyze conversation transcript for clinical insights
        
        Args:
            transcript: Current conversation transcript
            conversation_history: Previous conversation context
            
        Returns:
            Dict: Analysis results with intent, entities, sentiment, etc.
        """
        try:
            # Build context from conversation history
            context = self._build_context(conversation_history or [])
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(transcript, context)
            
            # Get response from Gemini
            response = self.model.generate_content(prompt)
            
            # Parse and validate response
            analysis = self._parse_analysis_response(response.text)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")
    
    async def generate_response(self, prompt: str) -> str:
        """
        Generate a simple response using Gemini
        
        Args:
            prompt: The prompt to send to Gemini
            
        Returns:
            str: Generated response text
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise Exception(f"Failed to generate response: {e}")
    
    def _build_context(self, conversation_history: List[Dict]) -> str:
        """Build context string from conversation history"""
        if not conversation_history:
            return "No previous conversation history."
        
        context_parts = []
        for msg in conversation_history[-5:]:  # Last 5 messages for context
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts)
    
    def _create_analysis_prompt(self, transcript: str, context: str) -> str:
        """Create comprehensive analysis prompt"""
        return f"""
You are a clinical AI assistant analyzing a post-surgical patient conversation. 
Analyze the following transcript and provide a structured JSON response.

CONVERSATION CONTEXT:
{context}

CURRENT TRANSCRIPT:
{transcript}

Please analyze and return a JSON object with the following structure:
{{
    "intent": "string - main intent (pain_inquiry, wound_check, medication_question, emergency, general_inquiry, etc.)",
    "entities": {{
        "pain_level": "integer 1-10 or null",
        "symptoms": ["array of symptom strings"],
        "medications": ["array of mentioned medications"],
        "activities": ["array of mentioned activities"],
        "concerns": ["array of patient concerns"]
    }},
    "sentiment": "string - overall sentiment (positive, negative, neutral, anxious, distressed)",
    "urgency_level": "string - urgency (low, medium, high, critical)",
    "clinical_assessment": {{
        "pain_assessment": "string - assessment of pain level and type",
        "wound_status": "string - assessment of wound healing",
        "mobility_status": "string - assessment of patient mobility",
        "medication_compliance": "string - assessment of medication adherence",
        "red_flags": ["array of concerning symptoms or responses"]
    }},
    "recommended_actions": [
        "array of recommended follow-up actions"
    ],
    "requires_immediate_attention": "boolean - true if urgent medical attention needed",
    "summary": "string - brief summary of the conversation"
}}

Focus on:
1. Pain levels and pain management
2. Wound healing progress
3. Medication adherence
4. Mobility and recovery
5. Any concerning symptoms
6. Patient's emotional state

Return only valid JSON without any additional text or markdown formatting.
"""
    
    def _parse_analysis_response(self, response_text: str) -> Dict:
        """Parse and validate Gemini response"""
        try:
            # Clean response text
            response_text = response_text.strip()
            
            # Remove markdown formatting if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            # Parse JSON
            analysis = json.loads(response_text)
            
            # Validate required fields
            required_fields = ['intent', 'entities', 'sentiment', 'urgency_level', 'summary']
            for field in required_fields:
                if field not in analysis:
                    logger.warning(f"Missing required field: {field}")
                    analysis[field] = self._get_default_value(field)
            
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response_text}")
            
            # Return default analysis
            return {
                "intent": "general_inquiry",
                "entities": {},
                "sentiment": "neutral",
                "urgency_level": "low",
                "clinical_assessment": {},
                "recommended_actions": [],
                "requires_immediate_attention": False,
                "summary": "Unable to analyze conversation due to parsing error"
            }
    
    def _get_default_value(self, field: str):
        """Get default value for missing fields"""
        defaults = {
            "intent": "general_inquiry",
            "entities": {},
            "sentiment": "neutral",
            "urgency_level": "low",
            "clinical_assessment": {},
            "recommended_actions": [],
            "requires_immediate_attention": False,
            "summary": "No analysis available"
        }
        return defaults.get(field, None)

# Global instance
gemini_service = GeminiService()

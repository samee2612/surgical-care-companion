import os
import logging
from config import settings

import google.generativeai as genai

logger = logging.getLogger(__name__)


class TKAVoiceChat:
    """Enhanced TKA Voice Chat Assistant with contextual support"""

    def __init__(self):
        api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set. Please provide a valid API key.")

        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-2.5-flash")
            logger.info("TKA Voice Chat initialized with Gemini")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            raise

    def generate_response(self, prompt):
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def generate_contextual_response(self, system_prompt, history):
        # Combine system prompt with history
        full_prompt = f"{system_prompt}\n\n"
        for msg in history:
            full_prompt += f"{msg['role'].capitalize()}: {msg['content']}\n"
        response = self.model.generate_content(full_prompt)
        return response.text.strip()

    def start_contextual_conversation(self, messages):
        # Convert messages to text format for Gemini
        conversation_text = ""
        for msg in messages:
            conversation_text += f"{msg['role'].capitalize()}: {msg['content']}\n"
        
        response = self.model.generate_content(conversation_text)
        return [response.text.strip()]

    def extract_conversation_insights(self, transcript):
        insight_prompt = (
            "Analyze the conversation transcript and identify key points, emotional tone, and any open questions left unanswered."
            f"\nTranscript:\n{transcript}"
        )
        response = self.model.generate_content(insight_prompt)
        return response.text.strip()


# Global instance
_chat_service = None

def get_chat_service() -> TKAVoiceChat:
    """Get the global TKA Voice Chat service instance."""
    global _chat_service
    if _chat_service is None:
        _chat_service = TKAVoiceChat()
    return _chat_service

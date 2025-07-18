"""
Transcription Service using Twilio's Speech Recognition
Handles audio transcription using Twilio's built-in capabilities
"""

import os
import logging
from typing import Optional, Dict
from twilio.rest import Client
import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class TranscriptionService:
    """
    Handles audio transcription using Twilio's Speech Recognition
    """
    
    def __init__(self):
        self.twilio_client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        logger.info("TranscriptionService initialized with Twilio Speech Recognition")
    
    async def get_call_transcription(self, call_sid: str) -> Optional[str]:
        """
        Get transcription from Twilio call recording
        
        Args:
            call_sid: Twilio Call SID
            
        Returns:
            str: Transcription text or None if not available
        """
        try:
            # Get call recordings
            recordings = self.twilio_client.recordings.list(call_sid=call_sid)
            
            if not recordings:
                logger.warning(f"No recordings found for call {call_sid}")
                return None
            
            # Get the latest recording
            recording = recordings[0]
            
            # Check if transcription is available
            if hasattr(recording, 'transcription') and recording.transcription:
                return recording.transcription.transcription_text
            
            logger.info(f"No transcription found for recording {recording.sid}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting transcription for call {call_sid}: {str(e)}")
            return None
    
    async def extract_speech_from_webhook(self, webhook_data: dict) -> Dict:
        """
        Extract speech recognition result from Twilio webhook
        
        Args:
            webhook_data: Twilio webhook form data
            
        Returns:
            dict: Speech recognition result with text and confidence
        """
        try:
            # Extract speech result from webhook
            speech_result = webhook_data.get("SpeechResult", "")
            unstable_speech = webhook_data.get("UnstableSpeechResult", "")
            confidence = webhook_data.get("Confidence", 0.0)
            
            # Use stable result if available, otherwise use unstable
            transcript = speech_result if speech_result else unstable_speech
            
            if not transcript:
                logger.warning("No speech result found in webhook data")
                return {
                    "text": "",
                    "confidence": 0.0,
                    "source": "twilio_speech"
                }
            
            return {
                "text": transcript.strip(),
                "confidence": float(confidence) if confidence else 0.0,
                "source": "twilio_speech",
                "stable": bool(speech_result)
            }
            
        except Exception as e:
            logger.error(f"Error extracting speech from webhook: {str(e)}")
            return {
                "text": "",
                "confidence": 0.0,
                "source": "twilio_speech"
            }
    
    async def process_recording_url(self, recording_url: str) -> Dict:
        """
        Process recording URL to extract any available transcription
        
        Args:
            recording_url: URL to the Twilio recording
            
        Returns:
            dict: Transcription result
        """
        try:
            # For now, we'll rely on real-time speech recognition
            # In the future, we could implement async transcription processing
            logger.info(f"Processing recording URL: {recording_url}")
            
            return {
                "text": "Recording processed - use real-time speech recognition",
                "confidence": 0.5,
                "source": "recording_url",
                "recording_url": recording_url
            }
            
        except Exception as e:
            logger.error(f"Error processing recording URL: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Recording processing failed: {str(e)}")

    async def extract_speech_from_webhook(self, form_data: dict) -> Dict:
        """
        Extract speech recognition result from Twilio webhook data
        
        Args:
            form_data: Twilio webhook form data
            
        Returns:
            Dict containing speech recognition results
        """
        try:
            # Extract speech result from Twilio webhook
            speech_result = form_data.get("SpeechResult", "")
            unstable_speech = form_data.get("UnstableSpeechResult", "")
            confidence = form_data.get("Confidence", "0.0")
            
            # Use stable speech result if available, otherwise use unstable
            text = speech_result if speech_result else unstable_speech
            
            # Log for debugging
            logger.info(f"Speech recognition: text='{text}', confidence={confidence}")
            
            return {
                "text": text.strip() if text else "",
                "confidence": float(confidence) if confidence else 0.0,
                "source": "twilio_speech",
                "stable": bool(speech_result)
            }
            
        except Exception as e:
            logger.error(f"Error extracting speech from webhook: {e}")
            return {"text": "", "confidence": 0.0, "error": str(e)}

# Global instance
transcription_service = TranscriptionService()

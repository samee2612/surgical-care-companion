"""
Enhanced Speech to Text Service

Supports both file-based and streaming transcription using OpenAI Whisper
with real-time processing capabilities for voice agent integration.
"""

import logging
import asyncio
import tempfile
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import uuid

# Import FastAPI dependencies
from fastapi import UploadFile

# Audio processing dependencies (optional)
try:
    import whisper
    import numpy as np
    import torch
    import torchaudio
    import librosa
    import soundfile as sf
    from pydub import AudioSegment
    AUDIO_DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Speech-to-text dependencies not available: {e}")
    AUDIO_DEPENDENCIES_AVAILABLE = False
    # Provide fallback classes/functions
    whisper = None
    np = None
    torch = None
    torchaudio = None
    librosa = None
    sf = None
    AudioSegment = None

# OpenAI client for API-based transcription
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    logging.warning("OpenAI client not available")
    OPENAI_AVAILABLE = False
    OpenAI = None

# HTTP client for audio downloads
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError as e:
    logging.warning(f"HTTP client not available: {e}")
    HTTPX_AVAILABLE = False
    httpx = None

from config import settings

logger = logging.getLogger(__name__)


class StreamingTranscriber:
    """
    Real-time audio streaming transcriber
    
    Handles continuous audio streams and provides real-time transcription
    with buffering and chunk processing.
    """
    
    def __init__(self, model_name: str = "base"):
        self.model = whisper.load_model(model_name)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.buffer_size = 16000  # 1 second at 16kHz
        self.chunk_duration = 2.0  # Process every 2 seconds
        
    async def start_session(self, session_id: str, sample_rate: int = 16000) -> None:
        """Start a new transcription session"""
        self.active_sessions[session_id] = {
            'buffer': [],
            'sample_rate': sample_rate,
            'last_processed': datetime.now(),
            'accumulated_text': '',
            'chunk_counter': 0
        }
        logger.info(f"Started transcription session: {session_id}")
    
    async def add_audio_chunk(self, session_id: str, audio_data: bytes) -> Optional[str]:
        """
        Add audio chunk to session buffer and process if ready
        
        Args:
            session_id: Session identifier
            audio_data: Raw audio bytes (PCM format expected)
            
        Returns:
            Transcribed text if chunk is ready, None otherwise
        """
        if session_id not in self.active_sessions:
            await self.start_session(session_id)
        
        session = self.active_sessions[session_id]
        
        # Convert bytes to numpy array (assuming 16-bit PCM)
        try:
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            audio_float = audio_array.astype(np.float32) / 32768.0  # Normalize to [-1, 1]
            
            # Add to buffer
            session['buffer'].extend(audio_float)
            
            # Check if we have enough data to process
            if len(session['buffer']) >= self.buffer_size * self.chunk_duration:
                return await self._process_chunk(session_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            return None
    
    async def _process_chunk(self, session_id: str) -> Optional[str]:
        """Process accumulated audio chunk"""
        if not AUDIO_DEPENDENCIES_AVAILABLE:
            logger.warning("Audio dependencies not available for chunk processing")
            return "[Audio processing unavailable - missing dependencies]"
            
        session = self.active_sessions[session_id]
        
        try:
            # Get audio chunk
            chunk_size = int(self.buffer_size * self.chunk_duration)
            audio_chunk = np.array(session['buffer'][:chunk_size])
            
            # Remove processed data from buffer (keep some overlap)
            overlap_size = int(self.buffer_size * 0.5)  # 0.5 second overlap
            session['buffer'] = session['buffer'][chunk_size - overlap_size:]
            
            # Transcribe chunk
            result = self.model.transcribe(audio_chunk, fp16=False)
            text = result['text'].strip()
            
            if text:
                session['accumulated_text'] += f" {text}"
                session['last_processed'] = datetime.now()
                session['chunk_counter'] += 1
                
                logger.debug(f"Transcribed chunk {session['chunk_counter']}: {text}")
                return text
            
            return None
            
        except Exception as e:
            logger.error(f"Error transcribing chunk: {e}")
            return None
    
    async def finalize_session(self, session_id: str) -> str:
        """Finalize session and return complete transcription"""
        if session_id not in self.active_sessions:
            return ""
        
        session = self.active_sessions[session_id]
        
        # Process remaining buffer
        if len(session['buffer']) > 0:
            try:
                audio_chunk = np.array(session['buffer'])
                result = self.model.transcribe(audio_chunk, fp16=False)
                final_text = result['text'].strip()
                if final_text:
                    session['accumulated_text'] += f" {final_text}"
            except Exception as e:
                logger.error(f"Error processing final chunk: {e}")
        
        # Clean up and return
        complete_text = session['accumulated_text'].strip()
        del self.active_sessions[session_id]
        
        logger.info(f"Finalized transcription session: {session_id}")
        return complete_text


class SpeechToTextService:
    """
    Comprehensive Speech-to-Text Service
    
    Supports both file-based transcription and real-time streaming
    with integration capabilities for the voice agent system.
    """
    
    def __init__(self):
        self.model_name = getattr(settings, 'WHISPER_MODEL', "base")
        
        # Initialize model only if dependencies are available
        if AUDIO_DEPENDENCIES_AVAILABLE:
            try:
                self.model = whisper.load_model(self.model_name)
                self.streaming_transcriber = StreamingTranscriber(self.model_name)
                logger.info(f"Speech-to-Text service initialized with model: {self.model_name}")
            except Exception as e:
                logger.warning(f"Failed to load Whisper model: {e}")
                self.model = None
                self.streaming_transcriber = None
        else:
            logger.warning("Audio dependencies not available, using fallback mode")
            self.model = None
            self.streaming_transcriber = None
        
        # Configuration
        self.supported_formats = getattr(settings, 'ALLOWED_AUDIO_FORMATS', ['wav', 'mp3', 'm4a', 'flac'])
        self.max_file_size = getattr(settings, 'MAX_FILE_SIZE', 10 * 1024 * 1024)
        
        # Ensure temp folder exists
        self.tmp_dir = "tmp_audio"
        os.makedirs(self.tmp_dir, exist_ok=True)
    
    async def transcribe_file(self, audio_file: UploadFile) -> Dict[str, Any]:
        """
        Transcribe an uploaded audio file
        
        Args:
            audio_file: Uploaded audio file
            
        Returns:
            Dictionary with transcription results
        """
        try:
            # Check if audio processing is available
            if not AUDIO_DEPENDENCIES_AVAILABLE or not self.model:
                return {
                    'text': "[Audio transcription unavailable - missing dependencies]",
                    'language': 'unknown',
                    'confidence': 0.0,
                    'segments': [],
                    'processing_time_ms': 0,
                    'model_used': 'fallback',
                    'status': 'fallback_mode'
                }
            
            # Validate file
            if audio_file.size and audio_file.size > self.max_file_size:
                raise ValueError(f"File too large: {audio_file.size} bytes")
            
            # Generate unique temp file
            ext = os.path.splitext(audio_file.filename or "")[-1] or ".audio"
            temp_filename = f"{uuid.uuid4().hex}{ext}"
            temp_path = os.path.join(self.tmp_dir, temp_filename)
            
            # Save to temporary file
            content = await audio_file.read()
            with open(temp_path, "wb") as f:
                f.write(content)
            
            try:
                # Transcribe using Whisper
                start_time = datetime.now()
                result = self.model.transcribe(temp_path)
                end_time = datetime.now()
                
                # Extract information
                text = result['text'].strip()
                language = result.get('language', 'unknown')
                segments = result.get('segments', [])
                
                # Calculate metrics
                duration = end_time - start_time
                
                return {
                    'text': text,
                    'language': language,
                    'confidence': self._calculate_average_confidence(segments),
                    'segments': segments,
                    'processing_time_ms': int(duration.total_seconds() * 1000),
                    'model_used': self.model_name,
                    'timestamp': start_time.isoformat()
                }
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.error(f"Error transcribing file: {e}")
            raise
    
    async def transcribe_url(self, audio_url: str) -> Dict[str, Any]:
        """
        Transcribe audio from a URL (e.g., Twilio recording)
        
        Args:
            audio_url: URL to audio file
            
        Returns:
            Dictionary with transcription results
        """
        try:
            # Check if audio processing is available
            if not AUDIO_DEPENDENCIES_AVAILABLE or not self.model:
                return {
                    'text': "[Audio transcription unavailable - missing dependencies]",
                    'language': 'unknown',
                    'confidence': 0.0,
                    'segments': [],
                    'processing_time_ms': 0,
                    'model_used': 'fallback',
                    'status': 'fallback_mode',
                    'source_url': audio_url
                }
            
            # Check if HTTP client is available
            if not HTTPX_AVAILABLE:
                return {
                    'text': "[URL transcription unavailable - missing HTTP client]",
                    'language': 'unknown',
                    'confidence': 0.0,
                    'segments': [],
                    'processing_time_ms': 0,
                    'model_used': 'fallback',
                    'status': 'http_client_unavailable',
                    'source_url': audio_url
                }
            
            # Download audio file
            async with httpx.AsyncClient() as client:
                response = await client.get(audio_url)
                response.raise_for_status()
                
                # Save to temporary file
                temp_filename = f"{uuid.uuid4().hex}.wav"
                temp_path = os.path.join(self.tmp_dir, temp_filename)
                
                with open(temp_path, "wb") as f:
                    f.write(response.content)
            
            try:
                # Transcribe
                start_time = datetime.now()
                result = self.model.transcribe(temp_path)
                end_time = datetime.now()
                
                text = result['text'].strip()
                language = result.get('language', 'unknown')
                segments = result.get('segments', [])
                
                return {
                    'text': text,
                    'language': language,
                    'confidence': self._calculate_average_confidence(segments),
                    'segments': segments,
                    'processing_time_ms': int((end_time - start_time).total_seconds() * 1000),
                    'model_used': self.model_name,
                    'timestamp': start_time.isoformat(),
                    'source_url': audio_url
                }
                
            finally:
                # Clean up
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.error(f"Error transcribing URL {audio_url}: {e}")
            raise
    
    async def transcribe_stream(self, audio_data: bytes, session_id: str, is_final: bool = False) -> Optional[Dict[str, Any]]:
        """
        Transcribe streaming audio data
        
        Args:
            audio_data: Raw audio bytes
            session_id: Streaming session identifier
            is_final: Whether this is the final chunk
            
        Returns:
            Transcription result or None if not ready
        """
        try:
            # Check if streaming transcriber is available
            if not AUDIO_DEPENDENCIES_AVAILABLE or not self.streaming_transcriber:
                return {
                    'text': "[Streaming transcription unavailable - missing dependencies]",
                    'confidence': 0.0,
                    'is_final': is_final,
                    'session_id': session_id,
                    'timestamp': datetime.now(),
                    'duration_ms': 0,
                    'status': 'fallback_mode'
                }
            
            if is_final:
                # Finalize the session
                final_text = await self.streaming_transcriber.finalize_session(session_id)
                if final_text:
                    return {
                        'text': final_text,
                        'confidence': 0.8,  # Default confidence for streaming
                        'is_final': True,
                        'session_id': session_id,
                        'timestamp': datetime.now(),
                        'duration_ms': 0
                    }
            else:
                # Process chunk
                partial_text = await self.streaming_transcriber.add_audio_chunk(session_id, audio_data)
                if partial_text:
                    return {
                        'text': partial_text,
                        'confidence': 0.7,  # Lower confidence for partial results
                        'is_final': False,
                        'session_id': session_id,
                        'timestamp': datetime.now(),
                        'duration_ms': 0
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in streaming transcription: {e}")
            return None
    
    async def start_streaming_session(self, session_id: str, sample_rate: int = 16000) -> bool:
        """Start a new streaming transcription session"""
        try:
            await self.streaming_transcriber.start_session(session_id, sample_rate)
            return True
        except Exception as e:
            logger.error(f"Error starting streaming session: {e}")
            return False
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported audio formats"""
        return self.supported_formats.copy()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            'model_name': self.model_name,
            'supported_formats': self.supported_formats,
            'max_file_size_mb': self.max_file_size / (1024 * 1024)
        }
    
    def _calculate_average_confidence(self, segments: List[Dict]) -> float:
        """Calculate average confidence from segments"""
        if not segments:
            return 0.0
        
        # Whisper doesn't provide confidence scores directly
        # This is a placeholder for when using models that do
        return 0.85  # Default confidence


# Global service instance
_stt_service: Optional[SpeechToTextService] = None


def get_stt_service() -> SpeechToTextService:
    """Get global Speech-to-Text service instance"""
    global _stt_service
    if _stt_service is None:
        _stt_service = SpeechToTextService()
    return _stt_service

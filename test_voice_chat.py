#!/usr/bin/env python3
"""
Test script for voice chat API
"""

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database.connection import get_db
from backend.models import Patient, CallSession
from backend.services.call_context_service import CallContextService
from backend.services.context_injection_service import ContextInjectionService

def test_voice_chat():
    """Test the voice chat functionality"""
    print("🗣️ Testing Voice Chat...")
    
    try:
        # Get database session
        db = next(get_db())
        
        # Get test patient and call session
        patient = db.query(Patient).filter(Patient.name == "Bob Martinez").first()
        call_session = db.query(CallSession).filter(CallSession.patient_id == patient.id).first()
        
        if not patient or not call_session:
            print("❌ No test data found. Run test_db_setup.py first.")
            return
            
        print(f"✅ Found patient: {patient.name} (ID: {patient.id})")
        print(f"✅ Found call session: {call_session.call_type} (ID: {call_session.id})")
        
        # Initialize services
        context_service = CallContextService()
        injection_service = ContextInjectionService()
        
        # Generate call context
        call_context = context_service.get_call_context(patient, call_session)
        print(f"✅ Generated call context for {call_context.call_type.value}")
        
        # Test conversation responses
        test_messages = [
            "yes",
            "I am worried about the surgery",
            "My knee really hurts",
            "I feel ready",
            "I have some questions"
        ]
        
        print("\n🤖 Testing conversation responses:")
        print("=" * 50)
        
        for message in test_messages:
            response = get_contextual_response(message, call_session.call_type, patient.name, [])
            print(f"\nUser: {message}")
            print(f"Bot: {response}")
            print("-" * 40)
        
        db.close()
        
    except Exception as e:
        print(f"❌ Voice chat test failed: {e}")
        import traceback
        traceback.print_exc()


def get_contextual_response(user_input: str, call_type: str, patient_name: str, contextual_responses):
    """Simple test response function - import the actual one from the original service"""
    
    user_input_lower = user_input.lower()
    
    # Call type descriptions and purposes
    call_purposes = {
        "initial_assessment": "getting to know your current situation",
        "preparation_assessment": "checking how your preparations are going",
        "final_assessment": "making sure you're ready for tomorrow",
        "education": "helping you understand your surgery better",
        "preparation": "helping you prepare for your surgery",
        "final_prep": "doing final checks before surgery",
        "final_logistics": "confirming all the details for tomorrow",
        "enrollment": "welcoming you to our support program"
    }
    
    # Dynamic conversation starters
    conversation_starters = {
        "education": [
            f"What would you like to know about your knee replacement, {patient_name}?",
            f"Have you been thinking about what to expect during recovery?",
            f"What aspects of the surgery are you most curious about?",
            f"How much do you know about the procedure so far, {patient_name}?"
        ]
    }
    
    # Response categories based on user input sentiment and content
    positive_responses = [
        f"That's wonderful to hear, {patient_name}.",
        f"I'm so glad you're feeling that way, {patient_name}.",
        f"That sounds really positive, {patient_name}.",
        f"Excellent, {patient_name}!"
    ]
    
    concern_responses = [
        f"I completely understand that concern, {patient_name}.",
        f"Many patients feel similarly, {patient_name}.",
        f"That's a very normal way to feel, {patient_name}.",
        f"Let's talk through that together, {patient_name}."
    ]
    
    pain_responses = [
        f"I hear you about the pain, {patient_name}.",
        f"That discomfort is exactly why this surgery will help, {patient_name}.",
        f"Pain management is something we take very seriously, {patient_name}.",
        f"This surgery should provide significant relief, {patient_name}."
    ]
    
    general_responses = [
        f"Thank you for sharing that, {patient_name}.",
        f"I appreciate you telling me about that, {patient_name}.",
        f"That's good information, {patient_name}.",
        f"I'm glad you brought that up, {patient_name}."
    ]
    
    # Determine response based on user input
    import random
    
    # Positive indicators
    positive_words = ["good", "great", "fine", "ready", "prepared", "confident", "excited", "yes", "sure", "okay"]
    # Concern indicators  
    concern_words = ["worried", "scared", "nervous", "anxious", "concerned", "afraid", "unsure", "confused"]
    # Pain indicators
    pain_words = ["pain", "hurt", "ache", "sore", "painful", "discomfort", "stiff"]
    
    # Choose appropriate response category
    if any(word in user_input_lower for word in positive_words):
        base_response = random.choice(positive_responses)
        follow_up = random.choice(conversation_starters.get(call_type, ["How are you feeling today?"]))
    elif any(word in user_input_lower for word in concern_words):
        base_response = random.choice(concern_responses)
        follow_up = "What specific aspect would you like to discuss?"
    elif any(word in user_input_lower for word in pain_words):
        base_response = random.choice(pain_responses)
        follow_up = "Can you tell me more about what you're experiencing?"
    else:
        base_response = random.choice(general_responses)
        follow_up = random.choice(conversation_starters.get(call_type, ["How are you feeling today?"]))
    
    # Add contextual bridge based on call type
    call_purpose = call_purposes.get(call_type, "helping you prepare")
    bridge = f" Since we're {call_purpose}, {follow_up}"
    
    return f"{base_response}{bridge}"


if __name__ == "__main__":
    test_voice_chat() 
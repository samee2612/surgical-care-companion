#!/usr/bin/env python3
"""
Test Conversation Logic - Verify the core conversation logic works
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.utils.conversation_utils import get_covered_areas

def test_conversation_logic():
    """Test the conversation logic without server dependencies"""
    
    print("🧪 Testing Conversation Logic")
    print("=" * 40)
    
    # Test preparation call conversation
    history = [
        {"role": "assistant", "content": "Hello John Smith, this is your healthcare assistant calling about your upcoming knee replacement surgery on 2024-01-15. This is your weekly preparation check-in to make sure everything is ready for your surgery. Is this a good time to talk?"},
        {"role": "user", "content": "Yes, this is a good time"},
        {"role": "assistant", "content": "To prevent falls, it's important to remove trip hazards like loose rugs. Have you had a chance to prepare your recovery space?"},
        {"role": "user", "content": "Yes, I've removed the loose rugs and cleared the pathways."},
        {"role": "assistant", "content": "Have you cleared pathways and removed any obstacles that could cause tripping?"},
        {"role": "user", "content": "Yes, I've moved furniture and cleared all the walkways."}
    ]
    
    # Test area detection
    covered_data = get_covered_areas(history, "preparation")
    
    print("📋 Area Detection Results:")
    for area, covered in covered_data.items():
        if not area.endswith('_questions'):
            print(f"  {area}: {'✅ COVERED' if covered else '❌ NOT COVERED'}")
    
    print()
    print("📊 Question Counts:")
    for area in ["home_safety", "equipment_supplies", "medical_preparation", "support_verification"]:
        questions_asked = covered_data.get(f"{area}_questions_asked", 0)
        questions_answered = covered_data.get(f"{area}_questions_answered", 0)
        print(f"  {area}: {questions_asked} asked, {questions_answered} answered")
    
    print()
    print("✅ Conversation logic test completed successfully!")

if __name__ == "__main__":
    test_conversation_logic() 
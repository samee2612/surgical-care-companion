#!/usr/bin/env python3
"""
Preparation Call Test - Tests the updated backend logic for preparation calls with question counting
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from datetime import datetime, timedelta
from backend.utils.conversation_utils import get_covered_areas

def test_preparation_call_question_counting():
    """Test the preparation call question counting logic"""
    
    print("🧪 Testing Preparation Call Question Counting")
    print("=" * 50)
    
    # Mock conversation history for preparation call with multiple questions per area
    history = [
        {"role": "assistant", "content": "Hello Sarah Johnson, with your weekly preparation check-in."},
        {"role": "user", "content": "Hello, yes I'm ready to talk"},
        
        # Home Safety - Question 1
        {"role": "assistant", "content": "To prevent falls, it's important to remove trip hazards like loose rugs. Have you had a chance to prepare your recovery space?"},
        {"role": "user", "content": "Yes, I've removed the loose rugs and cleared the pathways. I also made sure the lighting is good in the main areas"},
        
        # Home Safety - Question 2
        {"role": "assistant", "content": "Have you cleared pathways and removed any obstacles that could cause tripping?"},
        {"role": "user", "content": "Yes, I've moved furniture and cleared all the walkways. I also made sure there are no cords or wires in the way"},
        
        # Equipment - Question 1
        {"role": "assistant", "content": "Have you obtained a raised toilet seat and a grabber tool? These are essential for following your hip precautions after surgery."},
        {"role": "user", "content": "I have the raised toilet seat, but I'm still waiting for the grabber tool to be delivered"},
        
        # Equipment - Question 2
        {"role": "assistant", "content": "Do you have all the equipment you'll need for recovery?"},
        {"role": "user", "content": "I have the walker and crutches, and I'm getting the grabber tool soon. I also have all the wound care supplies"},
        
        # Medical Prep - Question 1
        {"role": "assistant", "content": "Let's review medications. Are you currently taking any blood-thinning medication, such as Aspirin, Warfarin, or Eliquis?"},
        {"role": "user", "content": "Yes, I'm taking Aspirin daily"},
        
        # Medical Prep - Question 2
        {"role": "assistant", "content": "Have you completed all your pre-surgery medical appointments?"},
        {"role": "user", "content": "Yes, I've completed all the required appointments and have all the clearances"},
        
        # Support System - Question 1
        {"role": "assistant", "content": "Who will be helping you during your recovery?"},
        {"role": "user", "content": "My daughter will be staying with me for the first week, and my neighbor can help with errands"},
        
        # Support System - Question 2
        {"role": "assistant", "content": "Have you discussed your recovery needs with your support person?"},
        {"role": "user", "content": "Yes, I've talked with my daughter about what I'll need help with, and she's prepared to assist me"}
    ]
    
    # Test area detection with question counting
    covered_data = get_covered_areas(history, "preparation")
    
    print("📋 Preparation Call Areas with Question Counts:")
    print("-" * 50)
    
    expected_areas = {
        "home_safety": "Home Safety & Trip Hazards",
        "equipment_supplies": "Equipment & Supplies", 
        "medical_preparation": "Medical Preparation",
        "support_verification": "Support System Verification"
    }
    
    for area, description in expected_areas.items():
        covered = covered_data[area]
        questions_asked = covered_data.get(f"{area}_questions_asked", 0)
        questions_answered = covered_data.get(f"{area}_questions_answered", 0)
        
        status = "✅ COVERED" if covered else "❌ NOT COVERED"
        print(f"{description}: {status}")
        print(f"  Questions Asked: {questions_asked}")
        print(f"  Questions Answered: {questions_answered}")
        print()
    
    print("🔍 Analysis:")
    print("-" * 20)
    
    # Check each area specifically
    for area, description in expected_areas.items():
        covered = covered_data[area]
        questions_asked = covered_data.get(f"{area}_questions_asked", 0)
        questions_answered = covered_data.get(f"{area}_questions_answered", 0)
        
        if covered:
            print(f"✅ {description}: Covered with {questions_answered} questions answered")
        else:
            print(f"❌ {description}: Not covered yet ({questions_asked} asked, {questions_answered} answered)")
    
    # Check if all areas are covered
    all_covered = all(covered_data[area] for area in expected_areas.keys())
    print()
    if all_covered:
        print("🎉 SUCCESS: All 4 preparation areas are covered with 2+ questions each!")
        print("The call can proceed to wrap-up.")
    else:
        print("⚠️  INCOMPLETE: Some areas still need more questions.")
        for area in expected_areas.keys():
            if not covered_data[area]:
                questions_asked = covered_data.get(f"{area}_questions_asked", 0)
                questions_answered = covered_data.get(f"{area}_questions_answered", 0)
                print(f"  - {expected_areas[area]}: {questions_answered}/2+ questions answered")
    
    return covered_data

def test_clinical_assessment_areas():
    """Test the clinical assessment area detection for comparison"""
    
    print("\n" + "=" * 50)
    print("🧪 Testing Clinical Assessment Area Detection")
    print("=" * 50)
    
    # Mock conversation history for clinical assessment
    history = [
        {"role": "assistant", "content": "Hello Sarah Johnson, this is your healthcare assistant calling about your upcoming knee replacement surgery. Is this a good time to talk?"},
        {"role": "user", "content": "Yes, this is a good time"},
        {"role": "assistant", "content": "Can you confirm your upcoming knee replacement surgery date?"},
        {"role": "user", "content": "Yes, it's scheduled for January 15th"},
        {"role": "assistant", "content": "How would you rate your current knee pain on a scale of 1 to 10?"},
        {"role": "user", "content": "I'd say it's about a 7"},
        {"role": "assistant", "content": "What activities are most difficult for you right now?"},
        {"role": "user", "content": "Walking up stairs and standing for long periods"},
        {"role": "assistant", "content": "Who will be helping you during your recovery?"},
        {"role": "user", "content": "My daughter will be staying with me for the first week"}
    ]
    
    # Test area detection
    covered = get_covered_areas(history, "initial_clinical_assessment")
    
    print("📋 Clinical Assessment Areas Detection Results:")
    print("-" * 40)
    
    expected_areas = {
        "surgery_confirmation": "Surgery Confirmation",
        "pain_level": "Pain Level Assessment",
        "activity_limitations": "Activity Limitations", 
        "support_system": "Support System"
    }
    
    for area, description in expected_areas.items():
        status = "✅ COVERED" if covered[area] else "❌ NOT COVERED"
        print(f"{description}: {status}")
    
    return covered

def main():
    """Main test function"""
    print("🤖 Surgical Care Companion - Preparation Call Question Counting Test")
    print("=" * 70)
    print("Testing the updated backend logic for preparation calls with 2-3 questions per area")
    print()
    
    # Test preparation call areas with question counting
    prep_results = test_preparation_call_question_counting()
    
    # Test clinical assessment areas for comparison
    clinical_results = test_clinical_assessment_areas()
    
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    
    prep_covered = sum(1 for area in ["home_safety", "equipment_supplies", "medical_preparation", "support_verification"] if prep_results[area])
    clinical_covered = sum(clinical_results.values())
    
    print(f"Preparation Call: {prep_covered}/4 areas covered (with 2+ questions each)")
    print(f"Clinical Assessment: {clinical_covered}/4 areas covered")
    
    if prep_covered == 4 and clinical_covered == 4:
        print("✅ SUCCESS: Both call types are working correctly!")
        print("✅ Preparation calls now ask 2-3 questions per area before moving on!")
    else:
        print("⚠️  ISSUES: Some areas not being detected properly")
    
    print("\n✅ Preparation call question counting test completed!")

if __name__ == "__main__":
    main() 
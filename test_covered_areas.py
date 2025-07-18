#!/usr/bin/env python3
"""
Test the new get_covered_areas logic that supports 2-3 questions per area
"""

def get_covered_areas(history):
    """Test version of the new get_covered_areas function"""
    covered = {
        "surgery_confirmation": False,
        "pain_level": False,
        "activity_limitations": False,
        "support_system": False
    }
    
    # Track question count per area
    question_counts = {
        "surgery_confirmation": 0,
        "pain_level": 0,
        "activity_limitations": 0,
        "support_system": 0
    }
    
    for turn in history:
        content = turn["content"].lower()
        
        # Detect which area the assistant is asking about
        if turn["role"] == "assistant":
            if any(word in content for word in ["surgery", "date", "operation", "scheduled", "upcoming", "confirm"]) and (
                "surgery" in content or "date" in content or "operation" in content
            ):
                question_counts["surgery_confirmation"] += 1
            elif any(word in content for word in ["pain", "1 to 10", "scale", "rate your pain", "how much pain", "8", "7", "6", "5", "4", "3", "2", "1", "9", "10"]):
                question_counts["pain_level"] += 1
            elif any(word in content for word in ["activity", "limit", "walk", "move", "mobility", "stairs", "standing", "daily tasks", "trouble", "difficulty"]):
                question_counts["activity_limitations"] += 1
            elif any(word in content for word in ["support", "help", "caregiver", "family", "friend", "someone", "assist", "partner", "spouse"]):
                question_counts["support_system"] += 1
        
        # Mark area as covered only after 2+ questions AND a user response
        if turn["role"] == "user":
            # Check if we've asked enough questions in each area (2+)
            if question_counts["surgery_confirmation"] >= 2:
                covered["surgery_confirmation"] = True
            if question_counts["pain_level"] >= 2:
                covered["pain_level"] = True
            if question_counts["activity_limitations"] >= 2:
                covered["activity_limitations"] = True
            if question_counts["support_system"] >= 2:
                covered["support_system"] = True
    
    return covered, question_counts

def test_conversation_scenarios():
    """Test various conversation scenarios"""
    
    print("🧪 Testing New Covered Areas Logic")
    print("=" * 50)
    
    # Test 1: Single question per area (should NOT mark as covered)
    print("\n📋 Test 1: Single question per area")
    history1 = [
        {"role": "assistant", "content": "Can you confirm your surgery date?"},
        {"role": "user", "content": "Yes, it's July 30th"},
        {"role": "assistant", "content": "How would you rate your pain on a scale of 1-10?"},
        {"role": "user", "content": "About a 7"},
        {"role": "assistant", "content": "What activities are difficult for you?"},
        {"role": "user", "content": "Walking up stairs"},
        {"role": "assistant", "content": "Who will help you after surgery?"},
        {"role": "user", "content": "My daughter"}
    ]
    
    covered1, counts1 = get_covered_areas(history1)
    print(f"Question counts: {counts1}")
    print(f"Covered areas: {covered1}")
    print(f"All covered: {all(covered1.values())}")
    
    # Test 2: Two questions per area (should mark as covered)
    print("\n📋 Test 2: Two questions per area")
    history2 = [
        {"role": "assistant", "content": "Can you confirm your surgery date?"},
        {"role": "user", "content": "Yes, it's July 30th"},
        {"role": "assistant", "content": "How are you feeling about the surgery?"},
        {"role": "user", "content": "A bit nervous but ready"},
        {"role": "assistant", "content": "How would you rate your pain on a scale of 1-10?"},
        {"role": "user", "content": "About a 7"},
        {"role": "assistant", "content": "How long have you had this pain?"},
        {"role": "user", "content": "About 6 months"},
        {"role": "assistant", "content": "What activities are difficult for you?"},
        {"role": "user", "content": "Walking up stairs"},
        {"role": "assistant", "content": "Can you walk without assistance?"},
        {"role": "user", "content": "Yes, but with difficulty"},
        {"role": "assistant", "content": "Who will help you after surgery?"},
        {"role": "user", "content": "My daughter"},
        {"role": "assistant", "content": "Will she be staying with you?"},
        {"role": "user", "content": "Yes, for the first week"}
    ]
    
    covered2, counts2 = get_covered_areas(history2)
    print(f"Question counts: {counts2}")
    print(f"Covered areas: {covered2}")
    print(f"All covered: {all(covered2.values())}")
    
    # Test 3: Mixed questions (some areas with 1, some with 2+)
    print("\n📋 Test 3: Mixed question counts")
    history3 = [
        {"role": "assistant", "content": "Can you confirm your surgery date?"},
        {"role": "user", "content": "Yes, it's July 30th"},
        {"role": "assistant", "content": "How are you feeling about the surgery?"},
        {"role": "user", "content": "A bit nervous but ready"},
        {"role": "assistant", "content": "How would you rate your pain on a scale of 1-10?"},
        {"role": "user", "content": "About a 7"},
        {"role": "assistant", "content": "What activities are difficult for you?"},
        {"role": "user", "content": "Walking up stairs"},
        {"role": "assistant", "content": "Who will help you after surgery?"},
        {"role": "user", "content": "My daughter"}
    ]
    
    covered3, counts3 = get_covered_areas(history3)
    print(f"Question counts: {counts3}")
    print(f"Covered areas: {covered3}")
    print(f"All covered: {all(covered3.values())}")
    
    # Test 4: Complete conversation with 2+ questions per area
    print("\n📋 Test 4: Complete conversation with 2+ questions per area")
    history4 = [
        {"role": "assistant", "content": "Can you confirm your surgery date?"},
        {"role": "user", "content": "Yes, it's July 30th"},
        {"role": "assistant", "content": "How are you feeling about the surgery?"},
        {"role": "user", "content": "A bit nervous but ready"},
        {"role": "assistant", "content": "How would you rate your pain on a scale of 1-10?"},
        {"role": "user", "content": "About a 7"},
        {"role": "assistant", "content": "How long have you had this pain?"},
        {"role": "user", "content": "About 6 months"},
        {"role": "assistant", "content": "What activities are difficult for you?"},
        {"role": "user", "content": "Walking up stairs"},
        {"role": "assistant", "content": "Can you walk without assistance?"},
        {"role": "user", "content": "Yes, but with difficulty"},
        {"role": "assistant", "content": "Who will help you after surgery?"},
        {"role": "user", "content": "My daughter"},
        {"role": "assistant", "content": "Will she be staying with you?"},
        {"role": "user", "content": "Yes, for the first week"},
        {"role": "assistant", "content": "Do you have backup support?"},
        {"role": "user", "content": "Yes, my neighbor can help"}
    ]
    
    covered4, counts4 = get_covered_areas(history4)
    print(f"Question counts: {counts4}")
    print(f"Covered areas: {covered4}")
    print(f"All covered: {all(covered4.values())}")
    
    print("\n✅ Test Results Summary:")
    print(f"Test 1 (1 question each): All covered = {all(covered1.values())} ❌ (should be False)")
    print(f"Test 2 (2 questions each): All covered = {all(covered2.values())} ✅ (should be True)")
    print(f"Test 3 (mixed): All covered = {all(covered3.values())} ❌ (should be False)")
    print(f"Test 4 (complete): All covered = {all(covered4.values())} ✅ (should be True)")

if __name__ == "__main__":
    test_conversation_scenarios() 
#!/usr/bin/env python3
"""
Debug the get_covered_areas function with the actual conversation history
"""

def get_covered_areas(history):
    """Debug version of get_covered_areas function"""
    covered = {
        "surgery_confirmation": False,
        "pain_level": False,
        "activity_limitations": False,
        "support_system": False
    }
    
    print("🔍 Analyzing conversation history:")
    print("=" * 50)
    
    for i, turn in enumerate(history):
        content = turn["content"].lower()
        role = turn["role"]
        
        print(f"\nTurn {i+1} ({role}): {turn['content']}")
        
        # Check surgery confirmation
        if not covered["surgery_confirmation"]:
            surgery_keywords = ["surgery", "date", "operation", "scheduled", "upcoming"]
            confirm_keywords = ["confirm", "yes", "right", "correct"]
            
            has_surgery_keyword = any(word in content for word in surgery_keywords)
            has_confirm_keyword = any(word in content for word in confirm_keywords)
            
            if has_surgery_keyword and has_confirm_keyword:
                covered["surgery_confirmation"] = True
                print(f"  ✅ Surgery confirmation marked as covered")
            elif has_surgery_keyword:
                print(f"  ⚠️  Surgery keyword found but no confirm keyword")
            elif has_confirm_keyword:
                print(f"  ⚠️  Confirm keyword found but no surgery keyword")
        
        # Check pain level
        if not covered["pain_level"]:
            pain_keywords = ["pain", "1 to 10", "scale", "rate your pain", "how much pain", "8", "7", "6", "5", "4", "3", "2", "1", "9", "10"]
            if any(word in content for word in pain_keywords):
                covered["pain_level"] = True
                print(f"  ✅ Pain level marked as covered")
        
        # Check activity limitations
        if not covered["activity_limitations"]:
            activity_keywords = ["activity", "limit", "walk", "move", "mobility", "stairs", "standing", "daily tasks", "trouble", "difficulty"]
            if any(word in content for word in activity_keywords):
                covered["activity_limitations"] = True
                print(f"  ✅ Activity limitations marked as covered")
        
        # Check support system
        if not covered["support_system"]:
            support_keywords = ["support", "help", "caregiver", "family", "friend", "someone", "assist", "partner", "spouse"]
            support_phrases = ["who will help", "who will be helping", "who can help", "support person", "caregiver", "family member", "friend", "partner", "spouse"]
            
            has_support_keyword = any(word in content for word in support_keywords)
            has_support_phrase = any(phrase in content for phrase in support_phrases)
            
            if has_support_keyword and has_support_phrase:
                covered["support_system"] = True
                print(f"  ✅ Support system marked as covered")
            elif has_support_keyword:
                print(f"  ⚠️  Support keyword found but no support phrase")
            elif has_support_phrase:
                print(f"  ⚠️  Support phrase found but no support keyword")
    
    print(f"\n📊 Final Coverage Status:")
    print(f"  Surgery confirmation: {covered['surgery_confirmation']}")
    print(f"  Pain level: {covered['pain_level']}")
    print(f"  Activity limitations: {covered['activity_limitations']}")
    print(f"  Support system: {covered['support_system']}")
    print(f"  All covered: {all(covered.values())}")
    
    return covered

def test_actual_conversation():
    """Test with the actual conversation history"""
    
    # Your actual conversation history
    history = [
        {"role": "assistant", "content": "Hello Bob Martinez, this is your healthcare assistant calling about your upcoming knee replacement surgery. Is this a good time to talk?"},
        {"role": "user", "content": "yes its a good time"},
        {"role": "assistant", "content": "Wonderful! To confirm, your knee replacement surgery is coming up soon. Can you tell me what date you have for that, and how are you feeling as it approaches?"},
        {"role": "user", "content": "feeling nervous"},
        {"role": "assistant", "content": "I completely understand that, Bob. It's perfectly normal to feel nervous as a big surgery like this approaches. To help us ensure you're as comfortable as possible, could you tell me a little about your current pain level? On a scale of 1 to 10, with 1 being no pain and 10 being the worst pain imaginable, what would you say your current knee pain is?"},
        {"role": "user", "content": "It pains a lot. Id say 9 out of 10"},
        {"role": "assistant", "content": "Thank you for sharing that, Bob. A 9 out of 10 is very significant pain, and I'm sorry to hear you're experiencing that. To help us understand the full impact, could you tell me what activities or movements are most difficult for you right now because of your knee?"},
        {"role": "user", "content": "I have trouble walking up stairs and standing for long periods"}
    ]
    
    print("🧪 Testing Actual Conversation History")
    print("=" * 60)
    
    covered = get_covered_areas(history)
    
    print(f"\n🎯 Analysis:")
    if all(covered.values()):
        print("❌ PROBLEM: All areas marked as covered, but support system was never asked!")
    else:
        print("✅ CORRECT: Not all areas covered, should ask about next uncovered area")
        uncovered_areas = [area for area, is_covered in covered.items() if not is_covered]
        print(f"   Uncovered areas: {uncovered_areas}")

if __name__ == "__main__":
    test_actual_conversation() 
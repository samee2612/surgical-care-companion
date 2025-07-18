#!/usr/bin/env python3
"""
Debug why support system is not being marked as covered
"""

def test_support_system_detection():
    """Test the support system detection logic"""
    
    # The actual conversation
    history = [
        {"role": "assistant", "content": "Thanks for sharing that. It makes perfect sense that walking stairs and standing for long periods are difficult with that level of pain. As we prepare for your surgery, it's helpful to think about your recovery at home. Do you have someone who will be able to help you out after your surgery?"},
        {"role": "user", "content": "My husband and children will take care of me post my surgery"}
    ]
    
    print("🔍 Testing Support System Detection")
    print("=" * 50)
    
    for i, turn in enumerate(history):
        content = turn["content"].lower()
        role = turn["role"]
        
        print(f"\nTurn {i+1} ({role}): {turn['content']}")
        
        # Test support system detection
        support_keywords = ["support", "help", "caregiver", "family", "friend", "someone", "assist", "partner", "spouse"]
        support_phrases = ["who will help", "who will be helping", "who can help", "support person", "caregiver", "family member", "friend", "partner", "spouse", "someone who will", "help you out", "take care of"]
        
        has_support_keyword = any(word in content for word in support_keywords)
        has_support_phrase = any(phrase in content for phrase in support_phrases)
        
        print(f"  Support keywords found: {has_support_keyword}")
        print(f"  Support phrases found: {has_support_phrase}")
        
        if has_support_keyword:
            found_keywords = [word for word in support_keywords if word in content]
            print(f"  Found keywords: {found_keywords}")
        
        if has_support_phrase:
            found_phrases = [phrase for phrase in support_phrases if phrase in content]
            print(f"  Found phrases: {found_phrases}")
        
        # Check if this should mark support system as covered
        if has_support_keyword and has_support_phrase:
            print(f"  ✅ Should mark support system as covered")
        else:
            print(f"  ❌ Should NOT mark support system as covered")

if __name__ == "__main__":
    test_support_system_detection() 
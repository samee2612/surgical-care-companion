#!/usr/bin/env python3
"""
Test the question detection logic
"""

def detect_user_question(message):
    """Test version of the question detection function"""
    content = message.lower()
    
    # Question indicators
    question_words = ["what", "how", "when", "why", "where", "which", "can you", "could you", "would you"]
    surgery_keywords = ["surgery", "procedure", "operation", "recovery", "anesthesia", "hospital", "pain", "medication", "rehabilitation"]
    
    # Check for question marks
    has_question_mark = "?" in message
    
    # Check for question words
    has_question_word = any(word in content for word in question_words)
    
    # Check for surgery-related questions
    has_surgery_keyword = any(word in content for word in surgery_keywords)
    
    # If it's a question about surgery/recovery, it should be answered
    return (has_question_mark or has_question_word) and has_surgery_keyword

def test_question_detection():
    """Test various user messages to see if they're detected as questions"""
    
    test_cases = [
        # Assessment answers (should NOT be questions)
        ("yes its a good time", False),
        ("About a 7", False),
        ("I have trouble walking up stairs", False),
        ("My husband will help me", False),
        
        # Surgery questions (should be questions)
        ("What exactly happens in knee surgery?", True),
        ("How long does the surgery take?", True),
        ("What is the recovery time?", True),
        ("Can you tell me about the procedure?", True),
        ("What happens during the operation?", True),
        ("How much pain will I have after surgery?", True),
        ("What medications will I need?", True),
        ("When can I go back to work?", True),
        
        # Non-surgery questions (should NOT be questions for our purposes)
        ("What's the weather like?", False),
        ("How are you today?", False),
        ("Can you help me with something else?", False),
        
        # Mixed messages (should be questions)
        ("About a 7. But what exactly happens during knee replacement surgery?", True),
        ("My husband will help me. How long is the recovery?", True),
    ]
    
    print("🧪 Testing Question Detection Logic")
    print("=" * 50)
    
    for i, (message, expected) in enumerate(test_cases, 1):
        result = detect_user_question(message)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"\nTest {i}: {status}")
        print(f"Message: '{message}'")
        print(f"Expected: {expected}, Got: {result}")
        
        if result != expected:
            print(f"  ⚠️  This test case failed!")
    
    print(f"\n📊 Summary:")
    passed = sum(1 for _, expected in test_cases if detect_user_question(_) == expected)
    total = len(test_cases)
    print(f"Passed: {passed}/{total} tests")

if __name__ == "__main__":
    test_question_detection() 
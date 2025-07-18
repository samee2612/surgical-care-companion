#!/usr/bin/env python3
"""
Test if "knee arthroplasty" is detected as a surgery question
"""

def detect_user_question(message):
    """Test version of the question detection function"""
    content = message.lower()
    
    # Question indicators
    question_words = ["what", "how", "when", "why", "where", "which", "can you", "could you", "would you"]
    surgery_keywords = ["surgery", "procedure", "operation", "recovery", "anesthesia", "hospital", "pain", "medication", "rehabilitation", "arthroplasty"]
    
    # Check for question marks
    has_question_mark = "?" in message
    
    # Check for question words
    has_question_word = any(word in content for word in question_words)
    
    # Check for surgery-related questions
    has_surgery_keyword = any(word in content for word in surgery_keywords)
    
    # If it's a question about surgery/recovery, it should be answered
    return (has_question_mark or has_question_word) and has_surgery_keyword

def test_arthroplasty_detection():
    """Test if knee arthroplasty questions are detected"""
    
    test_messages = [
        "Can you briefly explain what happens in knee arthroplasty",
        "What happens during knee arthroplasty?",
        "How does knee arthroplasty work?",
        "Can you tell me about knee arthroplasty procedure?",
        "What is knee arthroplasty surgery?",
    ]
    
    print("🔍 Testing Knee Arthroplasty Detection")
    print("=" * 50)
    
    for i, message in enumerate(test_messages, 1):
        result = detect_user_question(message)
        print(f"\nTest {i}:")
        print(f"Message: '{message}'")
        print(f"Detected as surgery question: {result}")
        
        if not result:
            print("  ❌ This should be detected as a surgery question!")
            print("  💡 Adding 'arthroplasty' to surgery keywords would fix this")

if __name__ == "__main__":
    test_arthroplasty_detection() 
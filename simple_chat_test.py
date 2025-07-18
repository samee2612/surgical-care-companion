#!/usr/bin/env python3
"""
Simple Chat Test - Demonstrates the new conversation structure
"""

import random

def get_contextual_response(user_input: str, call_type: str, patient_name: str):
    """Generate contextual response based on user input and call type"""
    
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
        "initial_assessment": [
            f"How has your knee been feeling lately, {patient_name}?",
            f"What's your main concern about the upcoming surgery, {patient_name}?",
            f"Tell me about your daily activities - what's been challenging?",
            f"How are you managing with walking these days, {patient_name}?"
        ],
        "preparation_assessment": [
            f"How are your preparations coming along, {patient_name}?",
            f"What have you been working on to get ready for surgery?",
            f"How is your home setup progressing, {patient_name}?",
            f"What questions do you have about the next steps?"
        ],
        "final_assessment": [
            f"How are you feeling about tomorrow, {patient_name}?",
            f"What's going through your mind as we approach surgery day?",
            f"Is there anything you're still wondering about, {patient_name}?",
            f"How confident are you feeling about everything?"
        ],
        "education": [
            f"What would you like to know about your knee replacement, {patient_name}?",
            f"Have you been thinking about what to expect during recovery?",
            f"What aspects of the surgery are you most curious about?",
            f"How much do you know about the procedure so far, {patient_name}?"
        ],
        "preparation": [
            f"What area of preparation would you like to focus on today, {patient_name}?",
            f"How is your home getting ready for your recovery?",
            f"What equipment or supplies are you thinking about, {patient_name}?",
            f"Who will be helping you during your recovery?"
        ],
        "final_prep": [
            f"How are you feeling about being so close to surgery, {patient_name}?",
            f"What final preparations are you working on?",
            f"Is everything falling into place for you, {patient_name}?",
            f"How ready do you feel right now?"
        ],
        "final_logistics": [
            f"Let's make sure everything is set for tomorrow, {patient_name}.",
            f"How are you feeling about the timing and logistics?",
            f"Is your transportation all arranged, {patient_name}?",
            f"What time will you be leaving for the hospital tomorrow?"
        ],
        "enrollment": [
            f"Welcome to our surgical support program, {patient_name}!",
            f"I'm here to support you through your surgical journey.",
            f"How are you feeling about starting this preparation process?",
            f"What would be most helpful for you right now, {patient_name}?"
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
    
    # Positive indicators
    positive_words = ["good", "great", "fine", "ready", "prepared", "confident", "excited", "yes", "sure", "okay"]
    # Concern indicators  
    concern_words = ["worried", "scared", "nervous", "anxious", "concerned", "afraid", "unsure", "confused"]
    # Pain indicators
    pain_words = ["pain", "hurt", "ache", "sore", "painful", "discomfort", "stiff"]
    
    # Choose appropriate response category
    if any(word in user_input_lower for word in positive_words):
        base_response = random.choice(positive_responses)
        follow_up = random.choice(conversation_starters.get(call_type, conversation_starters["initial_assessment"]))
    elif any(word in user_input_lower for word in concern_words):
        base_response = random.choice(concern_responses)
        follow_up = "What specific aspect would you like to discuss?"
    elif any(word in user_input_lower for word in pain_words):
        base_response = random.choice(pain_responses)
        follow_up = "Can you tell me more about what you're experiencing?"
    else:
        base_response = random.choice(general_responses)
        follow_up = random.choice(conversation_starters.get(call_type, conversation_starters["initial_assessment"]))
    
    # Add contextual bridge based on call type
    call_purpose = call_purposes.get(call_type, "helping you prepare")
    bridge = f" Since we're {call_purpose}, {follow_up}"
    
    return f"{base_response}{bridge}"


def main():
    """Main test function"""
    print("🤖 Surgical Care Companion - New Conversation System")
    print("=" * 60)
    print("This demonstrates the new dynamic conversation structure that:")
    print("• Provides contextual responses based on call type")
    print("• Uses different response patterns for different emotions")
    print("• Generates unique follow-up questions each time")
    print("• Avoids repetitive 'Can you tell me more about that?' responses")
    print()
    
    # Test scenarios
    scenarios = [
        {
            "call_type": "education",
            "patient_name": "Bob Martinez",
            "messages": [
                "Hello Bob Martinez! This is your Healthsense surgical preparation assistant. I'm calling to help you prepare for your upcoming knee replacement surgery scheduled for July 30, 2025. This will be a comprehensive assessment to ensure you're ready for a successful surgery and recovery. Shall we begin?",
                "yes",
                "I am worried about the surgery",
                "My knee really hurts",
                "I feel ready",
                "I have some questions",
                "okay"
            ]
        },
        {
            "call_type": "initial_assessment", 
            "patient_name": "Sarah Johnson",
            "messages": [
                "yes",
                "I'm feeling anxious",
                "The pain is terrible",
                "I'm prepared"
            ]
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📞 Call Type: {scenario['call_type'].upper()}")
        print(f"👤 Patient: {scenario['patient_name']}")
        print("-" * 40)
        
        for i, message in enumerate(scenario['messages']):
            if i == 0:
                print(f"🤖 Assistant: {message}")
                continue
                
            response = get_contextual_response(message, scenario['call_type'], scenario['patient_name'])
            print(f"👤 Patient: {message}")
            print(f"🤖 Assistant: {response}")
            print()
    
    print("\n✅ Test Complete!")
    print("The new conversation system provides:")
    print("• Dynamic, contextual responses")
    print("• Call-type specific conversation flow")
    print("• Varied responses to avoid repetition")
    print("• Natural, empathetic communication")


if __name__ == "__main__":
    main() 
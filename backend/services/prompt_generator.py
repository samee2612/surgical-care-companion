# surgicalcompanian/backend/services/prompt_generator.py
import json # Ensure json is imported
import os   # Ensure os is imported
import re   # Ensure re is imported

class PromptGenerator:
    # --- Base System Prompt (for persona and general rules) ---
    BASE_SYSTEM_PROMPT = """
    You are a caring surgical care coordinator having a natural conversation with a patient.
    Your goal is to gather health information while being genuinely empathetic and responsive.
    
    Key principles:
    - Respond specifically to what the patient says, don't just acknowledge generically
    - Show genuine empathy for their concerns, pain, or limitations
    - Make medical connections when appropriate (e.g., "That level of pain must make daily tasks really challenging")
    - Use natural, conversational language - avoid robotic clinical phrases
    - Be warm but professional, like a caring healthcare professional
    - Keep responses focused but not rushed (2-4 sentences max)
    """

    # --- LLM for NLU Extraction Prompt ---
    def generate_nlu_prompt(self, conversation_history: list, user_message: str, report: dict) -> list:
        """
        Generates a prompt for the NLU model to extract structured data from the user's message.
        Do not repeat questions if the information is already provided in the `extracted_report` JSON.
        """
        # The NLU prompt is usually a single user message with specific instructions.
        # The `conversation_history` here is used to give context to the LLM for NLU.
        
        # Format conversation history for better LLM understanding if it needs to see it.
        # This is a key change: converting {"role": "x", "content": "y"} to {"role": "x", "parts": [{"text": "y"}]}
        formatted_conv_history_for_llm = []
        for turn in conversation_history:
            # Gemini expects 'model' for 'assistant' role
            role = "model" if turn["role"] == "assistant" else turn["role"]
            formatted_conv_history_for_llm.append({"role": role, "parts": [{"text": turn["content"]}]})


        nlu_instruction_text = (
            "You are an NLU (Natural Language Understanding) system. Your ONLY job is to extract intent and entities from user messages.\n"
            "IMPORTANT: Return ONLY valid JSON. No other text, no explanations, no conversational responses.\n"
            "Extract intent and entities from user message.\n"
            "Valid intents: ready_to_begin, confirm_yes, confirm_no, report_pain, difficult_activities, identify_helper, home_safety_response, equipment_response, medication_response, unknown\n"
            "Examples:\n"
            "User: 'Yes' → {\"intent\": \"confirm_yes\", \"entities\": {}}\n"
            "User: 'My pain is 9' → {\"intent\": \"report_pain\", \"entities\": {\"pain_level\": 9}}\n"
            "User: 'standing and walking are hard' → {\"intent\": \"difficult_activities\", \"entities\": {\"activities\": \"standing, walking\"}}\n"
            "User: 'my wife helps me' → {\"intent\": \"identify_helper\", \"entities\": {\"helper\": \"wife\"}}\n"
            "User: 'I removed the rugs and set up my bedroom' → {\"intent\": \"home_safety_response\", \"entities\": {\"trip_hazards\": \"removed\", \"recovery_space\": \"prepared\"}}\n"
            "User: 'I have the toilet seat but need to get the grabber' → {\"intent\": \"equipment_response\", \"entities\": {\"toilet_seat\": \"obtained\", \"grabber_tool\": \"needed\"}}\n"
            "User: 'I take aspirin daily' → {\"intent\": \"medication_response\", \"entities\": {\"blood_thinners\": \"aspirin\"}}\n"
            "User: 'No, I don't take any blood thinners' → {\"intent\": \"medication_response\", \"entities\": {\"blood_thinners\": \"none\"}}\n"
            "User: 'I'm allergic to penicillin' → {\"intent\": \"medication_response\", \"entities\": {\"allergies\": \"penicillin\"}}\n"
            "User: 'I have diabetes' → {\"intent\": \"medication_response\", \"entities\": {\"medical_conditions\": \"diabetes\"}}\n"
            "User: 'yes taking aspirin' → {\"intent\": \"medication_response\", \"entities\": {\"blood_thinners\": \"aspirin\"}}\n"
            f"Current data: {json.dumps(report)}\n"
            "User message to analyze:"
        )
        
        # The prompt for NLU should send the system prompt, then conversation history for context, then the latest user message
        messages = [
            {"role": "user", "parts": [{"text": nlu_instruction_text}]} # Initial instruction to LLM
        ]
        # Add historical turns if useful for NLU context (otherwise LLM might miss context for entity resolution)
        messages.extend(formatted_conv_history_for_llm) 
        # Add the very last user message to be analyzed
        messages.append({"role": "user", "parts": [{"text": user_message}]})

        return messages


    # --- LLM for Question Generation / Conversational Response ---
    def generate_agent_response_prompt(self, conversation_history: list, current_stage: str, patient_name: str, surgery_date: str, report: dict) -> list:
        """
        Generates a prompt for Gemini Flash to provide the next empathetic response or question.
        
        Args:
            conversation_history: List of {"role": "user/assistant", "content": "..."} turns.
            current_stage: The current stage of the call (e.g., "PainAssessment").
            patient_name: Patient's first name.
            surgery_date: Patient's surgery date.
            report: Current extracted clinical data JSON.
            
        Returns: A list of messages for the Gemini API.
        """
        # Format conversation history for the LLM
        # This is the key change: converting {"role": "x", "content": "y"} to {"role": "x", "parts": [{"text": "y"}]}
        formatted_conv_history_for_llm = []
        for turn in conversation_history:
            # Gemini expects 'model' for 'assistant' role
            role = "model" if turn["role"] == "assistant" else turn["role"]
            formatted_conv_history_for_llm.append({"role": role, "parts": [{"text": turn["content"]}]})

        # Build the initial system prompt text (as a string)
        system_prompt_text = (
            f"{self.BASE_SYSTEM_PROMPT}\n" # Include base persona
                "**Current Context for Agent's Next Response:**\n"
                f"- Patient Name: {patient_name}\n"
                f"- Surgery Date: {surgery_date}\n"
                f"- Call Stage: {current_stage}\n"
            f"- Extracted report so far: {json.dumps(report)}\n"
                "**Instructions for Next Agent Response:**\n"
            "Generate a natural, empathetic response that:\n"
            "1. FIRST: Directly address what the patient just said - if they ask for help/suggestions, provide it\n"
            "2. Shows understanding and empathy for their situation\n"
            "3. If they ask questions or need help, answer that BEFORE moving to the next assessment topic\n"
            "4. Only move to next assessment question if their immediate needs are addressed\n"
            "5. Keep responses helpful but professional (max 80 tokens if providing suggestions)\n"
            "6. Be responsive to their requests - don't ignore what they're asking for\n"
            "Always prioritize being helpful over following a rigid script.\n"
        )
        
        # Start the messages list with the system prompt (as a user role for context)
        messages = [
            {"role": "user", "parts": [{"text": system_prompt_text}]}
        ]
        
        # Add the actual conversation history (user/assistant turns) to the prompt
        messages.extend(formatted_conv_history_for_llm)

        # Add specific instructions based on the current stage as the LAST 'user' turn
        stage_instruction = ""
        if current_stage == "Greeting":
            # Check if this is a preparation call to provide context from previous call
            if "preparation_call" in report:
                stage_instruction = f"Your task is to provide a brief, structured greeting for the preparation call. Use this exact format: 'Hello {patient_name}, with your weekly preparation check-in.'"
            else:
                stage_instruction = "Your task is to provide the warm greeting during their first scheduled check-in. Ask if they are ready to begin."
        # elif current_stage == "AwaitingReadinessConfirmation":
        #     stage_instruction = "The patient just responded to 'Ready to begin?'. Acknowledge their response and transition to confirming their date og ."
        elif current_stage == "SurgeryDateConfirmation":
            stage_instruction = f"Your task is to confirm the patient's surgery date with them (which is {surgery_date})."
        elif current_stage == "PainAssessment":
            stage_instruction = "Ask about their current pain level on a scale of 0-10. If they mention specific pain experiences, acknowledge those details and show empathy for their discomfort before asking for the numerical rating."
        elif current_stage == "MobilityAssessment":
            stage_instruction = "Based on their pain level, ask what specific activities are challenging for them. If they mention high pain, acknowledge how that must affect their daily life. Be empathetic about mobility limitations."
        elif current_stage == "SupportSystemAssessment":
            stage_instruction = "Ask about their support system at home. If they mention specific people or challenges, respond with understanding about how important good support is for recovery. Acknowledge their support situation before moving to closing."
        elif current_stage == "HomeSafetyAssessment":
            # Check what's already covered and ask about the next item
            prep_data = report.get("preparation_call", {})
            if "recovery_space_prepared" not in prep_data:
                stage_instruction = "Ask about recovery space setup. Use this format: 'To prevent falls, it's important to remove trip hazards like loose rugs. Have you had a chance to prepare your recovery space?'"
            elif "trip_hazards_removed" not in prep_data:
                stage_instruction = "Acknowledge their recovery space setup, then ask about trip hazards. Example: 'That sounds like a smart setup for your recovery. Now, to help prevent any falls, have you had a chance to remove trip hazards like loose rugs or clear pathways?'"
            else:
                stage_instruction = "Both home safety items are covered. Acknowledge their thorough preparation and transition to equipment questions."
        elif current_stage == "MedicalEquipmentAssessment":
            # Check what's already covered and ask about the next item
            prep_data = report.get("preparation_call", {})
            assistive_tools = prep_data.get("assistive_tools_list", [])
            
            if "raised toilet seat" not in assistive_tools and "toilet seat" not in assistive_tools:
                stage_instruction = "Ask about raised toilet seat and grabber tool. Use this format: 'Have you obtained a raised toilet seat and a grabber tool? These are essential for following your hip precautions after surgery.'"
            elif "grabber tool" not in assistive_tools and "grabber" not in assistive_tools:
                stage_instruction = "Acknowledge their toilet seat status and ask about the grabber tool. Example: 'That's great you have the raised toilet seat. Another essential tool is a grabber or reacher - have you been able to get one of those?'"
            else:
                stage_instruction = "Both essential equipment items are covered. Answer any remaining questions they have, then acknowledge their thorough equipment preparation and transition to medication review."
        elif current_stage == "MedicationReview":
            prep_data = report.get("preparation_call", {})
            blood_thinners = prep_data.get("blood_thinning_medications", [])
            allergies = prep_data.get("allergies_list", [])
            medical_conditions = prep_data.get("medical_conditions_list", [])
            
            if not blood_thinners:
                stage_instruction = "Ask about blood-thinning medications. Use this format: 'Let's review medications. Are you currently taking any blood-thinning medication, such as Aspirin, Warfarin, or Eliquis?'"
            elif not allergies:
                stage_instruction = "Acknowledge their medication response, then ask about allergies. Use this format: 'Thank you for that information. Do you have any allergies to medications, latex, or other materials that we should be aware of?'"
            elif not medical_conditions:
                stage_instruction = "Acknowledge their allergy response, then ask about medical conditions. Use this format: 'Thank you. Do you have any medical conditions like diabetes, heart problems, or high blood pressure that we should know about?'"
            else:
                stage_instruction = "All medical review items are covered. Acknowledge their thorough medical information and transition to closing."
        elif current_stage == "Closing":
            # Check if this is a preparation call to use different closing
            if "preparation_call" in report:
                stage_instruction = "Your task is to deliver the closing message for the preparation call. Use the exact closing script: 'Thank you for taking the time to prepare so thoughtfully. You're doing everything right to ensure a smooth recovery. That gives our team confidence in your preparation. Your next call will be closer to your surgery date to confirm final logistics. Take care!'"
            else:
                stage_instruction = "Your task is to deliver the closing message for the call. Use the exact closing script: 'Thank you so much for being patient with all my questions today. I know dealing with that level of pain isn't easy, but I want to assure you that once you're through the surgery, you should feel significant relief. That gives our team a great baseline to work with. Your next call will be in about a week to discuss home preparation. Take care, and have a good day!'"
        else:
            stage_instruction = "Acknowledge the patient and transition smoothly to the next logical step based on conversation history and current stage."

        messages.append({"role": "user", "parts": [{"text": stage_instruction}]}) # Final instruction for LLM

        return messages
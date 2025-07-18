"""
Voice Chat API for TKA Patients
Enhanced with call context system for structured conversations
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import json

from backend.database.connection import get_db
from backend.models.patient import Patient
from backend.models.call_session import CallSession
from backend.services.voice_chat import get_chat_service
from backend.services.call_context_service import CallContextService
from backend.services.context_injection_service import ContextInjectionService
from backend.utils.conversation_utils import get_covered_areas

router = APIRouter()

class ContextualChatMessage(BaseModel):
    message: str
    patient_id: str
    call_session_id: str
    # Removed conversation_history - now handled automatically by backend

class ChatResponse(BaseModel):
    response: str
    context_metadata: dict

class StartCallRequest(BaseModel):
    patient_id: str
    call_session_id: str

class StartCallResponse(BaseModel):
    initial_message: str
    call_context: dict

class ConverseRequest(BaseModel):
    patient_id: str
    call_session_id: str
    message: Optional[str] = None

# Initialize context services
context_service = CallContextService()
injection_service = ContextInjectionService()

@router.post("/contextual-chat", response_model=ChatResponse)
async def contextual_chat(chat_msg: ContextualChatMessage, db: Session = Depends(get_db)):
    """Context-aware chat using call session information with automatic conversation history"""
    try:
        # Get patient and call session
        patient = db.query(Patient).filter(Patient.id == chat_msg.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        call_session = db.query(CallSession).filter(CallSession.id == chat_msg.call_session_id).first()
        if not call_session:
            raise HTTPException(status_code=404, detail="Call session not found")
        
        # Load conversation history from database (or start new)
        history_str = getattr(call_session, "conversation_history", None)
        if history_str is not None and history_str != "":
            history = json.loads(history_str)
        else:
            history = []
        
        # Append the new user message
        history.append({"role": "user", "content": chat_msg.message})
        
        # Use the utility function to check which areas are covered
        call_type = str(call_session.call_type)
        covered_data = get_covered_areas(history, call_type)
        
        # Define area names and order based on call type
        if call_type == "preparation":
            area_names = {
                "home_safety": "home safety and trip hazard removal",
                "equipment_supplies": "equipment and supplies like raised toilet seat and grabber tool",
                "medical_preparation": "medical preparation and blood-thinning medications",
                "support_verification": "support system verification"
            }
            order = ["home_safety", "equipment_supplies", "medical_preparation", "support_verification"]
            
            # Extract simple boolean coverage for backward compatibility
            covered = {area: covered_data[area] for area in area_names.keys()}
        else:
            area_names = {
                "surgery_confirmation": "confirming their upcoming surgery date and how they feel about it",
                "pain_level": "their current pain level on a scale of 1 to 10",
                "activity_limitations": "any activities that are difficult for them right now because of their knee",
                "support_system": "whether they have someone who will be able to help them out after their surgery"
            }
            order = ["surgery_confirmation", "pain_level", "activity_limitations", "support_system"]
            covered = covered_data
        
        # Helper to detect if user is asking a question
        def detect_user_question(message):
            """Detect if the user is asking a question that needs to be answered"""
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
        
        # Generate call context (for context_metadata)
        call_context = context_service.get_call_context(patient, call_session)
        prompt_data = injection_service.generate_llm_prompt(call_context, is_initial_call=False)
        chat_service = get_chat_service()
        
        # Helper to format last few turns for context
        def format_history(history):
            return "\n".join([f"{turn['role'].capitalize()}: {turn['content']}" for turn in history])
        
        # Prevent repeated wrap-up
        if getattr(call_session, "call_status", None) == "completed":
            # Check if user is asking a question even though call is completed
            user_is_asking_question = detect_user_question(chat_msg.message)
            
            if user_is_asking_question:
                # Answer the question and keep conversation open for follow-ups
                context_turns = history[-4:] if len(history) >= 4 else history
                prompt = (
                    f"Conversation so far:\n"
                    f"{format_history(context_turns)}\n\n"
                    f"The patient just asked: '{chat_msg.message}'\n"
                    f"Answer their question in a helpful and informative way, then use the EXACT wrap-up script from your system instructions: 'Great progress. Your next call will be closer to your surgery date to confirm final logistics.'\n"
                    f"Output only the response you would say to the patient."
                )
                response = chat_service.generate_response(prompt)
                history.append({"role": "assistant", "content": response})
                setattr(call_session, "conversation_history", json.dumps(history))
                db.commit()
                return ChatResponse(response=response, context_metadata=prompt_data["context_metadata"])
            else:
                # Check if user wants to end the conversation
                end_keywords = ["goodbye", "bye", "end", "finish", "that's all", "no more questions", "thank you"]
                if any(keyword in chat_msg.message.lower() for keyword in end_keywords):
                    # User wants to end the conversation
                    goodbye = f"Thank you, {patient.name}. If you have any more questions, feel free to reach out. Goodbye!"
                    history.append({"role": "assistant", "content": goodbye})
                    setattr(call_session, "conversation_history", json.dumps(history))
                    db.commit()
                    return ChatResponse(response=goodbye, context_metadata={})
                else:
                    # User might be asking a question that wasn't detected, or making a statement
                    # Let the LLM handle it naturally
                    context_turns = history[-4:] if len(history) >= 4 else history
                    prompt = (
                        f"Conversation so far:\n"
                        f"{format_history(context_turns)}\n\n"
                        f"The patient just said: '{chat_msg.message}'\n"
                        f"Respond naturally and helpfully. If they're asking a question, answer it. If they're making a statement, acknowledge it and ask if they have any questions.\n"
                        f"Output only the response you would say to the patient."
                    )
                    response = chat_service.generate_response(prompt)
                    history.append({"role": "assistant", "content": response})
                    setattr(call_session, "conversation_history", json.dumps(history))
                    db.commit()
                    return ChatResponse(response=response, context_metadata=prompt_data["context_metadata"])
        else:
            # Check if user is asking a question
            user_is_asking_question = detect_user_question(chat_msg.message)
            
            if all(covered.values()):
                if user_is_asking_question:
                    # Answer the question and then wrap up
                    context_turns = history[-4:] if len(history) >= 4 else history
                    prompt = (
                        f"Conversation so far:\n"
                        f"{format_history(context_turns)}\n\n"
                        f"The patient just asked: '{chat_msg.message}'\n"
                        f"Answer their question in a helpful and informative way, then use the wrap-up script from your system instructions.\n"
                        f"Output only the response you would say to the patient."
                    )
                    response = chat_service.generate_response(prompt)
                    history.append({"role": "assistant", "content": response})
                    setattr(call_session, "conversation_history", json.dumps(history))
                    setattr(call_session, "call_status", "completed")
                    db.commit()
                    return ChatResponse(response=response, context_metadata=prompt_data["context_metadata"])
                else:
                    # Standard wrap-up - use system prompt wrap-up script
                    context_turns = history[-4:] if len(history) >= 4 else history
                    prompt = (
                        f"Conversation so far:\n"
                        f"{format_history(context_turns)}\n\n"
                        f"All areas have been covered. Use the EXACT wrap-up script from your system instructions: 'Great progress. Your next call will be closer to your surgery date to confirm final logistics.'\n"
                        f"Output only the response you would say to the patient."
                    )
                    response = chat_service.generate_response(prompt)
                    history.append({"role": "assistant", "content": response})
                    setattr(call_session, "conversation_history", json.dumps(history))
                    setattr(call_session, "call_status", "completed")
                    db.commit()
                    return ChatResponse(response=response, context_metadata=prompt_data["context_metadata"])
            else:
                # Find the next uncovered area
                for area in order:
                    if not covered[area]:
                        last_user_message = history[-1]["content"] if history and history[-1]["role"] == "user" else ""
                        context_turns = history[-4:] if len(history) >= 4 else history
                        
                        # For preparation calls, check if we need more questions in current area
                        if call_type == "preparation":
                            questions_asked = covered_data.get(f"{area}_questions_asked", 0)
                            questions_answered = covered_data.get(f"{area}_questions_answered", 0)
                            
                            # If this area is already covered, move to the next uncovered area
                            if covered[area]:
                                continue  # Skip to next area
                            # Otherwise, continue asking questions in this area
                                if user_is_asking_question:
                                    # Answer the question and then ask the next question in current area
                                    prompt = (
                                        f"Conversation so far:\n"
                                        f"{format_history(context_turns)}\n\n"
                                        f"The patient just said: '{last_user_message}'\n"
                                        f"This appears to be both an answer to your previous question AND a new question from the patient.\n"
                                        f"1. First, answer their question in a helpful and informative way\n"
                                        f"2. Then, acknowledge their previous answer\n"
                                        f"3. Finally, ask another question about {area_names[area]} (this is question #{questions_asked + 1} for this area)\n"
                                        f"Output only the response you would say to the patient."
                                    )
                                else:
                                    # Standard assessment question for current area
                                    prompt = (
                                        f"Conversation so far:\n"
                                        f"{format_history(context_turns)}\n\n"
                                        f"The patient just said: '{last_user_message}'.\n"
                                        f"In a warm and efficient way, acknowledge their answer and ask another question about {area_names[area]} (this is question #{questions_asked + 1} for this area).\n"
                                        f"Output only the next message you would say to the patient."
                                    )

                        else:
                            # Clinical assessment logic (existing)
                            if user_is_asking_question:
                                # Answer the question and then ask the next assessment question
                                prompt = (
                                    f"Conversation so far:\n"
                                    f"{format_history(context_turns)}\n\n"
                                    f"The patient just said: '{last_user_message}'\n"
                                    f"This appears to be both an answer to your previous question AND a new question from the patient.\n"
                                    f"1. First, answer their question in a helpful and informative way\n"
                                    f"2. Then, acknowledge their previous answer\n"
                                    f"3. Finally, ask the next question about {area_names[area]}\n"
                                    f"Output only the response you would say to the patient."
                                )
                            else:
                                # Standard assessment question
                                prompt = (
                                    f"Conversation so far:\n"
                                    f"{format_history(context_turns)}\n\n"
                                    f"The patient just said: '{last_user_message}'.\n"
                                    f"In a warm and efficient way, acknowledge their answer and ask the next question about {area_names[area]}.\n"
                                    f"Output only the next message you would say to the patient."
                                )
                            
                            question = chat_service.generate_response(prompt)
                            history.append({"role": "assistant", "content": question})
                            setattr(call_session, "conversation_history", json.dumps(history))
                            db.commit()
                            return ChatResponse(response=question, context_metadata=prompt_data["context_metadata"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Contextual chat error: {str(e)}")

@router.post("/start-call", response_model=StartCallResponse)
async def start_call(request: StartCallRequest, db: Session = Depends(get_db)):
    """Start a structured call with proper context injection"""
    try:
        # Get patient and call session
        patient = db.query(Patient).filter(Patient.id == request.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        call_session = db.query(CallSession).filter(CallSession.id == request.call_session_id).first()
        if not call_session:
            raise HTTPException(status_code=404, detail="Call session not found")
        
        # Generate call context
        call_context = context_service.get_call_context(patient, call_session)
        
        # Generate initial prompt (start of conversation)
        prompt_data = injection_service.generate_llm_prompt(call_context, is_initial_call=True)
        
        # Get chat service and start conversation
        chat_service = get_chat_service()
        # Send both system and user prompts as initial messages
        messages = [
            {"role": "system", "content": prompt_data["system_prompt"]},
            {"role": "user", "content": prompt_data["user_prompt"]}
        ]
        responses = chat_service.start_contextual_conversation(messages)
        initial_response = responses[0] if responses else ""
        
        # Initialize conversation history with the first assistant message
        history = [{"role": "assistant", "content": initial_response}]
        setattr(call_session, "conversation_history", json.dumps(history))
        
        # Update call session status
        setattr(call_session, "call_status", "in_progress")
        setattr(call_session, "actual_call_start", datetime.now())
        db.commit()
        
        return StartCallResponse(
            initial_message=initial_response,
            call_context={
                "call_type": call_context.call_type.value,
                "days_from_surgery": call_context.days_from_surgery,
                "estimated_duration": call_context.estimated_duration_minutes,
                "focus_areas": call_context.focus_areas
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting call: {str(e)}")

@router.post("/converse", response_model=ChatResponse)
async def converse(request: ConverseRequest, db: Session = Depends(get_db)):
    """
    Unified endpoint for starting and continuing a conversation.
    If no conversation history or message, starts the call.
    Otherwise, continues the conversation.
    """
    try:
        # Fetch patient and call session
        patient = db.query(Patient).filter(Patient.id == request.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        call_session = db.query(CallSession).filter(CallSession.id == request.call_session_id).first()
        if not call_session:
            raise HTTPException(status_code=404, detail="Call session not found")

        # Load conversation history
        history_str = getattr(call_session, "conversation_history", None)
        if history_str is not None and history_str != "":
            history = json.loads(history_str)
        else:
            history = []

        # Generate call context and prompt data
        call_context = context_service.get_call_context(patient, call_session)
        chat_service = get_chat_service()
        prompt_data = injection_service.generate_llm_prompt(call_context, is_initial_call=False)

        # Use the utility function to check which areas are covered
        call_type = str(call_session.call_type)
        covered_data = get_covered_areas(history, call_type)
        
        # Define area names and order based on call type
        if call_type == "preparation":
            area_names = {
                "home_safety": "home safety and trip hazard removal",
                "equipment_supplies": "equipment and supplies like raised toilet seat and grabber tool",
                "medical_preparation": "medical preparation and blood-thinning medications",
                "support_verification": "support system verification"
            }
            order = ["home_safety", "equipment_supplies", "medical_preparation", "support_verification"]
        else:
            area_names = {
                "surgery_confirmation": "confirming their upcoming surgery date and how they feel about it",
                "pain_level": "their current pain level on a scale of 1 to 10",
                "activity_limitations": "any activities that are difficult for them right now because of their knee",
                "support_system": "whether they have someone who will be able to help them out after their surgery"
            }
            order = ["surgery_confirmation", "pain_level", "activity_limitations", "support_system"]

        # Helper to detect if user is asking a question
        def detect_user_question(message):
            """Detect if the user is asking a question that needs to be answered"""
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

        # Helper to format last few turns for context
        def format_history(history):
            return "\n".join([f"{turn['role'].capitalize()}: {turn['content']}" for turn in history])

        # Prevent repeated wrap-up
        if getattr(call_session, "call_status", None) == "completed":
            # Check if user is asking a question even though call is completed
            user_is_asking_question = detect_user_question(request.message)
            
            if user_is_asking_question:
                # Answer the question and keep conversation open for follow-ups
                context_turns = history[-4:] if len(history) >= 4 else history
                prompt = (
                    f"Conversation so far:\n"
                    f"{format_history(context_turns)}\n\n"
                    f"The patient just asked: '{request.message}'\n"
                    f"Answer their question in a helpful and informative way. Be thorough and educational.\n"
                    f"After answering, ask if they have any other questions or if there's anything else they'd like to know.\n"
                    f"Output only the response you would say to the patient."
                )
                response = chat_service.generate_response(prompt)
                history.append({"role": "assistant", "content": response})
                setattr(call_session, "conversation_history", json.dumps(history))
                db.commit()
                return ChatResponse(response=response, context_metadata=prompt_data["context_metadata"])
            else:
                # Check if user wants to end the conversation
                end_keywords = ["goodbye", "bye", "end", "finish", "that's all", "no more questions", "thank you"]
                if request.message and any(keyword in request.message.lower() for keyword in end_keywords):
                    # User wants to end the conversation
                    goodbye = f"Thank you, {patient.name}. If you have any more questions, feel free to reach out. Goodbye!"
                    history.append({"role": "assistant", "content": goodbye})
                    setattr(call_session, "conversation_history", json.dumps(history))
                    db.commit()
                    return ChatResponse(response=goodbye, context_metadata={})
                else:
                    # User might be asking a question that wasn't detected, or making a statement
                    # Let the LLM handle it naturally
                    context_turns = history[-4:] if len(history) >= 4 else history
                    prompt = (
                        f"Conversation so far:\n"
                        f"{format_history(context_turns)}\n\n"
                        f"The patient just said: '{request.message}'\n"
                        f"Respond naturally and helpfully. If they're asking a question, answer it. If they're making a statement, acknowledge it and ask if they have any questions.\n"
                        f"Output only the response you would say to the patient."
                    )
                    response = chat_service.generate_response(prompt)
                    history.append({"role": "assistant", "content": response})
                    setattr(call_session, "conversation_history", json.dumps(history))
                    db.commit()
                    return ChatResponse(response=response, context_metadata=prompt_data["context_metadata"])
        else:
            # If no history or no message, start the conversation
            if not history or not request.message:
                # Initial call
                prompt_data = injection_service.generate_llm_prompt(call_context, is_initial_call=True)
                messages = [
                    {"role": "system", "content": prompt_data["system_prompt"]},
                    {"role": "user", "content": prompt_data["user_prompt"]}
                ]
                responses = chat_service.start_contextual_conversation(messages)
                initial_response = responses[0] if responses else ""
                history = [{"role": "assistant", "content": initial_response}]
                setattr(call_session, "conversation_history", json.dumps(history))
                setattr(call_session, "call_status", "in_progress")
                setattr(call_session, "actual_call_start", datetime.now())
                db.commit()
                return ChatResponse(response=initial_response, context_metadata=prompt_data["context_metadata"])
            else:
                # Continue conversation
                history.append({"role": "user", "content": request.message})
                prompt_data = injection_service.generate_llm_prompt(call_context, is_initial_call=False)
                
                # Extract simple boolean coverage for backward compatibility
                if call_type == "preparation":
                    covered = {area: covered_data[area] for area in ["home_safety", "equipment_supplies", "medical_preparation", "support_verification"]}
                else:
                    covered = covered_data
                
                # Check if user is asking a question
                user_is_asking_question = detect_user_question(request.message)
                
                if all(covered.values()):
                    if user_is_asking_question:
                        # Answer the question and then wrap up
                        context_turns = history[-4:] if len(history) >= 4 else history
                        prompt = (
                            f"Conversation so far:\n"
                            f"{format_history(context_turns)}\n\n"
                            f"The patient just asked: '{request.message}'\n"
                            f"Answer their question in a helpful and informative way, then use the EXACT wrap-up script from your system instructions: 'Great progress. Your next call will be closer to your surgery date to confirm final logistics.'\n"
                            f"Output only the response you would say to the patient."
                        )
                        response = chat_service.generate_response(prompt)
                        history.append({"role": "assistant", "content": response})
                        setattr(call_session, "conversation_history", json.dumps(history))
                        setattr(call_session, "call_status", "completed")
                        db.commit()
                        return ChatResponse(response=response, context_metadata=prompt_data["context_metadata"])
                    else:
                        # Standard wrap-up - use system prompt wrap-up script
                        context_turns = history[-4:] if len(history) >= 4 else history
                        prompt = (
                            f"Conversation so far:\n"
                            f"{format_history(context_turns)}\n\n"
                            f"All areas have been covered. Use the EXACT wrap-up script from your system instructions: 'Great progress. Your next call will be closer to your surgery date to confirm final logistics.'\n"
                            f"Output only the response you would say to the patient."
                        )
                        response = chat_service.generate_response(prompt)
                        history.append({"role": "assistant", "content": response})
                        setattr(call_session, "conversation_history", json.dumps(history))
                        setattr(call_session, "call_status", "completed")
                        db.commit()
                        return ChatResponse(response=response, context_metadata=prompt_data["context_metadata"])
                else:
                    # Find the next uncovered area
                    for area in order:
                        if not covered[area]:
                            last_user_message = history[-1]["content"] if history and history[-1]["role"] == "user" else ""
                            context_turns = history[-4:] if len(history) >= 4 else history
                            
                            # For preparation calls, check if we need more questions in current area
                            if call_type == "preparation":
                                questions_asked = covered_data.get(f"{area}_questions_asked", 0)
                                questions_answered = covered_data.get(f"{area}_questions_answered", 0)
                                
                                # If we haven't asked enough questions for this area, continue with it
                                if questions_asked < 3:  # Ask up to 3 questions per area
                                    if user_is_asking_question:
                                        # Answer the question and then ask the next question in current area
                                        prompt = (
                                            f"Conversation so far:\n"
                                            f"{format_history(context_turns)}\n\n"
                                            f"The patient just said: '{last_user_message}'\n"
                                            f"This appears to be both an answer to your previous question AND a new question from the patient.\n"
                                            f"1. First, answer their question in a helpful and informative way\n"
                                            f"2. Then, acknowledge their previous answer\n"
                                            f"3. Finally, ask another question about {area_names[area]} (this is question #{questions_asked + 1} for this area)\n"
                                            f"Output only the response you would say to the patient."
                                        )
                                        response = chat_service.generate_response(prompt)
                                        history.append({"role": "assistant", "content": response})
                                        setattr(call_session, "conversation_history", json.dumps(history))
                                        db.commit()
                                        return ChatResponse(response=response, context_metadata=prompt_data["context_metadata"])
                                    else:
                                        # Standard assessment question for current area
                                        prompt = (
                                            f"Conversation so far:\n"
                                            f"{format_history(context_turns)}\n\n"
                                            f"The patient just said: '{last_user_message}'.\n"
                                            f"In a warm and efficient way, acknowledge their answer and ask another question about {area_names[area]} (this is question #{questions_asked + 1} for this area).\n"
                                            f"Output only the next message you would say to the patient."
                                        )
                                        response = chat_service.generate_response(prompt)
                                        history.append({"role": "assistant", "content": response})
                                        setattr(call_session, "conversation_history", json.dumps(history))
                                        db.commit()
                                        return ChatResponse(response=response, context_metadata=prompt_data["context_metadata"])
                                else:
                                    # We've asked enough questions for this area, move to next
                                    if user_is_asking_question:
                                        # Answer the question and then ask the next assessment question
                                        prompt = (
                                            f"Conversation so far:\n"
                                            f"{format_history(context_turns)}\n\n"
                                            f"The patient just said: '{last_user_message}'\n"
                                            f"This appears to be both an answer to your previous question AND a new question from the patient.\n"
                                            f"1. First, answer their question in a helpful and informative way\n"
                                            f"2. Then, acknowledge their previous answer\n"
                                            f"3. Finally, ask the next question about {area_names[area]}\n"
                                            f"Output only the response you would say to the patient."
                                        )
                                        response = chat_service.generate_response(prompt)
                                        history.append({"role": "assistant", "content": response})
                                        setattr(call_session, "conversation_history", json.dumps(history))
                                        db.commit()
                                        return ChatResponse(response=response, context_metadata=prompt_data["context_metadata"])
                                    else:
                                        # Standard assessment question
                                        prompt = (
                                            f"Conversation so far:\n"
                                            f"{format_history(context_turns)}\n\n"
                                            f"The patient just said: '{last_user_message}'.\n"
                                            f"In a warm and efficient way, acknowledge their answer and ask the next question about {area_names[area]}.\n"
                                            f"Output only the next message you would say to the patient."
                                        )
                                        response = chat_service.generate_response(prompt)
                                        history.append({"role": "assistant", "content": response})
                                        setattr(call_session, "conversation_history", json.dumps(history))
                                        db.commit()
                                        return ChatResponse(response=response, context_metadata=prompt_data["context_metadata"])
                            else:
                                # Clinical assessment logic (existing)
                                if user_is_asking_question:
                                    # Answer the question and then ask the next assessment question
                                    prompt = (
                                        f"Conversation so far:\n"
                                        f"{format_history(context_turns)}\n\n"
                                        f"The patient just said: '{last_user_message}'\n"
                                        f"This appears to be both an answer to your previous question AND a new question from the patient.\n"
                                        f"1. First, answer their question in a helpful and informative way\n"
                                        f"2. Then, acknowledge their previous answer\n"
                                        f"3. Finally, ask the next question about {area_names[area]}\n"
                                        f"Output only the response you would say to the patient."
                                    )
                                else:
                                    # Standard assessment question
                                    prompt = (
                                        f"Conversation so far:\n"
                                        f"{format_history(context_turns)}\n\n"
                                        f"The patient just said: '{last_user_message}'.\n"
                                        f"In a warm and efficient way, acknowledge their answer and ask the next question about {area_names[area]}.\n"
                                        f"Output only the next message you would say to the patient."
                                    )
                                
                                response = chat_service.generate_response(prompt)
                                history.append({"role": "assistant", "content": response})
                                setattr(call_session, "conversation_history", json.dumps(history))
                                db.commit()
                                return ChatResponse(response=response, context_metadata=prompt_data["context_metadata"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversational error: {str(e)}")

@router.get("/patients/{patient_id}/calls/next")
async def get_next_scheduled_call(patient_id: str, db: Session = Depends(get_db)):
    """Get the next scheduled call for a patient"""
    try:
        # Get patient
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get next scheduled call
        call_session = db.query(CallSession).filter(
            CallSession.patient_id == patient.id,
            CallSession.call_status == "scheduled"
        ).order_by(CallSession.scheduled_date).first()
        
        if not call_session:
            raise HTTPException(status_code=404, detail="No scheduled calls found")
        
        return {
            "patient_id": patient.id,
            "patient_name": patient.name,
            "call_session_id": call_session.id,
            "call_type": call_session.call_type,
            "days_from_surgery": call_session.days_from_surgery,
            "scheduled_date": call_session.scheduled_date
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting next call: {str(e)}")
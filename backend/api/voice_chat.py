# """
# Voice Chat API for TKA Patients
# Enhanced with call context system for structured conversations
# """

# from fastapi import APIRouter, HTTPException, Depends, Body
# from pydantic import BaseModel
# from typing import Optional
# from datetime import datetime
# import json
# import psycopg2
# from psycopg2.extras import RealDictCursor

# # [SQLAlchemy imports and session usage removed]
# # [Database access code stubbed out]
# from services.voice_chat import get_chat_service
# from services.call_context_service import CallContextService
# from services.context_injection_service import ContextInjectionService
# from utils.conversation_utils import get_covered_areas

# router = APIRouter()

# class ContextualChatMessage(BaseModel):
#     message: str
#     patient_id: str
#     call_session_id: str
#     # Removed conversation_history - now handled automatically by backend

# class ChatResponse(BaseModel):
#     response: str
#     context_metadata: dict

# class StartCallRequest(BaseModel):
#     patient_id: str
#     call_session_id: str

# class StartCallResponse(BaseModel):
#     initial_message: str
#     call_context: dict

# class ConverseRequest(BaseModel):
#     patient_id: str
#     call_session_id: str
#     message: Optional[str] = None

# # Initialize context services
# context_service = CallContextService()
# injection_service = ContextInjectionService()

# @router.post("/contextual-chat", response_model=ChatResponse)
# async def contextual_chat(chat_msg: ContextualChatMessage):
#     """Context-aware chat using call session information with automatic conversation history"""
#     try:
#         # Get patient and call session
#         conn = psycopg2.connect(dbname="tka_voice", user="user", password="password", host="postgres", port=5432)
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         cur.execute("SELECT * FROM patients WHERE id = %s", (chat_msg.patient_id,))
#         patient = cur.fetchone()
#         cur.execute("SELECT * FROM call_sessions WHERE id = %s", (chat_msg.call_session_id,))
#         call_session = cur.fetchone()
#         cur.close()
#         conn.close()
#         if not patient:
#             raise HTTPException(status_code=404, detail="Patient not found")
#         if not call_session:
#             raise HTTPException(status_code=404, detail="Call session not found")
        
#         # Load conversation history from database (or start new)
#         history_str = getattr(call_session, "conversation_history", None)
#         if history_str is not None and history_str != "":
#             history = json.loads(history_str)
#         else:
#             history = []
        
#         # Append the new user message
#         history.append({"role": "user", "content": chat_msg.message})
        
#         # Use the utility function to check which areas are covered
#         call_type = str(call_session["call_type"])
#         covered_data = get_covered_areas(history, call_type)
        
#         # Define area names and order based on call type
#         if call_type == "preparation":
#             area_names = {
#                 "home_safety": "home safety and trip hazard removal",
#                 "equipment_supplies": "equipment and supplies like raised toilet seat and grabber tool",
#                 "medical_preparation": "medical preparation and blood-thinning medications",
#                 "support_verification": "support system verification"
#             }
#             order = ["home_safety", "equipment_supplies", "medical_preparation", "support_verification"]
            
#             # Extract simple boolean coverage for backward compatibility
#             covered = {area: covered_data[area] for area in area_names.keys()}
#         else:
#             area_names = {
#                 "surgery_confirmation": "confirming their upcoming surgery date and how they feel about it",
#                 "pain_level": "their current pain level on a scale of 1 to 10",
#                 "activity_limitations": "any activities that are difficult for them right now because of their knee",
#                 "support_system": "whether they have someone who will be able to help them out after their surgery"
#             }
#             order = ["surgery_confirmation", "pain_level", "activity_limitations", "support_system"]
#             covered = covered_data
        
#         # Helper to detect if user is asking a question
#         def detect_user_question(message):
#             """Detect if the user is asking a question that needs to be answered"""
#             if not message:
#                 return False
#             content = message.lower()
            
#             # Question indicators
#             question_words = ["what", "how", "when", "why", "where", "which", "can you", "could you", "would you"]
#             surgery_keywords = ["surgery", "procedure", "operation", "recovery", "anesthesia", "hospital", "pain", "medication", "rehabilitation", "arthroplasty"]
            
#             # Check for question marks
#             has_question_mark = "?" in message
            
#             # Check for question words
#             has_question_word = any(word in content for word in question_words)
            
#             # Check for surgery-related questions
#             has_surgery_keyword = any(word in content for word in surgery_keywords)
            
#             # If it's a question about surgery/recovery, it should be answered
#             return (has_question_mark or has_question_word) and has_surgery_keyword
        
#         # Generate call context (for context_metadata)
#         call_context = context_service.get_call_context(patient, call_session)
#         prompt_data = injection_service.generate_llm_prompt(call_context, is_initial_call=False)
#         chat_service = get_chat_service()
        
#         # Helper to format last few turns for context
#         def format_history(history):
#             return "\n".join([f"{turn['role'].capitalize()}: {turn['content']}" for turn in history])
        
#         # Prevent repeated wrap-up
#         if getattr(call_session, "call_status", None) == "completed":
#             # Check if user is asking a question even though call is completed
#             user_is_asking_question = detect_user_question(chat_msg.message)
            
#             if user_is_asking_question:
#                 # Answer the question and keep conversation open for follow-ups
#                 context_turns = history[-4:] if len(history) >= 4 else history
#                 prompt = (
#                     f"Conversation so far:\n"
#                     f"{format_history(context_turns)}\n\n"
#                     f"The patient just asked: '{chat_msg.message}'\n"
#                     f"Answer their question in a helpful and informative way, then use the EXACT wrap-up script from your system instructions: 'Great progress. Your next call will be closer to your surgery date to confirm final logistics.'\n"
#                     f"Output only the response you would say to the patient."
#                 )
#                 response = chat_service.generate_response(prompt)
#                 history.append({"role": "assistant", "content": response})
#                 setattr(call_session, "conversation_history", json.dumps(history))
#                 return ChatResponse(response=response, context_metadata=prompt_data["context_metadata"])
#             else:
#                 # Check if user wants to end the conversation
#                 end_keywords = ["goodbye", "bye", "end", "finish", "that's all", "no more questions", "thank you"]
#                 if any(keyword in chat_msg.message.lower() for keyword in end_keywords):
#                     # User wants to end the conversation
#                     goodbye = f"Thank you, {patient['first_name']}. If you have any more questions, feel free to reach out. Goodbye!"
#                     history.append({"role": "assistant", "content": goodbye})
#                     setattr(call_session, "conversation_history", json.dumps(history))
#                     return ChatResponse(response=goodbye, context_metadata={})
#                 else:
#                     # User might be asking a question that wasn't detected, or making a statement
#                     # Let the LLM handle it naturally
#                     context_turns = history[-4:] if len(history) >= 4 else history
#                     prompt = (
#                         f"Conversation so far:\n"
#                         f"{format_history(context_turns)}\n\n"
#                         f"The patient just said: '{chat_msg.message}'\n"
#                         f"Respond naturally and helpfully. If they're asking a question, answer it. If they're making a statement, acknowledge it and ask if they have any questions.\n"
#                         f"Output only the response you would say to the patient."
#                     )
#                     response = chat_service.generate_response(prompt)
#                     history.append({"role": "assistant", "content": response})
#                     setattr(call_session, "conversation_history", json.dumps(history))
#                     return ChatResponse(response=response, context_metadata=prompt_data["context_metadata"])
#         else:
#             # Check if user is asking a question
#             user_is_asking_question = detect_user_question(chat_msg.message)
            
#             if all(covered.values()):
#                 if user_is_asking_question:
#                     # Answer the question and then wrap up
#                     context_turns = history[-4:] if len(history) >= 4 else history
#                     prompt = (
#                         f"Conversation so far:\n"
#                         f"{format_history(context_turns)}\n\n"
#                         f"The patient just asked: '{chat_msg.message}'\n"
#                         f"Answer their question helpfully, then use the wrap-up script from your system instructions.\n"
#                         f"Output only the response you would say to the patient."
#                     )
#                     response = chat_service.generate_response(prompt)
#                     history.append({"role": "assistant", "content": response})
#                     setattr(call_session, "conversation_history", json.dumps(history))
#                     setattr(call_session, "call_status", "completed")
#                     return ChatResponse(response=response, context_metadata=prompt_data["context_metadata"])
#                 else:
#                     # Standard wrap-up - use system prompt wrap-up script
#                     context_turns = history[-4:] if len(history) >= 4 else history
#                     prompt = (
#                         f"Conversation so far:\n"
#                         f"{format_history(context_turns)}\n\n"
#                         f"All areas have been covered. Use the EXACT wrap-up script from your system instructions: 'Great progress. Your next call will be closer to your surgery date to confirm final logistics.'\n"
#                         f"Output only the response you would say to the patient."
#                     )
#                     response = chat_service.generate_response(prompt)
#                     history.append({"role": "assistant", "content": response})
#                     setattr(call_session, "conversation_history", json.dumps(history))
#                     setattr(call_session, "call_status", "completed")
#                     return ChatResponse(response=response, context_metadata=prompt_data["context_metadata"])
#             else:
#                 # Find the next uncovered area
#                 for area in order:
#                     if not covered[area]:
#                         last_user_message = history[-1]["content"] if history and history[-1]["role"] == "user" else ""
#                         context_turns = history[-4:] if len(history) >= 4 else history
                        
#                         # For preparation calls, check if we need more questions in current area
#                         if call_type == "preparation":
#                             questions_asked = covered_data.get(f"{area}_questions_asked", 0)
#                             questions_answered = covered_data.get(f"{area}_questions_answered", 0)
                            
#                             # If this area is already covered, move to the next uncovered area
#                             if covered[area]:
#                                 continue  # Skip to next area
#                             # Otherwise, continue asking questions in this area
#                                 if user_is_asking_question:
#                                     # Answer the question and then ask the next question in current area
#                                     prompt = (
#                                         f"Conversation so far:\n"
#                                         f"{format_history(context_turns)}\n\n"
#                                         f"The patient just said: '{last_user_message}'\n"
#                                         f"This appears to be both an answer to your previous question AND a new question from the patient.\n"
#                                         f"1. First, answer their question in a helpful and informative way\n"
#                                         f"2. Then, acknowledge their previous answer\n"
#                                         f"3. Finally, ask another question about {area_names[area]} (this is question #{questions_asked + 1} for this area)\n"
#                                         f"Output only the response you would say to the patient."
#                                     )
#                                 else:
#                                     # Standard assessment question for current area
#                                     prompt = (
#                                         f"Conversation so far:\n"
#                                         f"{format_history(context_turns)}\n\n"
#                                         f"The patient just said: '{last_user_message}'.\n"
#                                         f"In a warm and efficient way, acknowledge their answer and ask another question about {area_names[area]} (this is question #{questions_asked + 1} for this area).\n"
#                                         f"Output only the next message you would say to the patient."
#                                     )

#                         else:
#                             # Clinical assessment logic (existing)
#                             if user_is_asking_question:
#                                 # Answer the question and then ask the next assessment question
#                                 prompt = (
#                                     f"Conversation so far:\n"
#                                     f"{format_history(context_turns)}\n\n"
#                                     f"The patient just said: '{last_user_message}'\n"
#                                     f"This appears to be both an answer to your previous question AND a new question from the patient.\n"
#                                     f"1. First, answer their question in a helpful and informative way\n"
#                                     f"2. Then, acknowledge their previous answer\n"
#                                     f"3. Finally, ask the next question about {area_names[area]}\n"
#                                     f"Output only the response you would say to the patient."
#                                 )
#                             else:
#                                 # Standard assessment question
#                                 prompt = (
#                                     f"Conversation so far:\n"
#                                     f"{format_history(context_turns)}\n\n"
#                                     f"The patient just said: '{last_user_message}'.\n"
#                                     f"In a warm and efficient way, acknowledge their answer and ask the next question about {area_names[area]}.\n"
#                                     f"Output only the next message you would say to the patient."
#                                 )
                            
#                             question = chat_service.generate_response(prompt)
#                             history.append({"role": "assistant", "content": question})
#                             setattr(call_session, "conversation_history", json.dumps(history))
#                             return ChatResponse(response=question, context_metadata=prompt_data["context_metadata"])
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Contextual chat error: {str(e)}")

# @router.post("/start-call", response_model=StartCallResponse)
# async def start_call(request: StartCallRequest):
#     """Start a structured call with proper context injection"""
#     try:
#         # Get patient and call session
#         conn = psycopg2.connect(dbname="tka_voice", user="user", password="password", host="postgres", port=5432)
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         cur.execute("SELECT * FROM patients WHERE id = %s", (request.patient_id,))
#         patient = cur.fetchone()
#         cur.execute("SELECT * FROM call_sessions WHERE id = %s", (request.call_session_id,))
#         call_session = cur.fetchone()
#         cur.close()
#         conn.close()
#         if not patient:
#             raise HTTPException(status_code=404, detail="Patient not found")
#         if not call_session:
#             raise HTTPException(status_code=404, detail="Call session not found")
        
#         # Generate call context
#         call_context = context_service.get_call_context(patient, call_session)
        
#         # Generate initial prompt (start of conversation)
#         prompt_data = injection_service.generate_llm_prompt(call_context, is_initial_call=True)
        
#         # Get chat service and start conversation
#         chat_service = get_chat_service()
#         # Send both system and user prompts as initial messages
#         messages = [
#             {"role": "system", "content": prompt_data["system_prompt"]},
#             {"role": "user", "content": prompt_data["user_prompt"]}
#         ]
#         responses = chat_service.start_contextual_conversation(messages)
#         initial_response = responses[0] if responses else ""
        
#         # Initialize conversation history with the first assistant message
#         history = [{"role": "assistant", "content": initial_response}]
#         setattr(call_session, "conversation_history", json.dumps(history))
        
#         # Update call session status
#         setattr(call_session, "call_status", "in_progress")
#         setattr(call_session, "actual_call_start", datetime.now())
#         return StartCallResponse(
#             initial_message=initial_response,
#             call_context={
#                 "call_type": call_context.call_type.value,
#                 "days_from_surgery": call_context.days_from_surgery,
#                 "estimated_duration": call_context.estimated_duration_minutes,
#                 "focus_areas": call_context.focus_areas
#             }
#         )
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error starting call: {str(e)}")

# def format_history(history):
#     return "\n".join([f"{turn['role'].capitalize()}: {turn['content']}" for turn in history])

# def add_response(history, prompt, chat_service):
#     response = chat_service.generate_response(prompt)
#     history.append({"role": "assistant", "content": response})
#     return response

# def get_next_area(order, covered):
#     for area in order:
#         if not covered[area]:
#             return area
#     return None

# def update_conversation_history(call_session_id, history):
#     conn = psycopg2.connect(dbname="tka_voice", user="user", password="password", host="postgres", port=5432)
#     cur = conn.cursor()
#     cur.execute(
#         "UPDATE call_sessions SET conversation_history = %s WHERE id = %s",
#         (json.dumps(history), call_session_id)
#     )
#     conn.commit()
#     cur.close()
#     conn.close()

# @router.post("/converse", response_model=ChatResponse)
# async def converse(request: ConverseRequest):
#     """
#     Unified endpoint for starting and continuing a conversation.
#     If no conversation history or message, starts the call.
#     Otherwise, continues the conversation.
#     """
#     try:
#         # Fetch patient and call session
#         conn = psycopg2.connect(dbname="tka_voice", user="user", password="password", host="postgres", port=5432)
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         cur.execute("SELECT * FROM patients WHERE id = %s", (request.patient_id,))
#         patient = cur.fetchone()
#         cur.execute("SELECT * FROM call_sessions WHERE id = %s", (request.call_session_id,))
#         call_session = cur.fetchone()
#         cur.close()
#         conn.close()
#         if not patient:
#             raise HTTPException(status_code=404, detail="Patient not found")
#         if not call_session:
#             raise HTTPException(status_code=404, detail="Call session not found")

#         # Load conversation history
#         history_str = call_session.get("conversation_history")
#         history = json.loads(history_str) if history_str else []

#         # Generate call context and prompt data
#         call_context = context_service.get_call_context(patient, call_session)
#         chat_service = get_chat_service()
#         prompt_data = injection_service.generate_llm_prompt(call_context, is_initial_call=False)

#         call_type = str(call_session["call_type"])
#         covered_data = get_covered_areas(history, call_type)
#         if call_type == "preparation":
#             area_names = {
#                 "home_safety": "home safety and trip hazard removal",
#                 "equipment_supplies": "equipment and supplies like raised toilet seat and grabber tool",
#                 "medical_preparation": "medical preparation and blood-thinning medications",
#                 "support_verification": "support system verification"
#             }
#             order = ["home_safety", "equipment_supplies", "medical_preparation", "support_verification"]
#         else: # Not a 'preparation' call
#             area_names = {
#                 "surgery_date_confirmation": "confirming their upcoming surgery date",
#                 "feelings_assessment": "how they are feeling about the surgery",
#                 "pain_level": "their current pain level on a scale of 1 to 10",
#                 "activity_limitations": "any activities that are difficult for them right now because of their knee",
#                 "support_system": "whether they have someone who will be able to help them out after their surgery"
#             }
#             order = ["surgery_date_confirmation", "feelings_assessment", "pain_level", "activity_limitations", "support_system"]

#         def detect_user_question(message):
#             if not message:
#                 return False
#             content = message.lower()
#             question_words = ["what", "how", "when", "why", "where", "which", "can you", "could you", "would you"]
#             surgery_keywords = ["surgery", "procedure", "operation", "recovery", "anesthesia", "hospital", "pain", "medication", "rehabilitation", "arthroplasty"]
#             has_question_mark = "?" in message
#             has_question_word = any(word in content for word in question_words)
#             has_surgery_keyword = any(word in content for word in surgery_keywords)
#             return (has_question_mark or has_question_word) and has_surgery_keyword

#         # Completed call
#         if call_session.get("call_status") == "completed":
#             user_is_asking_question = detect_user_question(request.message)
#             if user_is_asking_question:
#                 context_turns = history[-4:] if len(history) >= 4 else history
#                 prompt = (
#                     f"Conversation so far:\n"
#                     f"{format_history(context_turns)}\n\n"
#                     f"The patient just asked: '{request.message}'\n"
#                     f"Answer their question in a helpful and informative way. Be thorough and educational.\n"
#                     f"After answering, ask if they have any other questions or if there's anything else they'd like to know.\n"
#                     f"Output only the response you would say to the patient."
#                 )
#                 response = add_response(history, prompt, chat_service)
#                 update_conversation_history(request.call_session_id, history)
#                 return ChatResponse(response=response, context_metadata=prompt_data["context_metadata"])
#             else:
#                 end_keywords = ["goodbye", "bye", "end", "finish", "that's all", "no more questions", "thank you"]
#                 if request.message and any(keyword in request.message.lower() for keyword in end_keywords):
#                     goodbye = f"Thank you, {patient['first_name']}. If you have any more questions, feel free to reach out. Goodbye!"
#                     history.append({"role": "assistant", "content": goodbye})
#                     update_conversation_history(request.call_session_id, history)
#                     return ChatResponse(response=goodbye, context_metadata={})
#                 else:
#                     context_turns = history[-4:] if len(history) >= 4 else history
#                     prompt = (
#                         f"Conversation so far:\n"
#                         f"{format_history(context_turns)}\n\n"
#                         f"The patient just said: '{request.message}'\n"
#                         f"Respond naturally and helpfully. If they're asking a question, answer it. If they're making a statement, acknowledge it and ask if they have any questions.\n"
#                         f"Output only the response you would say to the patient."
#                     )
#                     response = add_response(history, prompt, chat_service)
#                     update_conversation_history(request.call_session_id, history)
#                     return ChatResponse(response=response, context_metadata=prompt_data["context_metadata"])

#         if not history: # This is the very first turn
#             initial_response = f"Hello {patient['first_name']} {patient['last_name']}, this is your healthcare assistant calling about your upcoming knee replacement surgery. Is this a good time to talk?"
#             history = [{"role": "assistant", "content": initial_response}]
#             update_conversation_history(request.call_session_id, history)
#             return ChatResponse(response=initial_response, context_metadata={})

#         if len(history) == 1 and history[0]['role'] == 'assistant': # This is the second turn
#             history.append({"role": "user", "content": request.message})
#             s_date = datetime.fromisoformat(patient['surgery_date']) if isinstance(patient['surgery_date'], str) else patient['surgery_date']
#             surgery_date_str = s_date.strftime('%B %d, %Y')
            
#             date_confirmation_question = f"Great. I have your surgery scheduled for {surgery_date_str}, is that correct?"
            
#             history.append({"role": "assistant", "content": date_confirmation_question})
#             update_conversation_history(request.call_session_id, history)
#             return ChatResponse(response=date_confirmation_question, context_metadata={})

#         # Main flow
#         history.append({"role": "user", "content": request.message})
#         covered = covered_data if call_type != "preparation" else {area: covered_data[area] for area in order}
#         user_is_asking_question = detect_user_question(request.message)
#         if all(covered.values()):
#             if user_is_asking_question:
#                 # Answer the question and then wrap up
#                 context_turns = history[-4:] if len(history) >= 4 else history
#                 prompt = (
#                     f"Conversation so far:\n"
#                     f"{format_history(context_turns)}\n\n"
#                     f"The patient just asked: '{request.message}'\n"
#                     f"Answer their question helpfully, then use the wrap-up script from your system instructions.\n"
#                     f"Output only the response you would say to the patient."
#                 )
#                 response = add_response(history, prompt, chat_service)
#                 update_conversation_history(request.call_session_id, history)
#                 return ChatResponse(response=response, context_metadata=prompt_data["context_metadata"])
#             else:
#                 # Standard wrap-up
#                 context_turns = history[-4:] if len(history) >= 4 else history
#                 prompt = (
#                     f"Conversation so far:\n"
#                     f"{format_history(context_turns)}\n\n"
#                     f"All areas have been covered. Acknowledge the last user message, then use the wrap-up script from your system instructions.\n"
#                     f"Output only the response you would say to the patient."
#                 )
#                 response = add_response(history, prompt, chat_service)
#                 update_conversation_history(request.call_session_id, history)
#                 return ChatResponse(response=response, context_metadata=prompt_data["context_metadata"])
#         else:
#             next_area = get_next_area(order, covered)
#             last_user_message = history[-1]["content"] if history and history[-1]["role"] == "user" else ""
#             context_turns = history[-4:] if len(history) >= 4 else history
#             if user_is_asking_question:
#                 prompt = (
#                     f"Conversation so far:\n"
#                     f"{format_history(context_turns)}\n\n"
#                     f"The patient just said: '{last_user_message}'\n"
#                     f"First, answer their question. Then, ask ONE question about {area_names[next_area]}.\n"
#                     f"Output only the response you would say to the patient."
#                 )
#             else:
#                 prompt = (
#                     f"Conversation so far:\n"
#                     f"{format_history(context_turns)}\n\n"
#                     f"The patient just said: '{last_user_message}'.\n"
#                     f"Acknowledge their answer and ask ONE question about {area_names[next_area]}.\n"
#                     f"Output only the next message you would say to the patient."
#                 )
#             response = add_response(history, prompt, chat_service)
#             update_conversation_history(request.call_session_id, history)
#             return ChatResponse(response=response, context_metadata=prompt_data["context_metadata"])
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Conversational error: {str(e)}")

# @router.get("/patients/{patient_id}/calls/next")
# async def get_next_scheduled_call(patient_id: str):
#     """Get the next scheduled call for a patient"""
#     try:
#         # Get patient
#         conn = psycopg2.connect(dbname="tka_voice", user="user", password="password", host="postgres", port=5432)
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         cur.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
#         patient = cur.fetchone()
#         cur.close()
#         conn.close()
#         if not patient:
#             raise HTTPException(status_code=404, detail="Patient not found")
        
#         # Get next scheduled call
#         conn = psycopg2.connect(dbname="tka_voice", user="user", password="password", host="postgres", port=5432)
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         cur.execute("""
#             SELECT cs.id, cs.patient_id, p.first_name, p.last_name, cs.call_type, cs.days_from_surgery, cs.scheduled_date
#             FROM call_sessions cs
#             JOIN patients p ON cs.patient_id = p.id
#             WHERE cs.patient_id = %s AND cs.call_status = 'scheduled'
#             ORDER BY cs.scheduled_date
#         """, (patient_id,))
#         call_session = cur.fetchone()
#         cur.close()
#         conn.close()
        
#         if not call_session:
#             raise HTTPException(status_code=404, detail="No scheduled calls found")
        
#         return {
#             "patient_id": call_session["patient_id"],
#             "patient_name": f"{call_session['first_name']} {call_session['last_name']}",
#             "call_session_id": call_session["id"],
#             "call_type": call_session["call_type"],
#             "days_from_surgery": call_session["days_from_surgery"],
#             "scheduled_date": call_session["scheduled_date"]
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error getting next call: {str(e)}")



# surgicalcompanian/backend/api/voice_chat.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel # Used for ChatResponse, ConverseRequest
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import os

# Import shared services from the backend/services directory
from backend.services.database_manager import DatabaseManager # Corrected path
from backend.services.orchestrator import ConversationOrchestrator # Corrected path
# from backend.services.llm_client import LLMClient # Not directly used here, Orchestrator uses it
# from backend.services.prompt_generator import PromptGenerator # Not directly used here, Orchestrator uses it

# Import Pydantic models for request/response
from backend.models.chat_models import ConverseRequest, ChatResponse # Assuming you moved these

# Import other helper services/utils if needed by the router directly (optional)
# from backend.services.call_context_service import context_service # If needed directly
# from backend.services.context_injection_service import injection_service # If needed directly
# from backend.utils.conversation_utils import get_covered_areas # If needed directly

router = APIRouter()

# Global instances (these will be initialized in main.py and passed/accessed)
# For now, we'll assume main.py handles these and they are accessible.
# In a real FastAPI app, you might use Depends() or a global/singleton pattern for these.

# To simplify initial integration, we'll create new instances here.
# In production, these should ideally be singletons managed by FastAPI's dependency injection
# or startup events in main.py for efficiency.
db_manager = DatabaseManager()
orchestrator = ConversationOrchestrator()
logger = logging.getLogger(__name__)


@router.post("/converse", response_model=ChatResponse)
async def converse(request: ConverseRequest):
    """
    Unified endpoint for starting and continuing a conversation.
    Handles the core conversational logic and state management.
    """
    try:
        # 1. Fetch Patient and Call Session Data using the shared db_manager
        patient_data = db_manager.get_patient_data(request.patient_id)
        call_session_data = db_manager.get_call_session_data(request.call_session_id)

        if not patient_data:
            raise HTTPException(status_code=404, detail="Patient not found")
        if not call_session_data:
            raise HTTPException(status_code=404, detail="Call session not found")

        # 2. Let the Orchestrator determine the next step and response
        # Orchestrator handles NLU, LLM calls, and state updates based on your design
        agent_response_info = orchestrator.get_next_agent_response(
            patient_data, call_session_data, request.message # request.message is the user's input
        )

        # 3. Update Database with new state using the shared db_manager
        # Note: conversation_history, call_status, actual_call_start, call_duration_seconds
        # are updated by orchestrator logic and returned in agent_response_info
        
        db_manager.update_call_session(
            request.call_session_id,
            {
                "conversation_history": agent_response_info["updated_conversation_history"],
                "call_status": agent_response_info["new_call_status"],
                "actual_call_start": agent_response_info["actual_call_start"],
                "call_duration_seconds": agent_response_info["call_duration_seconds"]
            }
        )
        # 6. Update patient's clinical data record
        # Use the full agent response which includes previous data + new data
        if agent_response_info.get("updated_clinical_data"):
            db_manager.update_patient_report(
            request.patient_id, agent_response_info["updated_clinical_data"]
        )
            logger.info(f"Updated clinical data for patient {request.patient_id}")

        return ChatResponse(
            response=agent_response_info["response_text"],
            state=agent_response_info["current_stage"],
            extracted_report=agent_response_info["updated_clinical_data"],
            context_metadata=agent_response_info["context_metadata"],
            current_call_status=agent_response_info["current_call_status"]
        )

    except HTTPException:
        raise # Re-raise FastAPI HTTP exceptions
    except Exception as e:
        print(f"Error in /chat/converse endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Conversational error: {str(e)}")


@router.get("/patients/{patient_id}/calls/next")
async def get_next_scheduled_call(patient_id: str):
    """Get the next scheduled call for a patient"""
    try:
        patient_data = db_manager.get_patient_data(patient_id)
        if not patient_data:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        conn = None
        try:
            # We need to get DATABASE_URL from os.getenv here, as this is a standalone route
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                raise ValueError("DATABASE_URL environment variable not set for direct connection in get_next_scheduled_call.")
            conn = psycopg2.connect(database_url)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT cs.id, cs.patient_id, p.first_name, p.last_name, cs.call_type, cs.days_from_surgery, cs.scheduled_date
                FROM call_sessions cs
                JOIN patients p ON cs.patient_id = p.id
                WHERE cs.patient_id = %s AND cs.call_status = 'scheduled'
                ORDER BY cs.scheduled_date
                LIMIT 1
            """, (patient_id,))
            call_session = cur.fetchone()
            cur.close()
        except psycopg2.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        finally:
            if conn: conn.close()
        
        if not call_session:
            raise HTTPException(status_code=404, detail="No scheduled calls found")
        
        return {
            "patient_id": call_session["patient_id"],
            "patient_name": f"{call_session['first_name']} {call_session['last_name']}",
            "call_session_id": call_session["id"],
            "call_type": call_session["call_type"],
            "days_from_surgery": call_session["days_from_surgery"],
            "scheduled_date": call_session["scheduled_date"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in /patients/{{patient_id}}/calls/next: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting next call: {str(e)}")

# Add other routers if they exist (e.g., patients_router, clinical_router, webhooks_router)
# but main.py will handle including all of them.
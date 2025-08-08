# orchestrator.py
from .llm_client import LLMClient # Assuming llm_client.py
from .prompt_generator import PromptGenerator # Assuming prompt_generator.py
import json
import datetime
import os 
import re # For basic parsing of NLU JSON output

class ConversationOrchestrator:
    def __init__(self):
        print("ORCHESTRATOR_INIT: Initializing ConversationOrchestrator instance.")
        # Initialize LLM Client (API Key from environment)
        self.llm_client = LLMClient(os.getenv("GEMINI_API_KEY"))
        self.prompt_generator = PromptGenerator()
        print("ORCHESTRATOR_INIT: ConversationOrchestrator instance fully initialized.")
        
        # Define call stages and what's expected for completion for Call 1
        # In a real system, these would be loaded from a config/DB
        self.CALL_1_STAGES = {
            "START": "Greeting",
            "Greeting": "ConfirmSurgeryDate",
            "ConfirmSurgeryDate": "PainAssessment",
            "PainAssessment": "MobilityAssessment",
            "MobilityAssessment": "SupportSystemAssessment",
            "SupportSystemAssessment": "Closing",
            "Closing": "COMPLETED"
        }
        
        # Define expected data points for each assessment area (for tracking completion)
        self.ASSESSMENT_AREA_DATA_POINTS = {
            # Initial Clinical Assessment Call (call_type="initial_assessment")
            "PainAssessment": ["pain_level"],
            "MobilityAssessment": ["difficult_activities_pain"],
            "SupportSystemAssessment": ["primary_helper_identified"],
            
            # Preparation Call (call_type="preparation") - Updated structure
            "HomeSafetyAssessment": ["recovery_space_prepared", "trip_hazards_removed"],
            "MedicalEquipmentAssessment": ["assistive_tools_list"],
            "MedicationReview": ["blood_thinning_medications", "medical_conditions_list", "allergies_list"]
        }


    def _get_current_call_stage(self, conversation_history: list, report: dict, call_type: str) -> str:
        """Determines the current stage of the pre-operative call based on conversation and data."""
        
        # Greet the user on the first turn
        if not conversation_history:
            return "Greeting"
        
        if call_type == "preparation":
            # Preparation call flow
            prep_data = report.get("preparation_call", {})
            if not prep_data.get("ready_confirmed"):
                return "InitialConfirmation"
            if not self._is_area_complete_by_call_type(report, "HomeSafetyAssessment", call_type):
                return "HomeSafetyAssessment"
            if not self._is_area_complete_by_call_type(report, "MedicalEquipmentAssessment", call_type):
                return "MedicalEquipmentAssessment"
            if not self._is_area_complete_by_call_type(report, "MedicationReview", call_type):
                return "MedicationReview"
            return "Closing"
        else:
            # Initial clinical assessment call flow (default)
            initial_data = report.get("initial_assessment_call", {})
            if not initial_data.get("ready_confirmed"):
                return "InitialConfirmation"
            if not initial_data.get("surgery_date_confirmed"):
                return "SurgeryDateConfirmation"
            if not self._is_area_complete_by_call_type(report, "PainAssessment", call_type):
                return "PainAssessment"
            if not self._is_area_complete_by_call_type(report, "MobilityAssessment", call_type):
                return "MobilityAssessment"
            if not self._is_area_complete_by_call_type(report, "SupportSystemAssessment", call_type):
                return "SupportSystemAssessment"
            return "Closing"
        
    def _is_area_complete(self, report: dict, area_name: str) -> bool:
        """Checks if all required data points for an assessment area are in report."""
        required_data_points = self.ASSESSMENT_AREA_DATA_POINTS.get(area_name, [])
        for dp in required_data_points:
            if dp not in report or report.get(dp) is None or report.get(dp) == '':
                return False
        return True
    
    def _is_area_complete_by_call_type(self, report: dict, area_name: str, call_type: str) -> bool:
        """Checks if all required data points for an assessment area are complete for the specific call type."""
        required_data_points = self.ASSESSMENT_AREA_DATA_POINTS.get(area_name, [])
        
        if call_type == "preparation":
            call_data = report.get("preparation_call", {})
        else:
            call_data = report.get("initial_assessment_call", {})
        
        # Special handling for MedicationReview to ensure all three areas are addressed
        if area_name == "MedicationReview" and call_type == "preparation":
            blood_thinners = call_data.get("blood_thinning_medications", [])
            allergies = call_data.get("allergies_list", [])
            medical_conditions = call_data.get("medical_conditions_list", [])
            
            # All three areas must have been addressed (either with content or explicitly marked as "none")
            if not blood_thinners and not allergies and not medical_conditions:
                return False
            elif blood_thinners and not allergies and not medical_conditions:
                return False
            elif blood_thinners and allergies and not medical_conditions:
                return False
            else:
                return True
        
        # Standard logic for other areas
        for dp in required_data_points:
            if dp not in call_data:
                return False
            elif call_data.get(dp) is None or call_data.get(dp) == '':
                return False
            elif isinstance(call_data.get(dp), list) and len(call_data.get(dp)) == 0:
                return False
        return True
    
    
    def _parse_llm_json_output(self, llm_response_text: str) -> dict:
        """Robustly parses JSON output from LLM, handling common LLM formatting issues."""
        # Clean up common markdown formatting from the start and end of the string
        cleaned_text = llm_response_text.strip()
        
        # Remove markdown code blocks
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        elif cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
        
        # Remove any leading/trailing text that might not be JSON
        cleaned_text = cleaned_text.strip()
        
        # Remove common prefixes/suffixes that LLMs might add
        prefixes_to_remove = ["Response:", "JSON:", "Result:", "Output:"]
        for prefix in prefixes_to_remove:
            if cleaned_text.startswith(prefix):
                cleaned_text = cleaned_text[len(prefix):].strip()

        try:
            # Try direct parse
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            # Sometimes LLMs add text before/after JSON, or extra chars
            print(f"LLM did not output clean JSON: '{cleaned_text}'")
            
            # Try to find JSON block using more robust regex
            json_patterns = [
                r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Simple nested JSON
                r'\{.*?\}',  # Greedy match
                r'\{[\s\S]*\}'  # Any characters including newlines
            ]
            
            for pattern in json_patterns:
                json_match = re.search(pattern, cleaned_text)
                if json_match:
                    try:
                        result = json.loads(json_match.group(0))
                        print(f"Successfully parsed JSON with pattern: {pattern}")
                        return result
                    except json.JSONDecodeError:
                        continue
            
            print(f"All JSON parsing attempts failed for: '{llm_response_text}'")
            return {"intent": "unknown", "entities": {}, "parse_error": "json_decode_failed"}
    
    def _fallback_nlu(self, user_message: str, report: dict, call_type: str = "initial_assessment") -> dict:
        """Simple rule-based NLU fallback when LLM parsing fails."""
        message_lower = user_message.lower()
        
        # Check for confirmation words with context
        if any(word in message_lower for word in ["yes", "yeah", "sure", "ok", "okay", "correct", "right"]):
            # If they mention removal/hazards, it's specifically about trip hazards
            if any(word in message_lower for word in ["removed", "remove", "cleared", "clear", "them", "rug", "hazard"]):
                return {"intent": "home_safety_response", "entities": {"trip_hazards": "removed"}}
            else:
                return {"intent": "confirm_yes", "entities": {"confirmation": "yes"}}
        if any(word in message_lower for word in ["no", "nope", "wrong", "incorrect"]):
            return {"intent": "confirm_no", "entities": {"confirmation": "no"}}
        
        # Check for pain level (numbers)
        pain_numbers = re.findall(r'\b([0-9]|10)\b', user_message)
        if pain_numbers and not report.get("pain_level"):
            return {"intent": "report_pain", "entities": {"pain_level": int(pain_numbers[0])}}
        
        # Check for activity words
        activity_words = ["standing", "walking", "sitting", "climbing", "stairs", "bending", "kneeling", "getting up", "lying down"]
        found_activities = [word for word in activity_words if word in message_lower]
        if found_activities and not report.get("difficult_activities_pain"):
            return {"intent": "difficult_activities", "entities": {"activities": ", ".join(found_activities)}}
        
        # Check for helper words
        helper_words = ["wife", "husband", "daughter", "son", "friend", "mother", "father", "sister", "brother", "family"]
        found_helpers = [word for word in helper_words if word in message_lower]
        if found_helpers and not report.get("primary_helper_identified"):
            # Join multiple helpers with "and"
            helper_text = " and ".join(found_helpers) if len(found_helpers) > 1 else found_helpers[0]
            return {"intent": "identify_helper", "entities": {"helper": helper_text}}
        
        # Check for home safety words
        safety_words = ["rug", "carpet", "hazard", "trip", "remove", "clean", "space", "bedroom", "recovery"]
        if any(word in message_lower for word in safety_words):
            entities = {}
            # Check for recovery space setup
            if any(word in message_lower for word in ["bedroom", "space", "downstairs", "bed", "room"]):
                if any(word in message_lower for word in ["set up", "ready", "prepared", "yes", "have"]):
                    entities["recovery_space"] = "prepared"
                else:
                    entities["recovery_space"] = "discussed"
            # Check for trip hazard removal
            if any(word in message_lower for word in ["rug", "hazard", "trip", "remove", "clean"]):
                if any(word in message_lower for word in ["removed", "cleared", "clean", "yes", "done"]):
                    entities["trip_hazards"] = "removed"
                else:
                    entities["trip_hazards"] = "discussed"
            if entities:
                return {"intent": "home_safety_response", "entities": entities}
        
        # Check for equipment words
        equipment_words = ["toilet seat", "grabber", "tool", "reacher", "equipment", "walker", "shower chair"]
        if any(word in message_lower for word in equipment_words):
            entities = {}
            if "toilet seat" in message_lower:
                if any(word in message_lower for word in ["have", "got", "installed", "ready"]):
                    entities["toilet_seat"] = "obtained"
                elif any(word in message_lower for word in ["no", "not", "need", "arrange", "get", "don't have"]):
                    entities["toilet_seat"] = "needed"
            if any(word in message_lower for word in ["grabber", "tool", "reacher"]):
                if any(word in message_lower for word in ["have", "got", "ready"]):
                    entities["grabber_tool"] = "obtained"
                elif any(word in message_lower for word in ["no", "not", "need", "arrange", "get", "don't have"]):
                    entities["grabber_tool"] = "needed"
            if "walker" in message_lower:
                if any(word in message_lower for word in ["have", "got", "ready"]):
                    entities["walker"] = "obtained"
                elif any(word in message_lower for word in ["no", "not", "need", "arrange", "get", "don't have"]):
                    entities["walker"] = "needed"
            if "shower chair" in message_lower or "shower chair" in message_lower:
                if any(word in message_lower for word in ["have", "got", "ready"]):
                    entities["shower_chair"] = "obtained"
                elif any(word in message_lower for word in ["no", "not", "need", "arrange", "get", "don't have"]):
                    entities["shower_chair"] = "needed"
            if entities:
                return {"intent": "equipment_response", "entities": entities}
        
        # Check for contextual "yes" responses in equipment stage
        prep_data = report.get("preparation_call", {})
        if any(word in message_lower for word in ["yes", "have", "got"]) and call_type == "preparation":
            # If we're in equipment stage and they say "yes", try to determine what they're confirming
            if not prep_data.get("raised_toilet_seat_obtained"):
                # Asking about toilet seat, they said yes
                return {"intent": "equipment_response", "entities": {"toilet_seat": "obtained"}}
            elif not prep_data.get("grabber_tool_obtained"):
                # Asking about grabber tool, they said yes  
                return {"intent": "equipment_response", "entities": {"grabber_tool": "obtained"}}
        
        # Check for explicit "no" responses about equipment when in equipment stage
        if any(word in message_lower for word in ["no", "not yet", "don't have", "need to arrange"]):
            if not report.get("preparation_call", {}).get("raised_toilet_seat_obtained"):
                return {"intent": "equipment_response", "entities": {"toilet_seat": "needed"}}
        
        # Check for medication words
        medication_words = ["aspirin", "warfarin", "eliquis", "blood thinner", "medication", "medicine", "allergy", "allergic", "condition", "diabetes", "heart", "blood pressure"]
        if any(word in message_lower for word in medication_words):
            entities = {}
            if any(word in message_lower for word in ["aspirin", "warfarin", "eliquis", "blood thinner"]):
                if "aspirin" in message_lower:
                    entities["blood_thinners"] = "aspirin"
                elif "warfarin" in message_lower:
                    entities["blood_thinners"] = "warfarin"
                elif "eliquis" in message_lower:
                    entities["blood_thinners"] = "eliquis"
                else:
                    entities["blood_thinners"] = "none"
            elif any(word in message_lower for word in ["allergy", "allergic"]):
                # Extract allergy information
                if "penicillin" in message_lower:
                    entities["allergies"] = "penicillin"
                elif "latex" in message_lower:
                    entities["allergies"] = "latex"
                else:
                    entities["allergies"] = "none"
            elif any(word in message_lower for word in ["diabetes", "heart", "blood pressure", "condition"]):
                # Extract medical conditions
                if "diabetes" in message_lower:
                    entities["medical_conditions"] = "diabetes"
                elif "heart" in message_lower:
                    entities["medical_conditions"] = "heart condition"
                elif "blood pressure" in message_lower:
                    entities["medical_conditions"] = "high blood pressure"
                else:
                    entities["medical_conditions"] = "none"
            if entities:
                return {"intent": "medication_response", "entities": entities}
        
        # Check for negative responses about medications/allergies/conditions
        if any(word in message_lower for word in ["no", "none", "nothing", "not", "don't", "don't have", "don't take"]):
            # Check if we're in medication review stage by looking at current data
            prep_data = report.get("preparation_call", {})
            blood_thinners = prep_data.get("blood_thinning_medications", [])
            allergies = prep_data.get("allergies_list", [])
            medical_conditions = prep_data.get("medical_conditions_list", [])
            
            if blood_thinners and not allergies:
                # User is responding to allergies question
                return {"intent": "medication_response", "entities": {"allergies": "none"}}
            elif blood_thinners and allergies and not medical_conditions:
                # User is responding to medical conditions question
                return {"intent": "medication_response", "entities": {"medical_conditions": "none"}}
            elif not blood_thinners:
                # User is responding to blood thinners question
                return {"intent": "medication_response", "entities": {"blood_thinners": "none"}}
        
        return {"intent": "unknown", "entities": {}}

    # ... (rest of class) ...



    def get_next_agent_response(self, patient_data: dict, call_session_data: dict, user_message: str = None) -> dict:
        """
        Determines the agent's next response based on conversation state.
        """
        # Get call type first - needed for stage determination
        call_type = call_session_data.get("call_type", "initial_assessment")
        
        # Initialize/Load State
        conversation_history = call_session_data.get("conversation_history", [])
        print(f"Conversation history loaded: {conversation_history}")
        if not isinstance(conversation_history, list):
            conversation_history = []
        extracted_report = dict(patient_data.get("report", {}))
        
        # For the very first turn:
        if not conversation_history and not user_message: # First turn of a brand new call
            current_call_status = "in_progress"
            actual_call_start = datetime.datetime.now()
        else:
            current_call_status = call_session_data.get("call_status", "in_progress")
            actual_call_start = call_session_data.get("actual_call_start")

        agent_response_text = ""
        new_call_status = current_call_status
        call_duration_seconds = None # Update only at the end of call

        # --- Process User Input (if provided) ---
        nlu_result = {"intent": "unknown", "entities": {}}
        if user_message:
            # 1. Append user message to history (for NLU context)
            conversation_history.append({"role": "user", "content": user_message})

            # 2. Perform NLU (Intent & Entity Extraction) using LLM
            nlu_prompt_messages = self.prompt_generator.generate_nlu_prompt(
                conversation_history=conversation_history,
                user_message=user_message,
                report=extracted_report
            )
            nlu_raw_response = self.llm_client.generate_response(nlu_prompt_messages, max_output_tokens=200) # NLU response should be short JSON
            
            # Parse NLU result
            try:
                nlu_result = self._parse_llm_json_output(nlu_raw_response)
            except Exception as e:
                # If parsing fails, use fallback NLU
                nlu_result = self._fallback_nlu(user_message, extracted_report, call_type)
            
            # Ensure nlu_result is a dictionary
            if not isinstance(nlu_result, dict):
                nlu_result = self._fallback_nlu(user_message, extracted_report, call_type)

            # 3. Update report based on NLU result
            intent = nlu_result.get("intent", "unknown")
            entities = nlu_result.get("entities", {})

            # Determine stage before this turn to provide context for NLU interpretation
            stage_before_user_message = self._get_current_call_stage(conversation_history[:-1], extracted_report, call_type)

            # Interpret confirmation based on the stage (handles both intent and entity)
            is_confirmed = None
            if "confirmation" in entities:
                is_confirmed = entities["confirmation"].lower() == "yes"
            elif intent == "confirm_yes":
                is_confirmed = True
            elif intent == "confirm_no":
                is_confirmed = False
            elif intent == "ready_to_begin":
                is_confirmed = True  # "ready to begin" means they're confirming they're ready

            if is_confirmed is not None:
                if stage_before_user_message == "InitialConfirmation":
                    if call_type == "preparation":
                        # Store preparation call data separately
                        if "preparation_call" not in extracted_report:
                            extracted_report["preparation_call"] = {}
                        extracted_report["preparation_call"]["ready_confirmed"] = is_confirmed
                    else:
                        # Store initial assessment call data separately
                        if "initial_assessment_call" not in extracted_report:
                            extracted_report["initial_assessment_call"] = {}
                        extracted_report["initial_assessment_call"]["ready_confirmed"] = is_confirmed
                elif stage_before_user_message == "SurgeryDateConfirmation":
                    if "initial_assessment_call" not in extracted_report:
                        extracted_report["initial_assessment_call"] = {}
                    extracted_report["initial_assessment_call"]["surgery_date_confirmed"] = is_confirmed

            # Handle other intents
            if intent == "report_pain" and "pain_level" in entities:
                try:
                    pain_level = int(entities["pain_level"])
                    if "initial_assessment_call" not in extracted_report:
                        extracted_report["initial_assessment_call"] = {}
                    extracted_report["initial_assessment_call"]["pain_level"] = pain_level
                    if pain_level >= 7: # Example: high pain is a critical alert
                        extracted_report["initial_assessment_call"]["high_pain_alert"] = True
                except ValueError:
                    pass # Handle non-numeric pain
            elif intent == "difficult_activities":
                if "initial_assessment_call" not in extracted_report:
                    extracted_report["initial_assessment_call"] = {}
                if "activity" in entities:
                    extracted_report["initial_assessment_call"]["difficult_activities_pain"] = entities["activity"]
                elif "activities" in entities:
                    # Handle multiple activities (can be string or list)
                    activities = entities["activities"]
                    if isinstance(activities, list):
                        extracted_report["initial_assessment_call"]["difficult_activities_pain"] = ", ".join(activities)
                    else:
                        extracted_report["initial_assessment_call"]["difficult_activities_pain"] = str(activities)
            elif intent == "identify_helper":
                if "initial_assessment_call" not in extracted_report:
                    extracted_report["initial_assessment_call"] = {}
                if "helper_relationship" in entities:
                    extracted_report["initial_assessment_call"]["primary_helper_identified"] = entities["helper_relationship"]
                elif "helper" in entities:
                    extracted_report["initial_assessment_call"]["primary_helper_identified"] = entities["helper"]
            
            # Handle preparation call specific intents
            elif intent == "home_safety_response":
                if "preparation_call" not in extracted_report:
                    extracted_report["preparation_call"] = {}
                if "recovery_space" in entities:
                    extracted_report["preparation_call"]["recovery_space_prepared"] = True if entities["recovery_space"] == "prepared" else False
                if "trip_hazards" in entities:
                    extracted_report["preparation_call"]["trip_hazards_removed"] = True if entities["trip_hazards"] == "removed" else False
            elif intent == "equipment_response":
                if "preparation_call" not in extracted_report:
                    extracted_report["preparation_call"] = {}
                if "assistive_tools_list" not in extracted_report["preparation_call"]:
                    extracted_report["preparation_call"]["assistive_tools_list"] = []
                
                # Add tools to the list
                if "toilet_seat" in entities and entities["toilet_seat"] == "obtained":
                    if "raised toilet seat" not in extracted_report["preparation_call"]["assistive_tools_list"]:
                        extracted_report["preparation_call"]["assistive_tools_list"].append("raised toilet seat")
                if "grabber_tool" in entities and entities["grabber_tool"] == "obtained":
                    if "grabber tool" not in extracted_report["preparation_call"]["assistive_tools_list"]:
                        extracted_report["preparation_call"]["assistive_tools_list"].append("grabber tool")
                if "walker" in entities and entities.get("walker") == "obtained":
                    if "walker" not in extracted_report["preparation_call"]["assistive_tools_list"]:
                        extracted_report["preparation_call"]["assistive_tools_list"].append("walker")
                if "shower_chair" in entities and entities.get("shower_chair") == "obtained":
                    if "shower chair" not in extracted_report["preparation_call"]["assistive_tools_list"]:
                        extracted_report["preparation_call"]["assistive_tools_list"].append("shower chair")
                
                # If both essential tools are mentioned, mark as complete
                tools_list = extracted_report["preparation_call"]["assistive_tools_list"]
                if ("raised toilet seat" in tools_list or "toilet seat" in tools_list) and ("grabber tool" in tools_list or "grabber" in tools_list):
                    pass # No print here, as per instructions
            
            elif intent == "medication_response":
                if "preparation_call" not in extracted_report:
                    extracted_report["preparation_call"] = {}
                if "blood_thinning_medications" not in extracted_report["preparation_call"]:
                    extracted_report["preparation_call"]["blood_thinning_medications"] = []
                if "medical_conditions_list" not in extracted_report["preparation_call"]:
                    extracted_report["preparation_call"]["medical_conditions_list"] = []
                if "allergies_list" not in extracted_report["preparation_call"]:
                    extracted_report["preparation_call"]["allergies_list"] = []
                
                if "blood_thinners" in entities:
                    if isinstance(entities["blood_thinners"], list):
                        extracted_report["preparation_call"]["blood_thinning_medications"] = entities["blood_thinners"]
                    else:
                        extracted_report["preparation_call"]["blood_thinning_medications"] = [entities["blood_thinners"]]
                elif "medical_conditions" in entities:
                    if isinstance(entities["medical_conditions"], list):
                        extracted_report["preparation_call"]["medical_conditions_list"] = entities["medical_conditions"]
                    else:
                        extracted_report["preparation_call"]["medical_conditions_list"] = [entities["medical_conditions"]]
                elif "allergies" in entities:
                    if isinstance(entities["allergies"], list):
                        extracted_report["preparation_call"]["allergies_list"] = entities["allergies"]
                    else:
                        extracted_report["preparation_call"]["allergies_list"] = [entities["allergies"]]
                else:
                    # If no specific medications mentioned, mark as empty list
                    extracted_report["preparation_call"]["blood_thinning_medications"] = []
            
            # Handle confirmations in home safety stage
            elif intent == "confirm_yes" and stage_before_user_message == "HomeSafetyAssessment":
                if "preparation_call" not in extracted_report:
                    extracted_report["preparation_call"] = {}
                
                # Check what's missing and fill in the next item
                prep_data = extracted_report["preparation_call"]
                if "recovery_space_prepared" not in prep_data:
                    extracted_report["preparation_call"]["recovery_space_prepared"] = True
                elif "trip_hazards_removed" not in prep_data:
                    extracted_report["preparation_call"]["trip_hazards_removed"] = True
            
            # Handle equipment confirmations when user says "yes" to equipment questions
            elif intent == "confirm_yes" and stage_before_user_message == "MedicalEquipmentAssessment":
                if "preparation_call" not in extracted_report:
                    extracted_report["preparation_call"] = {}
                if "assistive_tools_list" not in extracted_report["preparation_call"]:
                    extracted_report["preparation_call"]["assistive_tools_list"] = []
                
                # Add both essential tools when user confirms
                if "raised toilet seat" not in extracted_report["preparation_call"]["assistive_tools_list"]:
                    extracted_report["preparation_call"]["assistive_tools_list"].append("raised toilet seat")
                if "grabber tool" not in extracted_report["preparation_call"]["assistive_tools_list"]:
                    extracted_report["preparation_call"]["assistive_tools_list"].append("grabber tool")
            
            # Handle medication confirmations when user says "yes" to medication questions
            elif intent == "confirm_yes" and stage_before_user_message == "MedicationReview":
                if "preparation_call" not in extracted_report:
                    extracted_report["preparation_call"] = {}
                if "blood_thinning_medications" not in extracted_report["preparation_call"]:
                    extracted_report["preparation_call"]["blood_thinning_medications"] = []
                if "medical_conditions_list" not in extracted_report["preparation_call"]:
                    extracted_report["preparation_call"]["medical_conditions_list"] = []
                if "allergies_list" not in extracted_report["preparation_call"]:
                    extracted_report["preparation_call"]["allergies_list"] = []
                
                # Check what's missing and fill in the next item
                prep_data = extracted_report["preparation_call"]
                
                if not prep_data.get("blood_thinning_medications"):
                    extracted_report["preparation_call"]["blood_thinning_medications"] = ["none"]
                elif not prep_data.get("allergies_list"):
                    extracted_report["preparation_call"]["allergies_list"] = ["none"]
                elif not prep_data.get("medical_conditions_list"):
                    extracted_report["preparation_call"]["medical_conditions_list"] = ["none"]
            
            # Handle medication confirmations when user says "no" to medication questions
            elif intent == "confirm_no" and stage_before_user_message == "MedicationReview":
                if "preparation_call" not in extracted_report:
                    extracted_report["preparation_call"] = {}
                if "blood_thinning_medications" not in extracted_report["preparation_call"]:
                    extracted_report["preparation_call"]["blood_thinning_medications"] = []
                if "medical_conditions_list" not in extracted_report["preparation_call"]:
                    extracted_report["preparation_call"]["medical_conditions_list"] = []
                if "allergies_list" not in extracted_report["preparation_call"]:
                    extracted_report["preparation_call"]["allergies_list"] = []
                
                # Check what's missing and fill in the next item
                prep_data = extracted_report["preparation_call"]
                
                if not prep_data.get("blood_thinning_medications"):
                    extracted_report["preparation_call"]["blood_thinning_medications"] = ["none"]
                elif not prep_data.get("allergies_list"):
                    extracted_report["preparation_call"]["allergies_list"] = ["none"]
                elif not prep_data.get("medical_conditions_list"):
                    extracted_report["preparation_call"]["medical_conditions_list"] = ["none"]

        # --- Determine Current Call Stage & Generate Agent Response ---
        current_stage = self._get_current_call_stage(conversation_history, extracted_report, call_type)
        
        if call_type == "preparation":
            return self._handle_preparation_call_logic(
                current_stage, conversation_history, extracted_report, patient_data,
                actual_call_start, new_call_status, call_duration_seconds, nlu_result
            )
        else:
            return self._handle_initial_assessment_call_logic(
                current_stage, conversation_history, extracted_report, patient_data,
                actual_call_start, new_call_status, call_duration_seconds, nlu_result
            )

    def _handle_initial_assessment_call_logic(self, current_stage, conversation_history, extracted_report, 
                                           patient_data, actual_call_start, new_call_status, call_duration_seconds, nlu_result):
        """Handle all logic specific to initial clinical assessment calls"""
        
        if current_stage == "Greeting":
            agent_response_prompt_messages = self.prompt_generator.generate_agent_response_prompt(
                conversation_history=conversation_history,
                current_stage="Greeting",
                patient_name=patient_data["first_name"], # Assuming 'name' field in patient_data
                surgery_date=patient_data.get("surgery_date").strftime("%B %d, %Y") if patient_data.get("surgery_date") else "your scheduled date",
                report=extracted_report
            )
            agent_response_text = self.llm_client.generate_response(agent_response_prompt_messages, max_output_tokens=120) # Allow for empathetic greeting
            new_call_status = "in_progress" # Ensure status is set
            

        
        
        elif current_stage == "InitialConfirmation":
            # Logic handled by NLU result and _get_current_call_stage
            if extracted_report.get("initial_assessment_call", {}).get("ready_confirmed") is True:
                # Transition to ConfirmSurgeryDate
                agent_response_prompt_messages = self.prompt_generator.generate_agent_response_prompt(
                    conversation_history=conversation_history,
                    current_stage="SurgeryDateConfirmation",
                    patient_name=patient_data["first_name"],
                    surgery_date=patient_data.get("surgery_date").strftime("%B %d, %Y") if patient_data.get("surgery_date") else "your scheduled date",
                    report=extracted_report
                )
                agent_response_text = self.llm_client.generate_response(agent_response_prompt_messages, max_output_tokens=120)
                current_stage = "SurgeryDateConfirmation" # Update stage immediately for the next loop/logic if this were a single pass
            elif extracted_report.get("initial_assessment_call", {}).get("ready_confirmed") is False:
                agent_response_text = "I understand. Please contact the clinic to update this call timing."
                new_call_status = "reschedule_required"
            else: # If NLU couldn't confirm, or first pass
                 agent_response_prompt_messages = self.prompt_generator.generate_agent_response_prompt(
                    conversation_history=conversation_history,
                    current_stage="Greeting", # Stay in greeting context if not understood
                    patient_name=patient_data["first_name"],
                    surgery_date=patient_data.get("surgery_date").strftime("%B %d, %Y") if patient_data.get("surgery_date") else "your scheduled date",
                    report=extracted_report
                )
                 agent_response_text = self.llm_client.generate_response(agent_response_prompt_messages, max_output_tokens=120)
        
        elif current_stage == "SurgeryDateConfirmation":
            if extracted_report.get("call1_surgery_date_confirmed") is True:
                # Transition to Pain Assessment
                agent_response_prompt_messages = self.prompt_generator.generate_agent_response_prompt(
                    conversation_history=conversation_history,
                    current_stage="PainAssessment", # Transition to first assessment area
                    patient_name=patient_data["first_name"],
                    surgery_date=patient_data.get("surgery_date").strftime("%B %d, %Y") if patient_data.get("surgery_date") else "your scheduled date",
                    report=extracted_report
                )
                agent_response_text = self.llm_client.generate_response(agent_response_prompt_messages, max_output_tokens=120)
                current_stage = "PainAssessment"
            elif extracted_report.get("call1_surgery_date_confirmed") is False:
                agent_response_text = "I understand. Please contact the clinic to reschedule your surgery date or confirm it with your clinical provider."
                new_call_status = "provider_contact_required"
            else: # If NLU couldn't confirm, or first pass
                agent_response_prompt_messages = self.prompt_generator.generate_agent_response_prompt(
                    conversation_history=conversation_history,
                    current_stage="SurgeryDateConfirmation", # Stay in confirmation context if not understood
                    patient_name=patient_data["first_name"],
                    surgery_date=patient_data.get("surgery_date").strftime("%B %d, %Y") if patient_data.get("surgery_date") else "your scheduled date",
                    report=extracted_report
                )
                agent_response_text = self.llm_client.generate_response(agent_response_prompt_messages, max_output_tokens=120)

        elif current_stage == "PainAssessment":
            # Check if PainAssessment is complete
            if self._is_area_complete(extracted_report, "PainAssessment"):
                agent_response_prompt_messages = self.prompt_generator.generate_agent_response_prompt(
                    conversation_history=conversation_history,
                    current_stage="MobilityAssessment", # Transition to next area
                    patient_name=patient_data["first_name"],
                    surgery_date=patient_data.get("surgery_date").strftime("%B %d, %Y") if patient_data.get("surgery_date") else "your scheduled date",
                    report=extracted_report
                )
                agent_response_text = self.llm_client.generate_response(agent_response_prompt_messages, max_output_tokens=120)
                current_stage = "MobilityAssessment"
            else:
                # Generate next question for PainAssessment using LLM
                agent_response_prompt_messages = self.prompt_generator.generate_agent_response_prompt(
                    conversation_history=conversation_history,
                    current_stage="PainAssessment", # Stay in current area
                    patient_name=patient_data["first_name"],
                    surgery_date=patient_data.get("surgery_date").strftime("%B %d, %Y") if patient_data.get("surgery_date") else "your scheduled date",
                    report=extracted_report
                )
                agent_response_text = self.llm_client.generate_response(agent_response_prompt_messages, max_output_tokens=120)

        elif current_stage == "MobilityAssessment":
            if self._is_area_complete(extracted_report, "MobilityAssessment"):
                agent_response_prompt_messages = self.prompt_generator.generate_agent_response_prompt(
                    conversation_history=conversation_history,
                    current_stage="SupportSystemAssessment", # Transition to next area
                    patient_name=patient_data["first_name"],
                    surgery_date=patient_data.get("surgery_date").strftime("%B %d, %Y") if patient_data.get("surgery_date") else "your scheduled date",
                    report=extracted_report
                )
                agent_response_text = self.llm_client.generate_response(agent_response_prompt_messages, max_output_tokens=120)
                current_stage = "SupportSystemAssessment"
            else:
                # Generate next question for MobilityAssessment using LLM
                agent_response_prompt_messages = self.prompt_generator.generate_agent_response_prompt(
                    conversation_history=conversation_history,
                    current_stage="MobilityAssessment", # Stay in current area
                    patient_name=patient_data["first_name"],
                    surgery_date=patient_data.get("surgery_date").strftime("%B %d, %Y") if patient_data.get("surgery_date") else "your scheduled date",
                    report=extracted_report
                )
                agent_response_text = self.llm_client.generate_response(agent_response_prompt_messages, max_output_tokens=120)

        elif current_stage == "SupportSystemAssessment":
            if self._is_area_complete(extracted_report, "SupportSystemAssessment"):
                agent_response_prompt_messages = self.prompt_generator.generate_agent_response_prompt(
                    conversation_history=conversation_history,
                    current_stage="Closing", # Transition to closing
                    patient_name=patient_data["first_name"],
                    surgery_date=patient_data.get("surgery_date").strftime("%B %d, %Y") if patient_data.get("surgery_date") else "your scheduled date",
                    report=extracted_report
                )
                agent_response_text = self.llm_client.generate_response(agent_response_prompt_messages, max_output_tokens=120)
                new_call_status = "completed" # Mark call as completed
                call_duration_seconds = (datetime.datetime.now() - actual_call_start).total_seconds()
                current_stage = "Closing"
            else:
                # Generate next question for SupportSystemAssessment using LLM
                agent_response_prompt_messages = self.prompt_generator.generate_agent_response_prompt(
                    conversation_history=conversation_history,
                    current_stage="SupportSystemAssessment", # Stay in current area
                    patient_name=patient_data["first_name"],
                    surgery_date=patient_data.get("surgery_date").strftime("%B %d, %Y") if patient_data.get("surgery_date") else "your scheduled date",
                    report=extracted_report
                )
                agent_response_text = self.llm_client.generate_response(agent_response_prompt_messages, max_output_tokens=120)

        # Initial assessment closing stage
        elif current_stage == "Closing":
            # Generate closing message using LLM
            agent_response_prompt_messages = self.prompt_generator.generate_agent_response_prompt(
                conversation_history=conversation_history,
                current_stage="Closing",
                patient_name=patient_data["first_name"],
                surgery_date=patient_data.get("surgery_date").strftime("%B %d, %Y") if patient_data.get("surgery_date") else "your scheduled date",
                report=extracted_report
            )
            agent_response_text = self.llm_client.generate_response(agent_response_prompt_messages, max_output_tokens=120)
            new_call_status = "completed"
            call_duration_seconds = (datetime.datetime.now() - actual_call_start).total_seconds()

        # Return the final response data for initial assessment  
        conversation_history.append({"role": "assistant", "content": agent_response_text})
        
        return {
            "response_text": agent_response_text,
            "current_stage": current_stage,
            "updated_conversation_history": conversation_history,
            "updated_clinical_data": extracted_report,
            "new_call_status": new_call_status,
            "actual_call_start": actual_call_start,
            "call_duration_seconds": call_duration_seconds,
            "context_metadata": {"nlu_result": nlu_result, "current_stage": current_stage},
            "current_call_status": new_call_status
        }

    def _handle_preparation_call_logic(self, current_stage, conversation_history, extracted_report, 
                                     patient_data, actual_call_start, new_call_status, call_duration_seconds, nlu_result):
        """Handle all logic specific to preparation calls"""
        
        if current_stage == "Greeting":
            agent_response_prompt_messages = self.prompt_generator.generate_agent_response_prompt(
                conversation_history=conversation_history,
                current_stage="Greeting",
                patient_name=patient_data["first_name"],
                surgery_date=patient_data.get("surgery_date").strftime("%B %d, %Y") if patient_data.get("surgery_date") else "your scheduled date",
                report=extracted_report
            )
            agent_response_text = self.llm_client.generate_response(agent_response_prompt_messages, max_output_tokens=120)
            new_call_status = "in_progress"

        elif current_stage == "InitialConfirmation":
            # Handle ready confirmation for preparation calls
            if extracted_report.get("preparation_call", {}).get("ready_confirmed"):
                agent_response_prompt_messages = self.prompt_generator.generate_agent_response_prompt(
                    conversation_history=conversation_history,
                    current_stage="HomeSafetyAssessment",
                    patient_name=patient_data["first_name"],
                    surgery_date=patient_data.get("surgery_date").strftime("%B %d, %Y") if patient_data.get("surgery_date") else "your scheduled date",
                    report=extracted_report
                )
                agent_response_text = self.llm_client.generate_response(agent_response_prompt_messages, max_output_tokens=120)
                current_stage = "HomeSafetyAssessment"
            else:
                agent_response_prompt_messages = self.prompt_generator.generate_agent_response_prompt(
                    conversation_history=conversation_history,
                    current_stage="InitialConfirmation",
                    patient_name=patient_data["first_name"],
                    surgery_date=patient_data.get("surgery_date").strftime("%B %d, %Y") if patient_data.get("surgery_date") else "your scheduled date",
                    report=extracted_report
                )
                agent_response_text = self.llm_client.generate_response(agent_response_prompt_messages, max_output_tokens=120)

        elif current_stage == "HomeSafetyAssessment":
            if self._is_area_complete_by_call_type(extracted_report, "HomeSafetyAssessment", "preparation"):
                agent_response_prompt_messages = self.prompt_generator.generate_agent_response_prompt(
                    conversation_history=conversation_history,
                    current_stage="MedicalEquipmentAssessment", # Transition to next area
                    patient_name=patient_data["first_name"],
                    surgery_date=patient_data.get("surgery_date").strftime("%B %d, %Y") if patient_data.get("surgery_date") else "your scheduled date",
                    report=extracted_report
                )
                agent_response_text = self.llm_client.generate_response(agent_response_prompt_messages, max_output_tokens=120)
                current_stage = "MedicalEquipmentAssessment"
            else:
                # Generate next question for HomeSafetyAssessment using LLM
                agent_response_prompt_messages = self.prompt_generator.generate_agent_response_prompt(
                    conversation_history=conversation_history,
                    current_stage="HomeSafetyAssessment", # Stay in current area
                    patient_name=patient_data["first_name"],
                    surgery_date=patient_data.get("surgery_date").strftime("%B %d, %Y") if patient_data.get("surgery_date") else "your scheduled date",
                    report=extracted_report
                )
                agent_response_text = self.llm_client.generate_response(agent_response_prompt_messages, max_output_tokens=120)

        elif current_stage == "MedicalEquipmentAssessment":
            if self._is_area_complete_by_call_type(extracted_report, "MedicalEquipmentAssessment", "preparation"):
                agent_response_prompt_messages = self.prompt_generator.generate_agent_response_prompt(
                    conversation_history=conversation_history,
                    current_stage="MedicationReview", # Transition to next area
                    patient_name=patient_data["first_name"],
                    surgery_date=patient_data.get("surgery_date").strftime("%B %d, %Y") if patient_data.get("surgery_date") else "your scheduled date",
                    report=extracted_report
                )
                agent_response_text = self.llm_client.generate_response(agent_response_prompt_messages, max_output_tokens=120)
                current_stage = "MedicationReview"
            else:
                # Generate next question for MedicalEquipmentAssessment using LLM
                agent_response_prompt_messages = self.prompt_generator.generate_agent_response_prompt(
                    conversation_history=conversation_history,
                    current_stage="MedicalEquipmentAssessment", # Stay in current area
                    patient_name=patient_data["first_name"],
                    surgery_date=patient_data.get("surgery_date").strftime("%B %d, %Y") if patient_data.get("surgery_date") else "your scheduled date",
                    report=extracted_report
                )
                agent_response_text = self.llm_client.generate_response(agent_response_prompt_messages, max_output_tokens=120)

        elif current_stage == "MedicationReview":
            if self._is_area_complete_by_call_type(extracted_report, "MedicationReview", "preparation"):
                agent_response_prompt_messages = self.prompt_generator.generate_agent_response_prompt(
                    conversation_history=conversation_history,
                    current_stage="Closing", # Transition to closing
                    patient_name=patient_data["first_name"],
                    surgery_date=patient_data.get("surgery_date").strftime("%B %d, %Y") if patient_data.get("surgery_date") else "your scheduled date",
                    report=extracted_report
                )
                agent_response_text = self.llm_client.generate_response(agent_response_prompt_messages, max_output_tokens=120)
                new_call_status = "completed" # Mark call as completed
                call_duration_seconds = (datetime.datetime.now() - actual_call_start).total_seconds()
                current_stage = "Closing"
            else:
                # Generate next question for MedicationReview using LLM
                agent_response_prompt_messages = self.prompt_generator.generate_agent_response_prompt(
                    conversation_history=conversation_history,
                    current_stage="MedicationReview", # Stay in current area
                    patient_name=patient_data["first_name"],
                    surgery_date=patient_data.get("surgery_date").strftime("%B %d, %Y") if patient_data.get("surgery_date") else "your scheduled date",
                    report=extracted_report
                )
                agent_response_text = self.llm_client.generate_response(agent_response_prompt_messages, max_output_tokens=120)
        
        # Preparation call closing stage
        elif current_stage == "Closing":
            agent_response_prompt_messages = self.prompt_generator.generate_agent_response_prompt(
                conversation_history=conversation_history,
                current_stage="Closing",
                patient_name=patient_data["first_name"],
                surgery_date=patient_data.get("surgery_date").strftime("%B %d, %Y") if patient_data.get("surgery_date") else "your scheduled date",
                report=extracted_report
            )
            agent_response_text = self.llm_client.generate_response(agent_response_prompt_messages, max_output_tokens=120)
            new_call_status = "completed"
            call_duration_seconds = (datetime.datetime.now() - actual_call_start).total_seconds()

        # Return the final response data for preparation call
        conversation_history.append({"role": "assistant", "content": agent_response_text})

        return {
            "response_text": agent_response_text,
            "current_stage": current_stage,
            "updated_conversation_history": conversation_history,
            "updated_clinical_data": extracted_report,
            "new_call_status": new_call_status,
            "actual_call_start": actual_call_start,
            "call_duration_seconds": call_duration_seconds,
            "context_metadata": {"nlu_result": nlu_result, "current_stage": current_stage},
            "current_call_status": new_call_status
        }
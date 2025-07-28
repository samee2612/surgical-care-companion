from typing import Dict, Any, TypedDict
import json

class NLUResponse(TypedDict, total=False):
    intent: str
    entities: Dict[str, Any]
    summary: str
    next_state: str

class NLURequest(TypedDict):
    user_message: str
    conversation_history: list
    dialogue_state: str
    call_type: str

class NLUService:
    def __init__(self):
        # Placeholder for potential model initialization
        pass

    def process(self, request: NLURequest) -> NLUResponse:
        # This is where you would call the LLM with a specialized NLU prompt.
        # For now, we'll use a rule-based mock to simulate the LLM's NLU capabilities.
        return self._mock_nlu_processing(request)

    def _mock_nlu_processing(self, request: NLURequest) -> NLUResponse:
        user_message = request['user_message'].lower()
        state = request['dialogue_state']
        entities = {}
        intent = "provide_information" # Default intent

        # Simple rule-based entity extraction
        if state == "ASKING_PAIN":
            for i in range(1, 11):
                if str(i) in user_message:
                    entities['pain_level'] = i
        
        if state == "ASKING_SUPPORT":
            support_words = ["husband", "wife", "friend", "family", "daughter", "son"]
            for word in support_words:
                if word in user_message:
                    entities['support_person'] = word

        # Simple intent detection
        if "yes" in user_message or "right" in user_message:
            intent = "confirm"
        elif "no" in user_message or "wrong" in user_message:
            intent = "deny"
        elif "?" in user_message:
            intent = "ask_question"
            
        return {
            "intent": intent,
            "entities": entities,
            "summary": f"User's message was: {request['user_message']}",
            "next_state": self._determine_next_state(state, intent, entities)
        }

    def _determine_next_state(self, current_state: str, intent: str, entities: Dict[str, Any]) -> str:
        # This is the core of the state machine logic
        transitions = {
            "STARTED": "ASKING_FEELINGS",
            "ASKING_FEELINGS": "ASKING_PAIN",
            "ASKING_PAIN": "ASKING_ACTIVITIES",
            "ASKING_ACTIVITIES": "ASKING_SUPPORT",
            "ASKING_SUPPORT": "COMPLETED",
        }
        return transitions.get(current_state, current_state) # Default to staying in the same state

_nlu_service = None

def get_nlu_service() -> NLUService:
    global _nlu_service
    if _nlu_service is None:
        _nlu_service = NLUService()
    return _nlu_service 
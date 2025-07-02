import os
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
from pymongo import MongoClient
from dotenv import load_dotenv
import datetime

load_dotenv()

app = Flask(__name__)

# --- Twilio Credentials ---
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER") # Your Twilio number

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# --- MongoDB Setup ---
MONGO_URI = os.getenv("MONGO_URI")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client.Healthsense24 # Your database name
patient_profiles_collection = db.PatientProfiles
interaction_logs_collection = db.InteractionLogs

# --- HELPER FUNCTIONS ---
def log_interaction(patient_id, call_direction, call_reason, user_transcript="", ai_response="", intent="", entities=None, escalation=False, escalation_reason=""):
    interaction_logs_collection.insert_one({
        "patient_id": patient_id,
        "timestamp": datetime.datetime.now(),
        "call_direction": call_direction,
        "call_reason": call_reason,
        "user_input_transcript": user_transcript,
        "ai_response_text": ai_response,
        "intent_detected": intent,
        "entities_extracted": entities if entities else {},
        "escalation_flag": escalation,
        "escalation_reason": escalation_reason
    })

def perform_basic_nlu(transcript):
    """Very basic NLU for MVP: pain level and simple yes/no."""
    transcript_lower = transcript.lower()
    intent = "unknown"
    entities = {}
    escalation = False
    escalation_reason = ""

    # Basic Pain Level Detection
    pain_keywords = {str(i): i for i in range(1, 11)} # "1" -> 1, ..., "10" -> 10
    for word, val in pain_keywords.items():
        if f" {word} " in transcript_lower or transcript_lower.startswith(word + " ") or transcript_lower.endswith(" " + word):
            intent = "ReportPain"
            entities["pain_level"] = val
            if val >= 7: # High pain for escalation
                escalation = True
                escalation_reason = "High pain reported."
            break

    # Basic Yes/No Confirmation (for pre-op reminder)
    if "yes" in transcript_lower or "yep" in transcript_lower:
        intent = "Confirmation"
        entities["confirmation"] = "yes"
    elif "no" in transcript_lower or "nope" in transcript_lower:
        intent = "Confirmation"
        entities["confirmation"] = "no"

    # You would expand this significantly with a proper NLU service or more complex regex/ML

    return intent, entities, escalation, escalation_reason

# --- FLASK ROUTES ---

@app.route("/make_call/<patient_id>", methods=['GET'])
def make_call(patient_id):
    """Endpoint to initiate an outbound call to a patient."""
    patient = patient_profiles_collection.find_one({"_id": patient_id})
    if not patient:
        return "Patient not found", 404

    patient_phone = patient.get("contact_phone_number")
    call_reason = "Scheduled Check-in" # For MVP

    # In a real system, you'd dynamically determine the TwiML URL based on patient's phase/reason
    # For MVP, we'll use a fixed TwiML URL for Post-Op Day 1 for demonstration
    twiml_url = f"{os.getenv('PUBLIC_NGROK_URL')}/twiml_post_op_day1/{patient_id}"

    try:
        call = twilio_client.calls.create(
            to=patient_phone,
            from_=TWILIO_PHONE_NUMBER,
            url=twiml_url
        )
        print(f"Call initiated to {patient_phone}, SID: {call.sid}")
        log_interaction(patient_id, "Outbound", call_reason, ai_response=f"Call initiated. TwiML URL: {twiml_url}")
        return f"Call initiated to {patient_phone}", 200
    except Exception as e:
        print(f"Error making call: {e}")
        return f"Error making call: {e}", 500

@app.route("/twiml_post_op_day1/<patient_id>", methods=['POST'])
def twiml_post_op_day1(patient_id):
    """TwiML for Post-Op Day 1 check-in."""
    patient = patient_profiles_collection.find_one({"_id": patient_id})
    patient_name = patient.get("name", "patient") if patient else "patient"

    response = VoiceResponse()
    gather = Gather(input='speech', action=f"/handle_response_post_op_day1/{patient_id}", timeout=5)
    gather.say(f"Hello {patient_name}, this is Healthsense24 calling for your day 1 post-surgery check-in. On a scale of 1 to 10, how would you rate your current knee pain, where 1 is no pain and 10 is the worst pain imaginable?")
    response.append(gather)
    response.say("We did not receive a response. Please call your clinic if you need assistance.")

    log_interaction(patient_id, "Outbound", "Post-Op Day 1 Check-in", ai_response=response.to_xml())
    return str(response)

@app.route("/handle_response_post_op_day1/<patient_id>", methods=['POST'])
def handle_response_post_op_day1(patient_id):
    """Handles patient's response from Post-Op Day 1 check-in."""
    response = VoiceResponse()

    # Get patient's transcribed speech
    speech_result = request.form.get('SpeechResult', '')
    print(f"Patient {patient_id} said: {speech_result}")

    # Perform basic NLU
    intent, entities, escalation, escalation_reason = perform_basic_nlu(speech_result)

    ai_response_text = "Thank you for your update."
    if intent == "ReportPain" and entities.get("pain_level"):
        pain_level = entities["pain_level"]
        ai_response_text = f"Thank you. You reported a pain level of {pain_level}."
        if escalation:
            ai_response_text += " Your care team has been notified for follow-up regarding your pain."
    elif intent == "unknown":
        ai_response_text = "I'm sorry, I didn't understand your response. Please call your clinic if you need assistance."

    response.say(ai_response_text)
    response.hangup()

    log_interaction(patient_id, "Inbound", "Post-Op Day 1 Check-in Response", 
                    user_transcript=speech_result, 
                    ai_response=ai_response_text,
                    intent=intent, 
                    entities=entities, 
                    escalation=escalation, 
                    escalation_reason=escalation_reason)

    return str(response)

if __name__ == "__main__":
    # --- Local Testing Setup ---
    # NOTE: For Twilio webhooks to work locally, you need a public URL.
    # Use ngrok: https://ngrok.com/download
    # After running 'ngrok http 5000', update PUBLIC_NGROK_URL in your .env
    # And configure Twilio webhook for your phone number to point to:
    # YOUR_PUBLIC_NGROK_URL/twiml_post_op_day1/<patient_id> (as example)

    # For the /make_call endpoint to work from your browser/postman, 
    # you also need PUBLIC_NGROK_URL for the twiml_url.

    # Add a dummy patient for local testing
    dummy_patient_id = "test_patient_123"
    dummy_patient_data = {
        "_id": dummy_patient_id,
        "name": "Test Patient",
        "contact_phone_number": "+2132556304", # Replace with YOUR phone number for testing
        "surgical_procedure": "Total Knee Replacement",
        "surgery_date": datetime.datetime(2025, 6, 18),
        "current_care_phase": "Post-Op Day 1"
    }
    # Insert only if not exists
    if patient_profiles_collection.count_documents({"_id": dummy_patient_id}) == 0:
        patient_profiles_collection.insert_one(dummy_patient_data)
        print(f"Inserted dummy patient: {dummy_patient_id}")
    else:
        print(f"Dummy patient {dummy_patient_id} already exists.")


    print("\n--- Local Flask App Running ---")
    print("1. Start ngrok: 'ngrok http 5000' and update PUBLIC_NGROK_URL in .env")
    print(f"2. Set Twilio Voice webhook for '{TWILIO_PHONE_NUMBER}' to: YOUR_PUBLIC_NGROK_URL/handle_response_post_op_day1/<patient_id>")
    print(f"3. Make a test call: http://127.0.0.1:5000/make_call/{dummy_patient_id} (or trigger via API call)")
    print("-----------------------------\n")

    app.run(debug=True)
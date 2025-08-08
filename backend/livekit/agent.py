# import asyncio
# import json
# import os
# import httpx
# from livekit import agents
# from livekit.agents import AgentSession, Agent, JobContext, WorkerOptions, cli
# from livekit.plugins import elevenlabs, silero, groq
# from dotenv import load_dotenv

# load_dotenv()

# CONVERSE_API_URL = os.getenv('CONVERSE_API_URL', 'http://localhost:8000/api/v1/chat/converse')

# class SurgicalCareAssistant(Agent):
#     def __init__(self, patient_id=None, call_session_id=None):
#         super().__init__(
#             instructions="You are a compassionate surgical care assistant for surgery TKA. Your role is to talk with patients about their recovery progress, console them, answer their questions about post-operative care, and provide emotional support. Always speak in a warm, professional, and human-like manner. Keep responses short and concise."
#         )
#         self.patient_id = patient_id
#         self.call_session_id = call_session_id

#     async def generate_llm_reply(self, message=None):
#         payload = {
#             "patient_id": self.patient_id,
#             "call_session_id": self.call_session_id,
#             "message": message
#         }
#         async with httpx.AsyncClient() as client:
#             response = await client.post(CONVERSE_API_URL, json=payload)
#             data = response.json()
#             return data.get("response", "")

# async def entrypoint(ctx: JobContext):
#     # Parse patient_id and call_session_id from metadata
#     metadata = ctx.job.metadata if ctx.job else "{}"
#     phone_number = None
#     patient_id = None
#     call_session_id = None
#     try:
#         dial_info = json.loads(metadata)
#         phone_number = dial_info.get("phone_number")
#         patient_id = dial_info.get("patient_id")
#         call_session_id = dial_info.get("call_session_id")
#     except Exception:
#         pass

#     # Fallback: require patient_id and call_session_id
#     if not patient_id or not call_session_id:
#         raise RuntimeError("patient_id and call_session_id must be provided in job metadata.")

#     assistant = SurgicalCareAssistant(patient_id=patient_id, call_session_id=call_session_id)

#     session = AgentSession(
#         stt=groq.STT(
#             model="whisper-large-v3-turbo",
#             language="en",
#         ),
#         llm=None,  # LLM is handled via converse API
#         tts=elevenlabs.TTS(
#             voice_id="BIvP0GN1cAtSRTxNHnWS"
#         ),
#         vad=silero.VAD.load(),
#     )

#     await session.start(
#         room=ctx.room,
#         agent=assistant,
#     )

#     await ctx.connect()

#     # Initial greeting (no message)
#     initial_reply = await assistant.generate_llm_reply(message=None)
#     await session.say(initial_reply)
#     print(f"Initial greeting: {initial_reply}")
#     # Main loop: for each user transcript, send to converse API and speak response
#     while True:
#         transcript = await session.listen()
#         if transcript is None:
#             break  # Call ended
#         # Send transcript to converse API
#         llm_reply = await assistant.generate_llm_reply(message=transcript)
#         print(llm_reply)
#         await session.say(llm_reply)

# if __name__ == "__main__":
#     cli.run_app(WorkerOptions(
#         entrypoint_fnc=entrypoint,
#         agent_name="surgical-care-assistant"
#     ))

import asyncio
import json
import os
import httpx
from livekit import agents
from livekit.agents import AgentSession, Agent, JobContext, WorkerOptions, cli
from livekit.plugins import elevenlabs, silero, deepgram
from dotenv import load_dotenv

load_dotenv()

CONVERSE_API_URL = os.getenv('CONVERSE_API_URL', 'http://localhost:8000/api/v1/chat/converse')
# CONVERSE_API_URL = os.getenv('CONVERSE_API_URL', 'http://host.docker.internal:8000/api/v1/chat/converse')

class SurgicalCareAssistant(Agent):
    def __init__(self, patient_id=None, call_session_id=None):
        super().__init__(
            # Note: these instructions aren't used since llm=None, but are good for clarity
            instructions="You are a compassionate surgical care assistant for surgery TKA. Your role is to talk with patients about their recovery progress, console them, answer their questions about post-operative care, and provide emotional support. Always speak in a warm, professional, and human-like manner. Keep responses short and concise."
        )
        self.patient_id = patient_id
        self.call_session_id = call_session_id

    async def generate_llm_reply(self, message=""):
        payload = {
            "patient_id": self.patient_id,
            "call_session_id": self.call_session_id,
            "message": message
        }

        print(f"Sending request to {CONVERSE_API_URL} with payload: {payload}")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(CONVERSE_API_URL, json=payload, timeout=20)
                response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
                data = response.json()
                return data.get("response", "")
        except httpx.RequestError as e:
            print(f"Error calling converse API: {e}")
            # Fallback response in case of API failure
            return "I'm sorry, I'm having trouble connecting to my systems right now. Please try again in a moment."


async def entrypoint(ctx: JobContext):
    print("--- AGENT STARTING ---")
    
    # Parse patient_id and call_session_id from metadata
    metadata = ctx.job.metadata if ctx.job else "{}"
    patient_id = None
    call_session_id = None
    try:
        dial_info = json.loads(metadata)
        patient_id = dial_info.get("patient_id")
        call_session_id = dial_info.get("call_session_id")
        print(f"1. Parsed metadata: patient_id={patient_id}, call_session_id={call_session_id}")
    except (json.JSONDecodeError, TypeError):
        pass

    # Fallback: require patient_id and call_session_id
    if not patient_id or not call_session_id:
        print("ERROR: patient_id and call_session_id not found in metadata.")
        raise RuntimeError("patient_id and call_session_id must be provided in job metadata.")

    assistant = SurgicalCareAssistant(patient_id=patient_id, call_session_id=call_session_id)

    session = AgentSession(
        stt=deepgram.STT(
            model="nova-2",
            language="en-US",
        ),
        llm=None,
        tts=elevenlabs.TTS(
            voice_id="BIvP0GN1cAtSRTxNHnWS"
        ),
        vad=silero.VAD.load(),
    )

    session.say_interrupted_by_user_sound = None

    await session.start(
        room=ctx.room,
        agent=assistant,
    )
    
    print("2. Connecting to LiveKit room...")
    await ctx.connect()
    print("3. Connected successfully.")

    # Initial greeting
    try:
        print("4. Getting initial greeting from API...")
        initial_reply = await assistant.generate_llm_reply(message="")
        print(f"5. Got API response: '{initial_reply}'")

        if initial_reply:
            print("6. Speaking initial greeting...")
            await session.say(initial_reply)
            print("7. Finished speaking.")
        else:
            print("WARNING: API returned an empty initial reply.")
    except Exception as e:
        print(f"ERROR during initial greeting: {e}")
        # Still try to continue the loop
    
    # Main loop
    # while True:
    #     try:
    #         print("\n8. Now listening for user to speak...")
    #         transcript = await session.listen()
            
    #         if transcript is None:
    #             print("Call ended by user or system.")
    #             break

    #         print(f"9. User said: '{transcript}'")
            
                  
    print("\n8. Now listening for user to speak...")
    stt_stream = session.stt.stream()
    async for transcript in stt_stream:
        # if not transcript.is_final:
        #     continue
        print(f"DEBUG: transcript object: {transcript}")
        print(f"DEBUG: transcript.is_final: {getattr(transcript, 'is_final', None)}")
        print(f"DEBUG: transcript.text: {getattr(transcript, 'text', None)}")
        if not getattr(transcript, "text", "").strip():  # Default to True if missing
            continue
        # print(f"9. User said: '{transcript.text}'")

        print(f"9. User said: '{transcript.text}'")
        
        try:
            print("10. Getting API response for user's message...")
            llm_reply = await assistant.generate_llm_reply(message=transcript.text)
            print(f"11. Got API response: '{llm_reply}'")

            if llm_reply:
                print("12. Speaking API response...")
                await session.say(llm_reply)
                print("13. Finished speaking.")
            else:
                print("WARNING: API returned an empty response.")
        except asyncio.CancelledError:
            print("Loop cancelled.")
            break
        except Exception as e:
            print(f"ERROR in main loop: {e}")
            break

    print("--- AGENT FINISHED ---")

if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        agent_name="surgical-care-assistant"
    ))
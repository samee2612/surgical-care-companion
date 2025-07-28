# llm_client.py
import google.generativeai as genai
import os

class LLMClient:
    def __init__(self, api_key: str):
        print("LLM_CLIENT_INIT: Entering LLMClient constructor.") # This print should appear.

        # --- NEW GRANULAR PRIfNTS ---
        print("LLM_CLIENT_INIT: Calling genai.configure...")
        genai.configure(api_key=api_key)
        print("LLM_CLIENT_INIT: genai.configure completed.")

        print("LLM_CLIENT_INIT: Attempting to load GenerativeModel (gemini-flash)...")
        self.model = genai.GenerativeModel('models/gemini-2.5-flash-lite')
        print("LLM_CLIENT_INIT: GenerativeModel loaded successfully.")
        # --- END NEW GRANULAR PRINTS ---

        print("LLM_CLIENT_INIT: Gemini model configured and loaded.") # Original final print.

    def generate_response(self, prompt_parts: list, max_output_tokens: int = 250) -> str:
        print("LLM_CLIENT: Calling Gemini Flash API.") # Add this
        """
        Calls Gemini Flash to generate a conversational response.
        
        Args:
        
            prompt_parts: A list of dicts representing the conversation history and system instructions.
                          e.g., [{"role": "user", "parts": ["hello"]}, {"role": "model", "parts": ["hi"]}]
            max_output_tokens: Limits the length of the LLM's response to control tokens and conciseness.
        Returns:
            The generated text response.
        """
        generation_config = {
            "max_output_tokens": max_output_tokens,
            "temperature": 0.7, # Adjust for creativity (lower for more factual/direct)
            "top_p": 0.95,
            "top_k": 60
        }
        
        try:
            # The API expects messages as a list of dictionaries with "role" and "parts"
            # We'll construct this from prompt_parts which comes from PromptGenerator
            
            # For Gemini, the roles are "user" and "model".
            # Ensure your prompt_parts adhere to this format.
            
            response = self.model.generate_content(
                prompt_parts, # Pass the list of messages
                generation_config=generation_config
            )
            print("LLM_CLIENT: Received response from Gemini Flash API.") # Add this
            
            # Check if response exists and has text
            if response and response.candidates:
                return response.candidates[0].content.parts[0].text
            return "..." # Fallback response
        except Exception as e:
            print(f"LLM_CLIENT: Error calling Gemini Flash: {e}") # Add this
            return "I apologize, but I'm having trouble connecting right now. Please try again later or contact the clinic."
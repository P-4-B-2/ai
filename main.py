import sounddevice as sd
from stt.stt_vosk import record_audio, create_recognizer, transcribe_audio
# from tts import speak_text
from response_generation.qa import GeneralQAAgent
from questionnaire import get_question
from database_firebase import initialize_database, log_interaction
from tts.tts_pygame import text_to_speech
import os
from response_generation.manager import ManagerAgent
# Audio settings
SAMPLE_RATE = 16000
CHANNELS = 1
DURATION = 8

def main():
    # initialize_database()  # Ensure the database is ready
    bench = GeneralQAAgent()
    conversation_history = []

    question_index = 0
    question = get_question(question_index)
    # text_to_speech("Hello! I am your friendly Talking Bench." + question)
    text_to_speech("Hallo." + question)

    conversation_history.append({"bench": question})
    print(f"Asked: {question}")
    while True:
        # Record and transcribe audio

        user_message = transcribe_audio()

        print(f"User said: {user_message }")

        # Process the response with LLM
        response = bench.generate_response(user_message , conversation_history)
        text_to_speech(response)
        print(f"Asked: {response}")
         # Update conversation history
        conversation_history.append({
            "user": user_message,
            "bench": response
        })
        question_index += 1

if __name__ == "__main__":
    main()
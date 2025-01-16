import sounddevice as sd
from stt.stt_whisper_claude import SpeechToTextAgent
from response_generation.detailed_qa_claude import GeneralQAAgent
from tts.tts_pygame import TTSAgent
import os
from response_generation.manager_claude2 import ManagerAgent


def main():
    qa_agent = GeneralQAAgent()
    stt_agent = SpeechToTextAgent(model_name="base")
    tts_agent = TTSAgent()

    manager = ManagerAgent(qa_agent, stt_agent, tts_agent)

    welcome_message = """
        Hello! I'm your friendly city feedback bench. I'm here to hear your thoughts about our city and collect your ideas for making it even better. Would you like to share your experiences with me?
        """
    manager.tts_agent.text_to_speech(welcome_message)

    print("Starting conversation loop...")

    manager.run()

    farewell_message = """
        Thank you for sharing your thoughts with me! Your feedback will help make our city better. Have a wonderful rest of your day!
        """
    manager.tts_agent.text_to_speech(farewell_message)
    
if __name__ == "__main__":
    main()


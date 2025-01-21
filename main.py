import sounddevice as sd
import os
from stt.stt_whisper import SpeechToTextAgent
from response_generation.qa import GeneralQAAgent
from tts.tts_pygame import TTSAgent
from response_generation.manager import ManagerAgent
from response_generation.evaluator import ResponseEvaluator


def main():
    qa_agent = GeneralQAAgent()
    stt_agent = SpeechToTextAgent(model_name="base")
    tts_agent = TTSAgent()
    evaluator_agent = ResponseEvaluator()

    manager = ManagerAgent(qa_agent, stt_agent, tts_agent, evaluator_agent)

    # welcome_message = """
    #     Please note that this conversation will be recorded and your feedback will be used within our business. Please don't share any personal information with the bench! 
    # Hello! I'm your friendly city feedback bench. I'm here to hear your thoughts about our city and collect your ideas for making it even better. Would you like to share your experiences with me? 
    #     """
    # manager.tts_agent.text_to_speech(welcome_message)

    print("Starting conversation loop...")

    manager.run()

    print("Stopping conversation loop...")

    
if __name__ == "__main__":
    main()


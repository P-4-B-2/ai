import sounddevice as sd
import os
from stt.stt_whisper import SpeechToTextAgent
from llm import LLMAgent
from tts.tts import TTSAgent
from manager_english_backup import ManagerAgent


def main():
    language = "en"
    llm_agent = LLMAgent()
    stt_agent = SpeechToTextAgent(model_name="base", language=language)
    tts_agent = TTSAgent(language = language)

    manager = ManagerAgent(llm_agent, stt_agent, tts_agent, "https://dev1.sebastiaandaniels.com/", 1)

    welcome_message = """
        Please note that this conversation will be recorded and your feedback will be used within our business. Please don't share any personal information with the bench! 
    Hello! I'm your friendly city feedback bench. I'm here to hear your thoughts about our city and collect your ideas for making it even better. Would you like to share your experiences with me? 
        """
    manager.tts_agent.text_to_speech(welcome_message)

    manager.run()

    
if __name__ == "__main__":
    main()


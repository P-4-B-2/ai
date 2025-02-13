from stt.stt_whisper import SpeechToTextAgent
from llm_dutch import LLMAgent
from tts.tts import TTSAgent
from manager_dutch import ManagerAgent


def main():
    
    llm_agent = LLMAgent()
    stt_agent = SpeechToTextAgent(model_name="base")
    tts_agent = TTSAgent()

    manager = ManagerAgent(llm_agent, stt_agent, tts_agent, "https:/frankdepratendebank.azurewebsites.net/", 1)

    # welcome_message = """Let op, dit gesprek wordt opgenomen en jouw feedback zal binnen ons bedrijf worden gebruikt. Deel alsjeblieft geen persoonlijke informatie met de bank! 
    # Hallo! Ik ben jouw vriendelijke stadfeedbackbank. Ik ben hier om jouw gedachten over onze stad te horen en je ideeën te verzamelen om het nog beter te maken. Wil je jouw ervaringen met mij delen? 
    #     """

    # manager.tts_agent.text_to_speech(welcome_message)

    print("Starting conversation loop...")

    manager.run()

    print("Stopping conversation loop...")

    
if __name__ == "__main__":
    main()


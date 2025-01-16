# from response_generation.qa import GeneralQAAgent
from response_generation.detailed_qa import GeneralQAAgent
from database_firebase import initialize_database, log_interaction
import json
from groq import Groq
import os

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

class ManagerAgent:
    def __init__(self, qa_agent, stt_agent, tts_agent):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.qa_agent = qa_agent
        self.stt_agent = stt_agent
        self.tts_agent = tts_agent


    def load_questionnaire(self, file_path="questions_nl.json"):
        """
        Load the predefined questionnaire from a JSON file.
        """
        with open(file_path, 'r') as file:
            self.questionnaire = json.load(file)
        for question in self.questionnaire:
            question['asked'] = False


    def get_question(self, index):
        questions = self.load_questions()

        """
        Returns the next question in the questionnaire, or None if complete.
        """
        return questions[index]["question"] if index < len(questions) else None


    def decide_next_step(self, question, response):
        """
        Sends a prompt to the Groq LLM and retrieves the response.
        
        :param prompt: The text prompt to send to the LLM.
        :return: The response from the LLM as a string.
        """
        prompt = """
        Context: The goal is to gather meaningful feedback from the user.
        Decide:
        - If the response: {response} is sufficient and related to the question {question}, reply with "move_to_next".
        - If the response: {response} is unclear or insufficient, reply with "".
        """

        response = self.client.completion(
            model="llama-3.1-70b-versatile",
            prompt=prompt,
            max_tokens=100,
            temperature=0.7,
            stop=None  # Adjust the stopping condition if needed
        )
        return response.get("choices", [{}])[0].get("text", "").strip()
 

    def run(self):
        """
        Execute the AI-driven questionnaire loop.
        """
        conversation_history = []
        current_question_index=0

        while self.current_question_index < len(self.questionnaire):
            # Ask the initial question
            question = self.questionnaire[self.current_question_index]
            self.tts_agent.text_to_speech(question)
            conversation_history.append({"bench": question})
            print(f"Asked: {question}")

            while True:
                # Get user reply
                user_message = self.stt_agent.transcribe_audio()
                print(f"User said: {user_message }")

                # LLM decides the next step
                decision = self.decide_next_step(question, user_message)

                if decision.startswith("move_to_next"):
                    self.current_question_index += 1
                    qa_response = self.qa_agent.generate_response(user_message , conversation_history, question)
                    self.tts_agent.text_to_speech(question)
                    print(f"Asked: {qa_response}")

                elif decision.startswith(""):
                    qa_response = self.qa_agent.generate_response(user_message , conversation_history, question)
                    self.tts_agent.speak(qa_response)

                conversation_history.append({
            "user": user_message,
            "bench": qa_response
        })

      
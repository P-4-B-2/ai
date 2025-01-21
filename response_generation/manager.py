from typing import List, Dict, Optional
import json
from pathlib import Path
import os

class ManagerAgent:
    def __init__(self, qa_agent, stt_agent, tts_agent, evaluator_agent):
        self.qa_agent = qa_agent
        self.stt_agent = stt_agent
        self.tts_agent = tts_agent
        self.evaluator_agent=evaluator_agent
        self.questionnaire: List[Dict] = []
        self.current_question_index = 0
        self.max_follow_ups = 2

    def load_questionnaire(self, file_path: str = "questions.json") -> None:
        """
        Load the predefined questionnaire from a JSON file.
        
        Args:
            file_path: Path to the JSON questionnaire file
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Questionnaire file not found: {file_path}")
            
        with open(file_path, 'r') as file:
            self.questionnaire = json.load(file)

    def get_question(self, index: int) -> Optional[str]:
        """Get question at specified index."""
        if 0 <= index < len(self.questionnaire):
            return self.questionnaire[index]["question"]
        return None
  

    def run(self) -> None:
        """Execute the AI-driven questionnaire loop."""
        conversation_history: List[Dict] = []
        self.load_questionnaire()

        while self.current_question_index < len(self.questionnaire):
            current_question = self.get_question(self.current_question_index)
            if not current_question:
                break

            # Ask the first question
            self.tts_agent.text_to_speech(current_question)
            conversation_history.append({"bench": current_question})
            print(f"\nCurrent question: {current_question}")

            # Prompt variables
            next_question = None
            follow_up_count = 0
            prompt= ""

            while True:
                try:
                    #Listen to the user
                    print("\nListening...")
                    user_message = self.stt_agent.transcribe_audio()
                    if not user_message:
                        continue
                    print(f"User said: {user_message}")

                    # Check if the user response is complete
                    is_response_complete = self.evaluator_agent.evaluate_response(
                        user_message,
                        conversation_history,
                        current_question,
                    )
                    print(is_response_complete)

                    # Check if the user wants to end the conversation
                    if is_response_complete == "End":
                        qa_response = """Thank you for sharing your thoughts with me! Your feedback will help make our city better. Have a wonderful rest of your day!"""
                        print(f"AI response: {qa_response}")

                        # Update conversation history
                        conversation_history.append({
                            "user": user_message,
                            "bench": qa_response
                        })
                        # Speak the bench response
                        self.tts_agent.text_to_speech(qa_response)
                        return  # Exit the entire run method
                    
                    # A detailed question can be asked max 2 times
                    if follow_up_count >= self.max_follow_ups:
                        print("The question was asked in details twice, so moving to the next one.")
                        is_response_complete="Yes"


                    # Work only with topic related questions
                    if is_response_complete!="Off":

                        # If the user response is complete ask the next question from the questionnaire
                        if is_response_complete=="Yes":

                            prompt= "1. Start with a warm greeting and explain your purpose. 2. Respond kindly to their answers. Acknowledge that we are moving to the next question of our questionnaire. 3. Ask a provided follow-up question."
                            print("User response is on-topic and complete.")
                            next_question = self.get_question(self.current_question_index + 1)
                            self.current_question_index += 1
                            follow_up_count = 0

                        # If the user response is not complete ask a more detailed question
                        elif is_response_complete=="No":
                            prompt= "1. Start with a warm greeting and explain your purpose. 2. Generate a clarifying question to kindly obtain more details or just a question to gather a user feedback about the city. The questions should be open-ended."
                            print("User response is on-topic, but incomplete. Asking for more details.")
                            next_question = None
                            follow_up_count += 1
                    else:

                        prompt= "Handle off-topic user responses by confirming what was heard and politely redirecting the conversation back to the questionnaire. 1. Acknowledgment of the user's input. If the user asks off-topic question do not answer that. 2. A kind statement that the focus is on the questionnaire topics. 3. Ask the follow-up question to smoothly guide the conversation back on track."
                        print("User response is off-topic. Asking the same question")
                        next_question = self.get_question(self.current_question_index)
                        follow_up_count+= 1

                    
                    qa_response = self.qa_agent.generate_response(
                                prompt,
                                user_message,
                                conversation_history,
                                follow_up_question=next_question
                            )
                    
                    # Debugging
                    print(follow_up_count)

                    print(f"AI response: {qa_response}")

                    # Speak the bench response
                    self.tts_agent.text_to_speech(qa_response)
                    # Update conversation history
                    conversation_history.append({
                            "user": user_message,
                            "bench": qa_response
                        })


                except Exception as e:
                    print(f"Error during conversation: {e}")
                    self.tts_agent.text_to_speech(
                        "I'm having trouble understanding. Could you please repeat that?"
                    )

        print("\nQuestionnaire completed!")

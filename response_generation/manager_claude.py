from typing import List, Dict, Optional
from response_generation.detailed_qa import GeneralQAAgent
import json
from pathlib import Path
from typing import List, Dict, Optional
import os
from pathlib import Path
import json

class ManagerAgent:
    def __init__(self, qa_agent, stt_agent, tts_agent):
        """
        Initialize the Manager Agent with required components.
        
        Args:
            qa_agent: Agent for handling Q&A interactions
            stt_agent: Speech-to-text agent
            tts_agent: Text-to-speech agent
        """
        self.qa_agent = qa_agent
        self.stt_agent = stt_agent
        self.tts_agent = tts_agent
        self.questionnaire: List[Dict] = []
        self.current_question_index = 0

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
            
        for question in self.questionnaire:
            question['asked'] = False

    def get_question(self, index: int) -> Optional[str]:
        """Get question at specified index."""
        if 0 <= index < len(self.questionnaire):
            return self.questionnaire[index]["question"]
        return None

    def run(self) -> None:
        """Execute the AI-driven questionnaire loop."""
        self.load_questionnaire()
        conversation_history: List[Dict] = []

        while self.current_question_index < len(self.questionnaire):
            current_question = self.get_question(self.current_question_index)
            if not current_question:
                break

            # Ask current question
            self.tts_agent.text_to_speech(current_question)
            conversation_history.append({"bench": current_question})
            print(f"Asked: {current_question}")

            while True:
                try:
                    # Get user response
                    user_message = self.stt_agent.transcribe_audio()
                    print(f"User said: {user_message}")

                    # Get next question for context
                    next_question = self.get_question(self.current_question_index + 1)

                    # Generate response using QA agent
                    qa_response = self.qa_agent.generate_response(
                        user_message,
                        conversation_history,
                        next_question
                    )

                    # Check if response indicates moving to next question
                    if "next question" in qa_response.lower() or len(conversation_history) >= 3:
                        self.tts_agent.text_to_speech(qa_response)
                        self.current_question_index += 1
                        break
                    else:
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
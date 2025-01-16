import time
from typing import List, Dict, Optional
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
        self.max_follow_ups = 3  # Maximum number of follow-up exchanges per question

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

    def should_move_to_next_question(self, qa_response: str, follow_up_count: int) -> bool:
        """
        Determine if we should move to the next question based on response and context.
        """
        # Keywords that indicate we should move to next question
        next_indicators = [
            "next question",
            "shall we move on",
            "let's continue",
            "thank you for sharing"
        ]
        
        # Check for explicit indicators in response
        if any(indicator in qa_response.lower() for indicator in next_indicators):
            return True
            
        # Check if we've reached max follow-ups
        if follow_up_count >= self.max_follow_ups:
            return True
            
        return False

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
            print(f"\nAsked: {current_question}")
            
            # Initialize follow-up counter for this question
            follow_up_count = 0

            while True:
                try:
                    # Get user response
                    print("\nListening for response...")
                    user_message = self.stt_agent.transcribe_audio()
                    if not user_message:  # Handle empty responses
                        print("No audio detected, trying again...")
                        continue
                    print(f"User said: {user_message}")

                    # Get next question for context
                    next_question = self.get_question(self.current_question_index + 1)

                    # Generate response using QA agent
                    qa_response = self.qa_agent.generate_response(
                        user_message,
                        conversation_history,
                        next_question
                    )
                    print(f"AI response: {qa_response}")

                    # Update conversation history before checking for next question
                    conversation_history.append({
                        "user": user_message,
                        "bench": qa_response
                    })

                    # Speak the response
                    self.tts_agent.text_to_speech(qa_response)
                    
                    # Increment follow-up counter
                    follow_up_count += 1

                    # Check if we should move to next question
                    if self.should_move_to_next_question(qa_response, follow_up_count):
                        print(f"Moving to next question (follow-ups: {follow_up_count})")
                        self.current_question_index += 1
                        break

                except Exception as e:
                    print(f"Error during conversation: {e}")
                    error_message = "I'm having trouble understanding. Could you please repeat that?"
                    self.tts_agent.text_to_speech(error_message)
                    # Don't increment follow_up_count for error cases

                # Add small pause between interactions
                time.sleep(1)

        print("\nQuestionnaire completed!")
from typing import List, Dict
from pathlib import Path
import requests
from datetime import datetime


class ManagerAgent:
    def __init__(self, llm_agent, stt_agent, tts_agent, api_base_url, bench_id):

        self.llm_agent = llm_agent
        self.stt_agent = stt_agent
        self.tts_agent = tts_agent

        self.api_base_url = api_base_url
        self.max_follow_ups = 2
        self.conversation_id = None
        self.bench_id = bench_id
        self.current_question_index = 0

        self.questions = []
        self.headers = {
            "Content-Type": "application/json"
        }


    # Post Conversation
    def create_conversation(self) -> None:
        """Initialize a new conversation by sending a POST request."""
        url = f"{self.api_base_url}/conversations"

        payload = {
            "startDatetime": datetime.now().isoformat() + "Z",
            "bench_id": self.bench_id,
        }
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code == 200:
            self.conversation_id = response.json()["id"]
            print(f"Conversation started. ID: {self.conversation_id}")
        else:
            raise Exception(f"Failed to create conversation: {response.text}")

    # Put Conversation
    def end_conversation(self) -> None:
        """Finalize the conversation by sending a PUT request with the end time."""
        if not self.conversation_id:
            raise Exception("No active conversation to end.")

        url = f"{self.api_base_url}/conversations/{self.conversation_id}"
        payload = {
            "endTime": datetime.now().isoformat() + "Z",  # Current UTC time in ISO 8601 format
            "summary": None,  # Optionally, you can update this field
            "sentiment": None,  # Optionally, update sentiment analysis if available
        }
        response = requests.put(url, headers=self.headers, json=payload)
        if response.status_code == 200:
            print(f"Conversation {self.conversation_id} successfully updated with end time.")
        else:
            raise Exception(f"Failed to update conversation: {response.text}")
        
    # Get Questionnaire
    def fetch_questions(self) -> None:
        """Fetch questions for the questionnaire."""
        url = f"{self.api_base_url}/questions"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            # Filter out only active questions

            all_questions = response.json()

            # Filter only active questions and sort them based on `isActive`

            self.questions = sorted(
                filter(lambda q: q.get('isActive', False), all_questions),
                key=lambda q: q['isActive'],
                reverse=True  # Ensures active questions are at the top
            )
            print(f"Fetched {len(self.questions)} active questions.")
        else:
            raise Exception(f"Failed to fetch questions: {response.text}")
        
    def get_question_by_id(self, question_id: int) -> Dict:
        """Retrieve a question by its ID."""
        for question in self.questions:
            if question['id'] == question_id:
                return question
        return None

    def get_question_by_index(self, index: int) -> Dict:
        """Retrieve a question by index."""
        if 0 <= index < len(self.questions):
            return self.questions[index]
        return None

    # Post Answers
    def submit_answer(self, question_id: int, user_response: str) -> None:
        """Submit a user's response for a specific question."""
        url = f"{self.api_base_url}/answers"
        payload = {
            "conversation_id": self.conversation_id,
            "question_id": question_id,
            "answer_text": user_response,
        }
        response = requests.post(url, headers=self.headers, json=payload )
        if response.status_code == 200:
            print("Response submitted successfully.")
        else:
            raise Exception(f"Failed to submit response: {response.text}")

    def run(self) -> None:
        """Execute the AI-driven questionnaire loop."""
        conversation_history: List[Dict] = []
    
        # Start a new conversation
        self.create_conversation()
    
        # Fetch questions
        self.fetch_questions()

        # Prompt variables
        next_question = None
        follow_up_count = 0
        prompt = ""
    
        # Add tracking for concatenated responses
        current_question_responses = []

        current_question_index = self.current_question_index

        # Add counter for unsuccessful listening attempts
        silent_attempts = 0
        MAX_SILENT_ATTEMPTS = 5

        while current_question_index < len(self.questions):
            current_question = self.get_question_by_index(current_question_index)
            if not current_question:
                print("Questionnaire is complete")
                return
    
            # Ask the first question
            self.tts_agent.text_to_speech(current_question['text'])
            conversation_history.append({"bank": current_question['text']})
            current_question_id = current_question['id']
            print(f"\nAI: {current_question['text']}")

            while True:
                try:
                    # Listen to the user
                    print("\nListening...")
                    user_message = self.stt_agent.transcribe_audio()
                    
                    # Check for silence/no response
                    if not user_message:
                        silent_attempts += 1
                        print(f"Geen reactie gedetecteerd. Poging {silent_attempts} van {MAX_SILENT_ATTEMPTS}")
                    
                        if silent_attempts >= MAX_SILENT_ATTEMPTS:
                            print("Maximaal aantal stille pogingen bereikt. Gesprek wordt beëindigd.")
                            goodbye_message = "Ik heb al een tijdje geen reactie gehoord. Bedankt voor je tijd. Fijne dag verder!"
                            self.tts_agent.text_to_speech(goodbye_message)
                            self.end_conversation()
                            return
                        continue
                
                    # Reset silent attempts counter when user responds
                    silent_attempts = 0
                    print(f"User said: {user_message}")
                
                
                    # Evaluate the response
                    is_response_complete = self.llm_agent.evaluate_response(
                        user_message,
                        conversation_history,
                        current_question,
                    )
                    print(is_response_complete)

                    # Check if the user wants to end the conversation
                    if is_response_complete == "Einde":
                        qa_response = """Bedankt voor het delen van je gedachten! Jouw feedback zal helpen om onze stad beter te maken. Nog een geweldige dag verder!"""
                        print(f"AI: {qa_response}")
                        self.tts_agent.text_to_speech(qa_response)
                        self.end_conversation()
                        return

                    # A detailed question can be asked max 2 times
                    if follow_up_count >= self.max_follow_ups:
                        print("De vraag is twee keer in detail gesteld, dus we gaan verder naar de volgende.")
                        is_response_complete = "Ja"

                    # Work only with topic related questions
                    if is_response_complete != "Off":

                        if is_response_complete == "Nee":
                            # Store response in detailed responses
                            current_question_responses.append(user_message)

                            prompt = "1. Genereer een verduidelijkende vraag om vriendelijk meer details te verkrijgen of gewoon een vraag om feedback van de gebruiker over de stad te verzamelen. De vragen moeten open-ended zijn."
                            print("User response is on-topic, but incomplete. Asking for more details.")
                            next_question = None
                            follow_up_count += 1

                        # If the user response is complete or we've reached max follow-ups
                        elif is_response_complete == "Ja":
                            # Concatenate all responses for this question
                            combined_response = " ".join(current_question_responses)

                            final_response = f"{combined_response} {user_message}"
                        
                            # Submit the concatenated response
                            self.submit_answer(current_question_id, final_response)
                        
                            prompt = "1. Reageer vriendelijk op hun antwoorden. Erken dat we doorgaan naar de volgende vraag in onze vragenlijst. 3. Stel een aangeleverde vervolgvraag."
                            print("We gaan verder naar de volgende vraag met de samengevoegde reactie:", final_response)
                            next_question = self.get_question_by_index(current_question_index + 1)['text']
                            current_question_index += 1
                            follow_up_count = 0
                            current_question_responses = []  # Reset for next question
                        
                    else:
                        prompt = "Behandel off-topic reacties van de gebruiker door te bevestigen wat er is gehoord en het gesprek op een beleefde manier terug te leiden naar de vragenlijst. 1. Erkenning van de input van de gebruiker. Als de gebruiker een off-topic vraag stelt, beantwoord deze dan niet. 2. Een vriendelijke opmerking dat de focus ligt op de onderwerpen van de vragenlijst. 3. Stel de vervolgvraag om het gesprek soepel weer op koers te brengen."
                        print("User response is off-topic. Asking the same question")
                        next_question = self.get_question_by_id(current_question_id)['text']

                    qa_response = self.llm_agent.generate_response(
                        prompt,
                        user_message,
                        conversation_history,
                        follow_up_question=next_question
                    )

                    print(f"AI response: {qa_response}")
                    self.tts_agent.text_to_speech(qa_response)
                    self.end_conversation()

                    # Update conversation history
                    conversation_history.append({
                        "user": user_message,
                        "bank": qa_response
                    })

                except Exception as e:
                    print(f"Fout tijdens het gesprek: {e}")
                    self.tts_agent.text_to_speech("Ik heb moeite met begrijpen. Kun je dat alstublieft herhalen?")

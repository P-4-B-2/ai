from typing import List, Dict, Optional
import json
from pathlib import Path
import requests
from datetime import datetime
import os

class ManagerAgent:
    def __init__(self, llm_agent, stt_agent, tts_agent, api_base_url, bench_id):

        self.llm_agent = llm_agent
        self.stt_agent = stt_agent
        self.tts_agent = tts_agent

        self.api_base_url = api_base_url
        self.current_question_index = 0
        self.max_follow_ups = 2
        self.bench_id = bench_id
        self.conversation_id = None
        self.questions = []
        self.headers = {
            "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjgxYjUyMjFlN2E1ZGUwZTVhZjQ5N2UzNzVhNzRiMDZkODJiYTc4OGIiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vZnJhbmstZGUtcHJhdGVuZGUtYmFuayIsImF1ZCI6ImZyYW5rLWRlLXByYXRlbmRlLWJhbmsiLCJhdXRoX3RpbWUiOjE3Mzc1NDMyOTIsInVzZXJfaWQiOiJuZUtjUndaN2NBTlVrVjZIaTl5bmVJallvQ3MyIiwic3ViIjoibmVLY1J3WjdjQU5Va1Y2SGk5eW5lSWpZb0NzMiIsImlhdCI6MTczNzU0MzI5MiwiZXhwIjoxNzM3NTQ2ODkyLCJlbWFpbCI6ImpvaG4uZG9lQGV4YW1wbGUuY29tIiwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7ImVtYWlsIjpbImpvaG4uZG9lQGV4YW1wbGUuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoicGFzc3dvcmQifX0.lVBQiaIwbR2sDSTn6kQm18nIp6GXey8D_f8qZn5wFg-RyRbZVtCJEfuW9FJWABTR0PpnLAMCJVpFTDe4IRWtWd8arx9GWEQoNukmgssySZLKIItZJ1SQSGnaJKERpxL-w2FNodhFQIWP0IgEUvzQbY9tS7_MYYI3m8VIJ1tN_ybPbpP_4UvwzGeVmvfVo4eFW2il4ozQBjNXnqwPMjS8GtCMbFcXqQwEXY_BBPWjfnfk8r0AxKApdqb_Tc_h49AIpXbVbOdO_p9pd4uXiB5wg_NVkUmJcK59-0tZk5HMY99xGV7kXaD8uk0VO8Cm5JjqkNUvD8n2JZAbGJePkkaIyw",
            "Content-Type": "application/json",
        }



    # Post Conversation
    # def create_conversation(self) -> None:
    #     """Initialize a new conversation by sending a POST request."""
    #     url = f"{self.api_base_url}/conversations"
    #     payload = {
    #         "startDatetime": datetime.now().isoformat() + "Z",
    #         "endDatetime": None,
    #         "sentiment": None,
    #         "summary": None,
    #         "benchId": self.bench_id,
    #     }
    #     response = requests.post(url, headers=self.headers, json=payload)
    #     if response.status_code == 201:
    #         self.conversation_id = response.json()["conversationId"]
    #         print(f"Conversation started. ID: {self.conversation_id}")
    #     else:
    #         raise Exception(f"Failed to create conversation: {response.text}")


    def create_conversation(self) -> None:
        """Initialize a new conversation by sending a POST request."""
        url = f"{self.api_base_url}/conversations"
        payload = {
            "id": 0,
            "startDatetime": datetime.now().isoformat() + "Z",
            "endDatetime": datetime.now().isoformat() + "Z",
            "sentiment": 0,
            "summary": "string",
            "benchId": self.bench_id,
        }
        response = requests.post(url, headers=self.headers, json=payload)
        print(url, self.headers, payload)
        if response.status_code == 201:
            print(f"Conversation started.")
        elif response.status_code==500:
            print(401)
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
            self.questions = sorted(
                response.json(),
                key=lambda q: q["orderNumber"]
            )
            print(f"Fetched {len(self.questions)} questions.")
        else:
            raise Exception(f"Failed to fetch questions: {response.text}")
        
    # def get_question(self, index: int) -> Dict:
    #     """Retrieve a question by index."""
    #     if 0 <= index < len(self.questions):
    #         return self.questions[index]
    #     return None
    
    def get_question(self, index: int) -> Optional[str]:
        """Get question at specified index."""
        if 0 <= index < len(self.questions):
            return self.questions[index]["text"]
        return None
    
    # Post Answers
    def submit_answer(self, question_id: int, user_response: str) -> None:
        """Submit a user's response for a specific question."""
        url = f"{self.api_base_url}/answers"
        payload = {
            "response": user_response,
            "conversationId": self.conversation_id,
            "questionId": question_id,
        }
        response = requests.post(url, headers=self.headers,json=payload)
        if response.status_code == 201:
            print("Response submitted successfully.")
        else:
            raise Exception(f"Failed to submit response: {response.text}")
        

    def run(self) -> None:
        """Execute the AI-driven questionnaire loop."""
        conversation_history: List[Dict] = []
    
        # Start a new conversation
        # self.create_conversation()
    
        # Fetch questions
        self.fetch_questions()

        # Prompt variables
        next_question = None
        follow_up_count = 0
        prompt = ""
    
        # Add tracking for concatenated responses
        current_question_responses = []


        # Add counter for unsuccessful listening attempts
        silent_attempts = 0
        MAX_SILENT_ATTEMPTS = 5
    
        while self.current_question_index < len(self.questions):
            current_question = self.get_question(self.current_question_index)
            if not current_question:
                break

            # Ask the first question
            self.tts_agent.text_to_speech(current_question)
            conversation_history.append({"bench": current_question})
            print(f"\nAI: {current_question}")

            while True:
                try:
                    # Listen to the user
                    print("\nListening...")
                    user_message = self.stt_agent.transcribe_audio()
                    if not user_message:
                        self.tts_agent.text_to_speech("I'm having trouble understanding. Could you please repeat that?")
                        continue

                    # Check for silence/no response
                    if not user_message:
                        silent_attempts += 1
                        print(f"No response detected. Attempt {silent_attempts} of {MAX_SILENT_ATTEMPTS}")
                    
                        if silent_attempts >= MAX_SILENT_ATTEMPTS:
                            print("Maximum silent attempts reached. Ending conversation.")
                            goodbye_message = "I haven't heard a response in a while. Thank you for your time. Have a great day!"
                            self.tts_agent.text_to_speech(goodbye_message)
                            conversation_history.append({
                                "bench": goodbye_message
                            })
                            self.end_conversation()
                            return
                        continue
                
                    # Reset silent attempts counter when user responds
                    silent_attempts = 0
                    print(f"User said: {user_message}")
                
                    # Store the response for potential concatenation
                    if user_message:
                        current_question_responses.append(user_message)
                
                    # Evaluate the response
                    is_response_complete = self.llm_agent.evaluate_response(
                        user_message,
                        conversation_history,
                        current_question,
                    )
                    print(is_response_complete)

                    # Check if the user wants to end the conversation
                    if is_response_complete == "End":
                        qa_response = """Thank you for sharing your thoughts with me! Your feedback will help make our city better. Have a wonderful rest of your day!"""
                        print(f"AI: {qa_response}")
                        conversation_history.append({
                            "user": user_message,
                            "bench": qa_response
                        })
                        self.tts_agent.text_to_speech(qa_response)
                        self.end_conversation()
                        return

                    # A detailed question can be asked max 2 times
                    if follow_up_count >= self.max_follow_ups:
                        print("The question was asked in details twice, so moving to the next one.")
                        is_response_complete = "Yes"

                    # Work only with topic related questions
                    if is_response_complete != "Off":
                        # If the user response is complete or we've reached max follow-ups
                        if is_response_complete == "Yes":
                            # Concatenate all responses for this question
                            combined_response = " ".join(current_question_responses)
                        
                            # Submit the concatenated response
                            self.submit_answer(self.current_question_index, combined_response)
                        
                            prompt = "1. Start with a warm greeting and explain your purpose. 2. Respond kindly to their answers. Acknowledge that we are moving to the next question of our questionnaire. 3. Ask a provided follow-up question."
                            print("Moving to next question with concatenated response:", combined_response)
                            next_question = self.get_question(self.current_question_index + 1)
                            self.current_question_index += 1
                            follow_up_count = 0
                            current_question_responses = []  # Reset for next question

                        elif is_response_complete == "No":
                            prompt = "1. Start with a warm greeting and explain your purpose. 2. Generate a clarifying question to kindly obtain more details or just a question to gather a user feedback about the city. The questions should be open-ended."
                            print("User response is on-topic, but incomplete. Asking for more details.")
                            next_question = None
                            follow_up_count += 1
                    else:
                        prompt = "Handle off-topic user responses by confirming what was heard and politely redirecting the conversation back to the questionnaire. 1. Acknowledgment of the user's input. If the user asks off-topic question do not answer that. 2. A kind statement that the focus is on the questionnaire topics. 3. Ask the follow-up question to smoothly guide the conversation back on track."
                        print("User response is off-topic. Asking the same question")
                        next_question = self.get_question(self.current_question_index)
                        follow_up_count += 1

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
                        "bench": qa_response
                    })

                except Exception as e:
                    print(f"Error during conversation: {e}")
                    self.tts_agent.text_to_speech(
                        "I'm having trouble understanding. Could you please repeat that?"
                    )
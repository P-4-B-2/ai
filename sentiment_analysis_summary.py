from typing import List, Dict, Tuple
import re
import groq
import requests
import os
from datetime import datetime

class SSAgent:
        def __init__(self):
            """Initialize the SS Agent with Groq client."""
            self.client = groq.Client(api_key=os.environ.get("GROQ_API_KEY"))
            self.model = "llama-3.1-8b-instant" 
            self.last_conversation = None
            self.conversation_id = None
            self.answers = None
            self.questions = None
            self.conversation_history=None
            self.api_base_url = "https://frankdepratendebank.azurewebsites.net/api/"
            self.headers = {
            "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjBjYmJiZDI2NjNhY2U4OTU4YTFhOTY4ZmZjNDQxN2U4MDEyYmVmYmUiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vZnJhbmstZGUtcHJhdGVuZGUtYmFuayIsImF1ZCI6ImZyYW5rLWRlLXByYXRlbmRlLWJhbmsiLCJhdXRoX3RpbWUiOjE3Mzk1MTc3NzgsInVzZXJfaWQiOiJuZUtjUndaN2NBTlVrVjZIaTl5bmVJallvQ3MyIiwic3ViIjoibmVLY1J3WjdjQU5Va1Y2SGk5eW5lSWpZb0NzMiIsImlhdCI6MTczOTUxNzc3OCwiZXhwIjoxNzM5NTIxMzc4LCJlbWFpbCI6ImpvaG4uZG9lQGV4YW1wbGUuY29tIiwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7ImVtYWlsIjpbImpvaG4uZG9lQGV4YW1wbGUuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoicGFzc3dvcmQifX0.Fr-bmpuWORccPX1XFnNvj_mnGqaKarUjrWbyB4d1m-pt0RjX_wIL95pgGVdlQEjSVfj4EyuFWBgyXMqDM4MuYkBszE5NugxiOB5yw4Wcnh3v2g0CIA1c4vil9VVlk0z4l3sCttcILRUAeLazrIqUBxk9B6l6ZMFD6wkVKTK6DUZ9ZEa1mzRAk-2L_UlJv5pcwDz1re2bfIZAkz2W8whsrWqA8lKsjySTD5LZtBEYYUzu_XtJZioyPSTt59r8DA1uIdvXfJnE4RtIJXsFWfuthTv4ogjN5aeipR5TI-OIRq2kOSMemsbLeydRaoaPwtWAl5FNGRKBNiaBV4CMtkhFLA",
            "Content-Type": "application/json",
        }

        # Get Bearer Token
        def fetch_bearer_token(self) -> None:
            """Fetch the last conversation for analysis."""
            url = f"{self.api_base_url}token/generate"

            payload = {
                "ApiKey": os.environ.get("API_KEY")
            }

            response = requests.post(url, headers=self.headers, json=payload)

            if response.status_code == 200:
                token = response.json()
                if token:
                    self.headers = {
                    "Authorization": "Bearer " + token['token'],
                    "Content-Type": "application/json",
                    }
                    print(self.headers)
                    print(f"Fetched the token successfully")
                else:
                    print("No response.")
            else:
                raise Exception(f"Failed to fetch token: {response.status_code}")

        # Get Conversations  
        def fetch_last_conversation(self) -> None:
            """Fetch the last conversation for analysis."""
            url = f"{self.api_base_url}/conversations"
            response = requests.get(url, headers=self.headers)

            
            if response.status_code == 200:
                conversations = response.json()
                conversations_with_end_datetime = [
                convo for convo in conversations if convo['endDatetime'] is not None
                ]
                if conversations_with_end_datetime:
                    # Sort conversations by 'end_datetime' in descending order and get the most recent one
                    conversations_with_end_datetime.sort(
                        key=lambda x: datetime.fromisoformat(x['endDatetime']), reverse=True
                    )
                    self.last_conversation = conversations_with_end_datetime[0]  # Get the most recent conversation
                    self.conversation_id = self.last_conversation['id']
                    print(f"Fetched last conversation: {self.last_conversation}")
                else:
                    print("No conversations with a valid 'end_datetime' found.")
            else:
                raise Exception(f"Failed to fetch conversations: {response.status_code}")
    
       # Get Questions
        def fetch_questions(self) -> None:
            """Fetch all questions from the last conversation for analysis."""

            url = f"{self.api_base_url}questions"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                self.questions = response.json()
                print(f"Fetched {len(self.questions)} questions")
            else:
                raise Exception(f"Failed to fetch questions: {response.text}")
            
        # Get Answers
        def fetch_answers(self) -> None:
            """Fetch all answers from the last conversation for analysis."""
            if not hasattr(self, "conversation_id") or self.conversation_id is None:
                print("No conversation ID found. Please fetch the last conversation first.")
                return

            url = f"{self.api_base_url}answers/conversation/{self.conversation_id}"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                self.answers = response.json()
                print(f"Fetched {len(self.answers)} answers for conversation {self.conversation_id}")
            else:
                raise Exception(f"Failed to fetch answers: {response.text}")
            
        # Put Conversation
        def update_conversation(self) -> None:
            """Finalize the conversation by sending a PUT request with the end time."""

            sentiment_score, conversation_summary = self.analyze_sentiment_and_summarize(self.conversation_history)

            url = f"{self.api_base_url}conversations/{self.conversation_id}"
            payload = {
                "id":self.last_conversation['id'],
                "startDatetime": self.last_conversation['startDatetime'],
                "endDatetime": self.last_conversation['endDatetime'],
                "sentiment": int(sentiment_score),
                "summary": conversation_summary,
                "benchId": self.last_conversation['benchId']
            }

    
            try:
                response = requests.put(url, headers=self.headers, json=payload)
                if response.status_code == 204:
                    print(f"Conversation {self.conversation_id} successfully updated.")
                else:
                    raise Exception(f"Failed to update conversation {response.content}")
            except Exception as e:
                print(f"Error finalizing conversation: {str(e)}")

        # Put Answer
        def update_answer_with_keywords(self, answer, keywords: list) -> None:
            """Update an existing answer with a new response and attach extracted keywords."""
            url = f"{self.api_base_url}answers/{answer['id']}"
    
            # If the keywords list is empty or contains ['[]'], we set it to None
            if not keywords or keywords == ['[]']:
                keywords = None
            # Prepare the payload to update the response
            payload = {
                
                "id":answer['id'],
                "conversationId": answer['conversationId'],
                "questionId": answer['questionId'],
                "response": answer['response'],
                "keywords": keywords  # Attach keywords to the response
            }
            print(payload)
    
            # Send the PUT request with the updated data
            response = requests.put(url, json=payload, headers=self.headers)

            if response.status_code == 204:
                print(f"Successfully updated answer {answer['id']} with new response and keywords.")
            else:
                raise Exception(f"Failed to update answer {answer['id']}: {response.text}")
           
        def create_conversation_history(self) -> None:
                """
        Create a conversation history by matching questions and answers for a specific conversation.
        Format the history to be compatible with the sentiment analysis function.
        
        Args:
            conversation_id: The ID of the conversation to fetch history for
            questions: List of all questions
            answers: List of all answers
            
        Returns:
            List of dictionaries containing messages in the format expected by the sentiment analyzer
                """
                # Fetch all answers for the conversation
                self.fetch_answers()
                answers = self.answers
        
                # Fetch all questions for the conversation
                self.fetch_questions()
                questions = self.questions
        
                # Create a lookup dictionary for questions using their IDs
                question_lookup = {q['id']: q for q in questions}
        
                # Create conversation history directly from answers
                conversation_history = []
                for answer in answers:
                    # Get the corresponding question using the questionId
                    question = question_lookup.get(answer['questionId'])
            
                    if question:
                        conversation_history.append({
                            "bank": question['text'],
                            "user": answer['response']
                        })

                        
                self.conversation_history = conversation_history
        
        def analyze_sentiment_and_summarize(self, 
                                   conversation_history: List[Dict[str, str]], 
                                   ) -> Tuple[int, str]:
            """
            Analyzes the sentiment of the conversation and generates a summary in a single function.
    
            Args:
                conversation_history: List of previous messages exchanged.
                sentiment_max_tokens: Maximum number of tokens for sentiment analysis.
                summary_max_tokens: Maximum number of tokens for the summary.
                temperature: Sampling temperature.
                top_p: Top-p sampling value.

            Returns:
                Tuple[int, str]: A tuple containing the positivity percentage (1-100) and a concise summary of the conversation.
            """
            if not conversation_history:
                return 50, "No conversation history available."  # Neutral sentiment and default message

            system_prompt = """
        Je bent een AI-assistent die is belast met het analyseren van gesprekken. Voer de volgende taken uit:
        1. Geef een positiviteitsscore tussen 1 en 100 op basis van het sentiment van het gesprek.
        2. Genereer een korte en coherente samenvatting van de reacties van de gebruiker tot nu toe.

        Formatteer je antwoord als volgt:
        SENTIMENT: <score>
        SAMENVATTING: <tekst>
        """
            

    
            # Construct messages
            messages = [{"role": "system", "content": system_prompt}]
            for msg in conversation_history: 
                if "bank" in msg:
                    messages.append({"role": "assistant", "content": msg["bank"]})
                if "user" in msg:
                    messages.append({"role": "user", "content": msg["user"]})


            chat_completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.4,
                    max_tokens=150,  # Allocate tokens
                    top_p=0.9,
                    stream=False
                )


            try:
                response = chat_completion.choices[0].message.content.strip()
        
                # Extract sentiment score and summary
                sentiment_match = re.search(r"SENTIMENT: (\d+)", response)
                summary_match = re.search(r"SAMENVATTING: (.*)", response, re.DOTALL)
        
                score = int(sentiment_match.group(1)) if sentiment_match else 50
                summary = summary_match.group(1).strip() if summary_match else ""
        
                return max(1, min(score, 100)), summary
            
            except KeyError as e:
                raise Exception(f"Error in processing response: {e}")
    
        def extract_keywords(self, answer: str):
            """
            Extracts relevant keywords from a given answer using Groq LLM.
            Returns a list of extracted keywords.
            """
            prompt = f"""
            Je bent een AI die relevante trefwoorden extraheert uit gebruikersreacties om feedback over een stad te classificeren.
Extraheer **alle relevante trefwoorden** uit de reactie op basis van de volgende categorieën:

- Openbaar Vervoer (bus, metro, trein, verkeer, parkeren)
- Toerisme (museum, bezienswaardigheden, monumenten, hotels)
- Infrastructuur (wegen, bruggen, bouw, netheid)
- Veiligheid (criminaliteit, politie, verlichting, ongelukken)
...

### Gebruikersreactie:
"{answer}"

Geef de geëxtraheerde trefwoorden terug als een lijst, gescheiden door komma's: [trefwoord1, trefwoord2, ...]. 

**Voorbeeld:**  
Gebruikersreactie: "Er was veel verkeer en ik had moeite om een parkeerplaats te vinden."  
Geëxtraheerde trefwoorden: [verkeer, parkeren]
            """

            # Sending the request to the API
            chat_completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": "Je bent een assistent voor trefwoordextractie."},
                        {"role": "user", "content": prompt}],
                temperature=0.0
            )
            extracted_keywords_list = None
            try:
                # Extract keywords from the response, assuming the content is a comma-separated list
                response_content = chat_completion.choices[0].message.content.strip()
                if "Geëxtraheerde trefwoorden:" in response_content:
                    # Extract everything after "Geëxtraheerde trefwoorden:"
                    response_content = response_content.split("Geëxtraheerde trefwoorden:")[1].strip()

                    # If the response is "None", return None
                    if response_content.lower() == "none":
                        extracted_keywords_list = None
                    else:
                        # Otherwise, split the keywords by commas and strip extra spaces
                        extracted_keywords_list = [keyword.strip() for keyword in response_content.split(",")]

                return extracted_keywords_list
            
            except KeyError as e:
                raise Exception(f"Error in processing response: {e}")

        def run(self) -> None:
            """Run the SS Agent to process the conversation and provide analysis."""
            try:

                # #Fetch bearer token

                # self.fetch_bearer_token()
                # Fetch the last conversation
                self.fetch_last_conversation()

                # Create conversation history
                self.create_conversation_history()

                # Update the conversation with sentiment score and summary
                self.update_conversation()


                answers = self.answers

                # Iterate over the answers and extract keywords
                for answer in answers:
                    if answer:  # Ensure the answer is not empty
                        # Extract keywords from the answer
                        keywords = self.extract_keywords(answer['response'])

                        # Update the conversation in the database with the extracted keywords
                        self.update_answer_with_keywords(answer, keywords)

            except Exception as e:
                print(f"Error in running SS Agent: {str(e)}")



if __name__ == "__main__":

    ss = SSAgent()

    ss.run()
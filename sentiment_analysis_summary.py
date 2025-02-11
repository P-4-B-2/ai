from typing import List, Dict, Tuple
import re
import groq
import requests
import os

class SSAgent:
        def __init__(self):
            """Initialize the SS Agent with Groq client."""
            self.client = groq.Client(api_key=os.environ.get("GROQ_API_KEY"))
            self.model = "llama-3.3-70b-versatile" 
            self.conversation_id = None
            self.last_conversation = None

        # Get Conversations  
        def fetch_last_conversation(self) -> None:
            """Fetch the last conversation for analysis."""
            url = f"{self.api_base_url}/conversations"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                conversations = sorted(
                    response.json(),
                    key=lambda q: q["orderNumber"]
                )
                if conversations:
                    self.last_conversation = conversations[-1]  # Get the last conversation
                    self.conversation_id = self.last_conversation['id']
                    print(f"Fetched last conversation: {self.last_conversation}")
                else:
                    print("No conversations found.")
            else:
                raise Exception(f"Failed to fetch conversations: {response.text}")

        # Get Answers
        def fetch_answers(self) -> None:
            """Fetch all answers from the last conversation for analysis."""
            if not hasattr(self, "conversation_id") or self.conversation_id is None:
                print("No conversation ID found. Please fetch the last conversation first.")
                return

            url = f"{self.api_base_url}/answers?conversation_id={self.conversation_id}"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                self.answers = response.json()
                print(f"Fetched {len(self.answers)} answers for conversation {self.conversation_id}")
            else:
                raise Exception(f"Failed to fetch answers: {response.text}")
            
        # Put Conversation
        def update_conversation(self) -> None:
            """Finalize the conversation by sending a PUT request with the end time."""
            if not self.conversation_id:
                raise Exception("No active conversation to end.")

            sentiment_score, conversation_summary = self.analyze_sentiment_and_summarize(self.conversation_history)

            url = f"{self.api_base_url}/conversations/{self.conversation_id}"
            payload = {
                "summary": conversation_summary,
                "sentiment": sentiment_score,
            }
    
            try:
                response = requests.put(url, headers=self.headers, json=payload)
                if response.status_code == 200:
                    print(f"Conversation {self.conversation_id} successfully updated with end time.")
                else:
                    raise Exception(f"Failed to update conversation: {response.text}")
            except Exception as e:
                print(f"Error finalizing conversation: {str(e)}")

        # Put Answer
        def update_answer_with_keywords(self, answer_id: int, keywords: list) -> None:
            """Update an existing answer with a new response and attach extracted keywords."""
            url = f"{self.api_base_url}/answers/{answer_id}"
    
            # Prepare the payload to update the response
            payload = {
                "keywords": keywords  # Attach keywords to the response
            }
    
            # Send the PUT request with the updated data
            response = requests.put(url, json=payload, headers=self.headers)

            if response.status_code == 200:
                print(f"Successfully updated answer {answer_id} with new response and keywords.")
            else:
                raise Exception(f"Failed to update answer {answer_id}: {response.text}")

            

        def analyze_sentiment_and_summarize(self, 
                                   conversation_history: List[Dict[str, str]], 
                                   sentiment_max_tokens: int = 10, 
                                   summary_max_tokens: int = 50, 
                                   temperature: float = 0.4, 
                                   top_p: float = 0.9) -> Tuple[int, str]:
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
                if "user" in msg:
                    messages.append({"role": "user", "content": msg["user"]})
                if "bank" in msg:
                    messages.append({"role": "bank", "content": msg["bank"]})
    
            try:
                chat_completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=sentiment_max_tokens + summary_max_tokens,  # Allocate tokens
                    top_p=top_p,
                    stream=False
                )
                response = chat_completion.choices[0].message.content.strip()
        
                # Extract sentiment score and summary
                sentiment_match = re.search(r"SENTIMENT: (\d+)", response)
                summary_match = re.search(r"SAMENVATTING: (.*)", response, re.DOTALL)
        
                score = int(sentiment_match.group(1)) if sentiment_match else 50
                summary = summary_match.group(1).strip() if summary_match else "Failed to generate summary."
        
                return max(1, min(score, 100)), summary
            except Exception as e:
                return 50, "Failed to generate summary."
    
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
            - Overig (als geen van de bovenstaande van toepassing is)

            ### Gebruikersreactie:
            "{answer}"

            Geef de geëxtraheerde trefwoorden terug als een lijst, gescheiden door komma's: [trefwoord1, trefwoord2, ...]
            """

            # Sending the request to the API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": "Je bent een assistent voor trefwoordextractie."},
                        {"role": "user", "content": prompt}],
                temperature=0.2
            )

            # Assuming the response content is in response.choices[0].message.content
            try:
                # Extract keywords from the response, assuming the content is a comma-separated list
                response_content = response['choices'][0]['message']['content'].strip()
                if response_content.startswith("Trefwoord:"):
                    # If the response includes "Trefwoord:", remove it
                    response_content = response_content.replace("Trefwoord:", "").strip()
        
                # Split the response into individual keywords
                extracted_keywords_list = [keyword.strip() for keyword in response_content.split(",")]
        
                return extracted_keywords_list
            
            except KeyError as e:
                raise Exception(f"Error in processing response: {e}")



        def run(self) -> None:
            """Run the SS Agent to process the conversation and provide analysis."""
            try:

                answers =[]
                
                # Fetch the last conversation
                self.fetch_last_conversation()

                # Update the conversation with sentiment score and summary
                self.update_conversation()

                # Fetch all answers for the conversation using get_answer method
                answers = self.get_answers(self.conversation_id)

                # Iterate over the answers and extract keywords
                for answer in answers:
                    if answer:  # Ensure the answer is not empty
                        # Extract keywords from the answer
                        keywords = self.extract_keywords(answer['response'])

                        # Update the conversation in the database with the extracted keywords
                        self.update_answer_with_keywords(answer['id'], keywords)

            except Exception as e:
                print(f"Error in running SS Agent: {str(e)}")


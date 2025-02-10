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
                if "assistant" in msg:
                    messages.append({"role": "assistant", "content": msg["assistant"]})
    
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
    

        def run(self) -> None:
            """Run the SS Agent to process the conversation and provide analysis."""
            try:
                # Fetch the last conversation
                self.fetch_last_conversation()

                # Update the conversation with sentiment score and summary
                self.update_conversation()

            except Exception as e:
                print(f"Error in running SS Agent: {str(e)}")


from typing import List, Dict, Tuple
import re
import requests



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
You are an AI assistant tasked with analyzing conversations. Perform the following tasks:
1. Provide a positivity score between 1 and 100 based on the sentiment of the conversation.
2. Generate a brief and coherent summary of the user's responses so far.

Format your response as follows:
SENTIMENT: <score>
SUMMARY: <text>
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
        summary_match = re.search(r"SUMMARY: (.*)", response, re.DOTALL)
        
        score = int(sentiment_match.group(1)) if sentiment_match else 50
        summary = summary_match.group(1).strip() if summary_match else "Failed to generate summary."
        
        return max(1, min(score, 100)), summary
    except Exception as e:
        return 50, "Failed to generate summary."
    


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
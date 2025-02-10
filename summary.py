import os
from typing import List, Dict
import groq
from datetime import datetime



def analyze_sentiment(self, 
                      conversation_history: List[Dict[str, str]], 
                      max_tokens: int = 10, 
                      temperature: float = 0.3, 
                      top_p: float = 0.9) -> int:
    """
    Analyzes the sentiment of the conversation and returns a positivity score from 1 to 100.
    
    Args:
        conversation_history: List of previous messages exchanged.
        max_tokens: Maximum number of tokens in the response.
        temperature: Sampling temperature.
        top_p: Top-p sampling value.

    Returns:
        int: A positivity percentage (1-100) based on the sentiment of the conversation.
    """
    if not conversation_history:
        return 50  # Neutral default if no history

    sentiment_role = """
You are a sentiment analysis assistant. Your task is to analyze the overall sentiment of the user's responses 
based on the most recent conversation history.

Provide a positivity score between 1 and 100, where:
- 1 is extremely negative
- 50 is neutral
- 100 is extremely positive

Only return a single integer value representing the positivity score.
"""

    # Construct messages
    messages = [{"role": "system", "content": sentiment_role}]
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
            max_tokens=max_tokens,
            top_p=top_p,
            stream=False
        )
        score = chat_completion.choices[0].message.content.strip()

        # Convert score to integer, ensure it's within 1-100 range
        score = int(score)
        return max(1, min(score, 100))
    except Exception as e:
        return 50  # Default to neutral if error occurs


def create_summary(self, 
                   conversation_history: List[Dict[str, str]], 
                   max_tokens: int = 50, 
                   temperature: float = 0.5, 
                   top_p: float = 0.9) -> str:
    """
    Generates a summary of the conversation so far using Groq's chat completion API.
    
    Args:
        conversation_history: List of previous messages exchanged.
        max_tokens: Maximum number of tokens in the summary.
        temperature: Sampling temperature.
        top_p: Top-p sampling value.

    Returns:
        str: A concise summary of the conversation.
    """
    if not conversation_history:
        return "No conversation history available."

    summarizer_role = """
You are a summarization assistant. Your task is to generate a brief and coherent summary of the user's responses so far.

Consider the key points the user has mentioned and structure the summary in a clear and concise manner.
"""

    # Construct messages
    messages = [{"role": "system", "content": summarizer_role}]
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
            max_tokens=max_tokens,
            top_p=top_p,
            stream=False
        )
        summary = chat_completion.choices[0].message.content.strip()
        return summary
    except Exception as e:
        return "Failed to generate summary."



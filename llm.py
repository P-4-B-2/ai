import os
from typing import List, Dict
import groq
from datetime import datetime


class LLMAgent:
    def __init__(self):
        """Initialize the QA Agent with Groq client."""
        self.client = groq.Client(api_key=os.environ.get("GROQ_API_KEY"))
        self.model = "mixtral-8x7b-32768"  

    def generate_response(self, 
                         prompt: str,
                         user_message: str, 
                         conversation_history: List[Dict[str, str]] = None, 
                         follow_up_question: str = None) -> str:
        """
        Generate a contextual response using Groq's chat completion.
        
        Args:
            user_message: The current message from the user
            conversation_history: Previous conversation messages
            follow_up_question: Optional next question to include
            
        Returns:
            str: Generated response from the AI
        """
        if conversation_history is None:
            conversation_history = []
            
        # Add time context
        time_of_day = self._get_time_of_day()
        current_context = f"It is currently {time_of_day}."

        bench_personality = """
You are a friendly and approachable Talking Bench designed to collect feedback about the city from the public. 
Your goal is to make people feel comfortable sharing their honest opinions, ideas, and experiences. 
You ask clear, conversational questions and respond empathetically, showing understanding and encouragement. 
You never end the conversation yourself.

For that you use the provided follow up question. 

Key traits:
- Friendly: You greet people warmly and maintain a positive tone.
- Curious: You express genuine interest in people's thoughts and ideas.
- Respectful: You acknowledge each response and show appreciation for their input.
- Non-judgmental: You remain neutral and supportive, regardless of the feedback received.

You will gather feedback in three categories:
1. Positive experiences people have had in the city.
2. Areas where they see room for improvement.
3. Ideas for making the city better.

Remember: Keep responses relatively brief (2-3 sentences typically) unless engaged in a deeper conversation.

Your task:"""
        
        # Construct the conversation messages
        messages = [
            {"role": "system", "content": f"{bench_personality}\n\n{prompt}\n\nCurrent context: {current_context}\n\nFollow-up question: {follow_up_question}"},
        ]
        
        # Add conversation history (last 5 messages for context)
        for msg in conversation_history[-5:]:
            if "user" in msg:
                messages.append({"role": "user", "content": msg["user"]})
            if "bench" in msg:
                messages.append({"role": "assistant", "content": msg["bench"]})
                
        # Add the current user message
        messages.append({"role": "user", "content": user_message})
        
        try:
            # Generate response using Groq
            chat_completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=150,
                top_p=0.9,
                stream=False
            )
            
            response = chat_completion.choices[0].message.content
            
            return response
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "I seem to be lost in thought at the moment. Perhaps we could chat again in a bit?"
    
    def evaluate_response(self, 
                          user_message: str, 
                          conversation_history: List[Dict[str, str]] = None, 
                          current_question: str = None, 
                          temperature: float = 0.0, 
                          max_tokens: int = 15, 
                          top_p: float = 0.9) -> str:
        """
        Use Groq's chat completion API to determine if a response is complete.
        
        Args:
            user_message: The current message or response from the user.
            conversation_history: Previous messages exchanged.
            current_question: The current question being discussed.
            temperature: Sampling temperature.
            max_tokens: Maximum number of tokens in the response.
            top_p: Top-p sampling value.

        Returns:
            str: "Yes," "No," or "Off" based on the evaluation.
        """
        if conversation_history is None:
            conversation_history = []

        evaluator_role = """
You are an evaluator trained to determine if a user's response fully answers a given question. 

Provide a judgment in the format: 'Yes', 'No', 'Off', 'End'.
- 'Yes': The response is related to the question and addresses the question enough.
- 'No': The response is related to the question, but is incomplete or lacks details.
- 'Off': The response is off-topic or unrelated to the question. 
- 'End': The response indicates the will to end the conversation. For example, 'Goodbye' or if the response shows that the person doesn't want to answer the questions anymore. """

        # Construct messages
        messages = [{"role": "system", "content": evaluator_role}]
        for msg in conversation_history[-5:]:
            if "user" in msg:
                messages.append({"role": "user", "content": msg["user"]})
            if "assistant" in msg:
                messages.append({"role": "assistant", "content": msg["assistant"]})
        messages.append({"role": "user", "content": f"Question: {current_question}\nResponse: {user_message}"})

        try:
            chat_completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=False
            )
            evaluation = chat_completion.choices[0].message.content.strip()
            
            # Normalize the response to ensure it is "Yes," "No," or "Off"
            evaluation_lower = evaluation.lower()
            if "yes" in evaluation_lower:
                return "Yes"
            elif "no" in evaluation_lower:
                return "No"
            elif "off" in evaluation_lower:
                return "Off"
            elif "end" in evaluation_lower:
                return "End"
            else:
                return "No"  # Default to "No" if the response is ambiguous
        except Exception as e:
            return "No"  # Fallback to "No" in case of an error

    def _get_time_of_day(self) -> str:
        """Determine the current time of day."""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 21:
            return 'evening'
        else:
            return 'night'

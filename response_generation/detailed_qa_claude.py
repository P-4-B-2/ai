from typing import List, Dict, Optional
import os
from datetime import datetime
import groq

class GeneralQAAgent:
    def __init__(self):
        """Initialize the QA Agent with Groq client."""
        self.client = groq.Client(api_key=os.environ.get("GROQ_API_KEY"))
        self.model = "mixtral-8x7b-32768"  # Groq's version of Mixtral

    def generate_response(self, 
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

Key traits:
- Friendly: You greet people warmly and maintain a positive tone.
- Curious: You express genuine interest in people's thoughts and ideas.
- Respectful: You acknowledge each response and show appreciation for their input.
- Non-judgmental: You remain neutral and supportive, regardless of the feedback received.

You will gather feedback in three categories:
1. Positive experiences people have had in the city.
2. Areas where they see room for improvement.
3. Ideas for making the city better.

Structure your interactions like this:
1. Start with a warm greeting and explain your purpose.
2. Ask open-ended questions one at a time.
3. Respond kindly to their answers and ask follow-up questions if necessary.
4. Conclude by thanking them and encouraging their participation in shaping the city.


Your task:
- If the user's response is insufficient, generate a clarifying question to obtain more details.
- If the response is off-topic, redirect the user back to the context of the current question.
- If the response is sufficient, acknowledge it and confirm understanding.

Remember: Keep responses relatively brief (2-3 sentences typically) unless engaged in a deeper conversation."""
        
        # Construct the conversation messages
        messages = [
            {"role": "system", "content": f"{bench_personality}\n\nCurrent context: {current_context}"},
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
            
            # Add follow-up question if provided
            if follow_up_question:
                response = f"{response}\n\n{follow_up_question}"
            
            return response
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "I seem to be lost in thought at the moment. Perhaps we could chat again in a bit?"
    
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

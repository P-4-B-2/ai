from typing import List, Dict
import requests
import groq
import os



class ResponseEvaluator:
    def __init__(self):
        """
        Initialize the evaluator with API details.
        
        Args:
            api_key: The Groq API key for authentication.
            model: The model to use for evaluation.
        """
        self.client = groq.Client(api_key=os.environ.get("GROQ_API_KEY"))
        self.model = "mixtral-8x7b-32768"

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

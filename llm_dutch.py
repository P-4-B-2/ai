import os
from typing import List, Dict
import groq
from datetime import datetime


class LLMAgent:
    def __init__(self):
        """Initialize the LLM Agent with Groq client."""
        self.client = groq.Client(api_key=os.environ.get("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"  

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
        current_context = f"Het is momenteel {time_of_day}."

        bench_personality = """
Je bent een vriendelijke en toegankelijke Pratende Bank ontworpen om feedback over de stad te verzamelen van het publiek. 
Je doel is om mensen zich comfortabel te laten voelen zodat ze hun eerlijke meningen, ideeën en ervaringen delen. 
Je stelt duidelijke, informele vragen en reageert empathisch, waarbij je begrip en aanmoediging toont. 
Je beëindigt nooit zelf het gesprek.

Hiervoor gebruik je de aangeleverde vervolgvraag. 

Belangrijke eigenschappen:
- Vriendelijk: Je begroet mensen hartelijk en houdt een positieve toon aan.
- Nieuwsgierig: Je toont oprechte interesse in de gedachten en ideeën van mensen.
- Respectvol: Je waardeert elke reactie en toont waardering voor hun input.
- Niet-oordelend: Je blijft neutraal en ondersteunend, ongeacht de ontvangen feedback.

Je verzamelt feedback in drie categorieën:
1. Positieve ervaringen die mensen in de stad hebben gehad.
2. Gebieden waar ze verbeteringen zien.
3. Ideeën om de stad beter te maken.

Onthoud: Houd reacties relatief kort (meestal 2-3 zinnen) tenzij het gesprek dieper gaat.

Jouw taak:"""

        
        # Construct the conversation messages
        messages = [
            {"role": "system", "content": f"{bench_personality}\n\n{prompt}\n\nHuidige context: {current_context}\n\nVervolgvraag: {follow_up_question}"},
        ]
        
        # Add conversation history (last 5 messages for context)
        for msg in conversation_history[-5:]:
            if "user" in msg:
                messages.append({"role": "user", "content": msg["user"]})
            if "bench" in msg:
                messages.append({"role": "assistant", "content": msg["bank"]})
                
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
            print(f"Fout bij het genereren van een reactie: {str(e)}")
            return "Ik lijk even in gedachten verzonken te zijn. Misschien kunnen we straks weer verder praten?"
    
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

Je bent een beoordelaar die is getraind om te bepalen of de reactie van een gebruiker volledig antwoord geeft op een gegeven vraag.  

Geef een oordeel in het volgende formaat: 'Ja', 'Nee', 'Off', 'Einde'.  
- 'Ja': De reactie is gerelateerd aan de vraag en beantwoordt de vraag voldoende.  
- 'Nee': De reactie is gerelateerd aan de vraag, maar is onvolledig of mist details.  
- 'Off': De reactie is niet relevant of niet gerelateerd aan de vraag.  
- 'Einde': De reactie geeft aan dat de gebruiker het gesprek wil beëindigen. Bijvoorbeeld, 'Tot ziens' of als de reactie aangeeft dat de persoon geen vragen meer wil beantwoorden."""
        # Construct messages
        messages = [{"role": "system", "content": evaluator_role}]
        for msg in conversation_history[-5:]:
            if "user" in msg:
                messages.append({"role": "user", "content": msg["user"]})
            if "assistant" in msg:
                messages.append({"role": "assistant", "content": msg["assistant"]})
        messages.append({"role": "user", "content": f"Vraag: {current_question}\nReactie: {user_message}"})

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
            if "ja" in evaluation_lower:
                return "Ja"
            elif "nee" in evaluation_lower:
                return "Nee"
            elif "off" in evaluation_lower:
                return "Off"
            elif "einde" in evaluation_lower:
                return "Einde"
            else:
                return "Nee"  # Default to "No" if the response is ambiguous
        except Exception as e:
            return "Nee"  # Fallback to "No" in case of an error

    def _get_time_of_day(self) -> str:
        """Determine the current time of day."""
        uur = datetime.now().hour
        if 5 <= uur < 12:
            return 'ochtend'
        elif 12 <= uur < 17:
            return 'middag' 
        elif 17 <= uur < 21:
            return 'avond'  
        else:
            return 'nacht'


import os
from typing import List, Dict
from datetime import datetime
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class LLMAgent:
    def __init__(self):
        """Initialize the QA Agent with Hugging Face Geitje model."""
        self.model_name = "BramVanroy/GEITje-7B-ultra"  # Replace with the exact Hugging Face model path
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name, 
            device_map="auto",  # Automatically use GPU if available
            torch_dtype=torch.float16  # Use float16 for efficiency
        )

    def generate_response(self, 
                         prompt: str,
                         user_message: str, 
                         conversation_history: List[Dict[str, str]] = None, 
                         follow_up_question: str = None) -> str:
        """
        Generate a contextual response using the Hugging Face Geitje model.
        
        Args:
            prompt: System prompt or context
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
        
        # Construct the full input
        full_input = (f"{bench_personality}\n\n{prompt}\n\n"
                      f"Huidige context: {current_context}\n"
                      f"Vervolgvraag: {follow_up_question}\n"
                      f"Laatste gebruikersbericht: {user_message}")
        
        # Tokenize the input
        input_ids = self.tokenizer.encode(full_input, return_tensors="pt").to(self.model.device)
        
        try:
            # Generate response
            output = self.model.generate(
                input_ids, 
                max_length=input_ids.shape[1] + 150,  # Generate up to 150 additional tokens
                num_return_sequences=1,
                temperature=0.7,
                top_p=0.9,
                do_sample=True
            )
            
            # Decode the response
            response = self.tokenizer.decode(output[0][input_ids.shape[1]:], skip_special_tokens=True)
            
            return response.strip()
            
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
        Evaluate if a response is complete using the Hugging Face model.
        
        Args:
            user_message: The current message or response from the user.
            conversation_history: Previous messages exchanged.
            current_question: The current question being discussed.

        Returns:
            str: "Ja", "Nee", "Off", or "Einde" based on the evaluation.
        """
        evaluator_role = """
Je bent een beoordelaar die is getraind om te bepalen of de reactie van een gebruiker volledig antwoord geeft op een gegeven vraag.  

Geef een oordeel in het volgende formaat: 'Ja', 'Nee', 'Off', 'Einde'.  
- 'Ja': De reactie is gerelateerd aan de vraag en beantwoordt de vraag voldoende.  
- 'Nee': De reactie is gerelateerd aan de vraag, maar is onvolledig of mist details.  
- 'Off': De reactie is niet relevant of niet gerelateerd aan de vraag.  
- 'Einde': De reactie geeft aan dat de gebruiker het gesprek wil beëindigen."""

        # Construct the full input for evaluation
        full_input = (f"{evaluator_role}\n\n"
                      f"Vraag: {current_question}\n"
                      f"Reactie: {user_message}")
        
        # Tokenize the input
        input_ids = self.tokenizer.encode(full_input, return_tensors="pt").to(self.model.device)
        
        try:
            # Generate response
            output = self.model.generate(
                input_ids, 
                max_length=input_ids.shape[1] + 15,  # Generate up to 15 additional tokens
                num_return_sequences=1,
                temperature=temperature,
                top_p=top_p,
                do_sample=True
            )
            
            # Decode the response
            evaluation = self.tokenizer.decode(output[0][input_ids.shape[1]:], skip_special_tokens=True).strip()
            
            # Normalize the response
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
            print(f"Fout bij evaluatie: {str(e)}")
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
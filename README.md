# **Talking Bench AI**  

## **Project Overview**  
The **Talking Bench AI** is an interactive system designed to collect user feedback about the city through a conversational interface. The system operates in two main environments:  
1. **Bench-side AI** (Running on the physical bench)  
2. **Cloud AI** (Hosted for processing sentiment analysis, summaries, and keyword extraction)  

## **Project Structure**  

📂 **stt/** *(Speech-to-Text Processing)*  
- `stt_whisper.py` → Uses Whisper AI for speech recognition.  

📂 **tts/** *(Text-to-Speech Processing)*  
- `tts_female.py` → Female voice text-to-speech implementation.  
- `tts_male.py` → Male voice text-to-speech implementation.  

📄 **main_dutch.py** *(Bench-side AI – Main File)*  
- Runs the conversation loop on the physical bench.  
- Uses gTTS for text-to-speech.  
- Captures user responses for speech-to-text.  
- Sends responses for classification.  

📄 **main.py** *(Cloud AI – Sentiment Analysis & Processing)*  
- Processes user responses from the bench.  
- Performs **sentiment analysis**, **summarization**, and **keyword extraction**.  
- Uses the **Groq API** for response classification.  

📄 **manager.py** *(Questionnaire Flow Management)*  
- Controls the sequence of questions.  
- Ensures the conversation stays on-topic.  

📄 **llm_dutch.py** *(Dutch Language LLM Integration)*  
- Handles response generation in Dutch.  

📄 **requirements.txt** *(Dependencies)*  
- Lists required Python packages for the project.  

📄 **README.md** *(You are here!)*  

## **How It Works**  

1. **User Interaction:**  
   - A person sits on the bench and presses a button to start.  
   - The AI greets them and asks a pre-written question.  

2. **Speech Processing:**  
   - The user responds, and their speech is converted to text using Vosk.  
   - The AI plays background music while waiting for an answer.  

3. **Response Analysis:**  
   - The cloud-hosted AI (`main.py`) performs a sentiment analysis on the response.  
   - Keywords are extracted to categorize feedback (e.g., public transport, tourism).  

4. **Conversation Flow:**  
   - The system asks follow-up questions if needed.  
   - If no response is detected after multiple attempts, the AI ends the conversation politely.  

## **Technologies Used**  

🚀 **Speech-to-Text:** Vosk, Whisper  
🗣 **Text-to-Speech:** gTTS  
🤖 **AI & NLP:** Groq API, Llama 3.3 70B  
☁️ **Cloud Services:** Firestore  
🎵 **Audio Processing:** Background music integration  

from multiprocessing import Process, Queue, Event
from typing import List, Dict, Optional
import json
from pathlib import Path
import requests
from datetime import datetime
import os

class ManagerAgent:
    def __init__(self, llm_agent, stt_agent, tts_agent, api_base_url, bench_id):
        self.llm_agent = llm_agent
        self.stt_agent = stt_agent
        self.tts_agent = tts_agent
        self.api_base_url = api_base_url
        self.current_question_index = 0
        self.max_follow_ups = 2
        self.bench_id = bench_id
        self.conversation_id = None
        self.questions = []
        self.headers = {
            "Authorization": f"Bearer {os.environ.get('bearer_token')}",
            "Content-Type": "application/json",
        }

        # Multiprocessing setup
        self.tts_queue = Queue()
        self.stt_queue = Queue()
        self.llm_queue = Queue()
        self.tts_done_event = Event()
        self.stop_event = Event()

        # Start TTS and STT processes
        self.tts_process = Process(target=self.tts_worker)
        self.stt_process = Process(target=self.stt_worker)
        self.tts_process.start()
        self.stt_process.start()

    def tts_worker(self):
        """Process for handling TTS requests"""
        while not self.stop_event.is_set():
            text = self.tts_queue.get()
            if text is None:  # Poison pill
                break
            self.tts_agent.text_to_speech(text)
            self.tts_done_event.set()  # Signal TTS completion

    def stt_worker(self):
        """Process for continuous speech recognition"""
        while not self.stop_event.is_set():
            self.stt_queue.put(self.stt_agent.transcribe_audio())

    def __del__(self):
        """Cleanup processes on destruction"""
        self.stop_event.set()
        self.tts_queue.put(None)
        self.tts_process.join()
        self.stt_process.terminate()
        self.stt_process.join()

    # (Keep existing methods: create_conversation, end_conversation, 
    #  fetch_questions, get_question, submit_answer mostly unchanged)

    def run(self):
        """Modified main loop using multiprocessing"""
        conversation_history: List[Dict] = []
        self.create_conversation()
        self.fetch_questions()

        current_question_responses = []
        silent_attempts = 0
        MAX_SILENT_ATTEMPTS = 5

        while self.current_question_index < len(self.questions):
            current_question = self.get_question(self.current_question_index)
            if not current_question:
                break

            # Send TTS request and wait for completion
            self.tts_queue.put(current_question)
            self.tts_done_event.wait()
            self.tts_done_event.clear()

            print(f"\nAI: {current_question}")
            conversation_history.append({"bank": current_question})

            while True:
                print("\nListening...")
                user_message = None
                
                # Listen for user input with timeout
                while not self.stt_queue.empty() and user_message is None:
                    user_message = self.stt_queue.get()

                if not user_message:
                    # Handle silence/no response
                    silent_attempts += 1
                    if silent_attempts >= MAX_SILENT_ATTEMPTS:
                        goodbye_message = "Bedankt voor je tijd. Fijne dag verder!"
                        self.tts_queue.put(goodbye_message)
                        self.end_conversation()
                        return
                    continue

                silent_attempts = 0
                print(f"User said: {user_message}")
                current_question_responses.append(user_message)

                # LLM processing in main process (could be parallelized further)
                is_response_complete = self.llm_agent.evaluate_response(
                    user_message,
                    conversation_history,
                    current_question,
                )

                # (Keep existing response handling logic here)
                # [Rest of your existing logic for handling responses...]

                # Example continuation:
                if is_response_complete == "Ja":
                    combined_response = " ".join(current_question_responses)
                    self.submit_answer(self.current_question_index, combined_response)
                    self.current_question_index += 1
                    current_question_responses = []
                    break

                # Generate response using LLM
                qa_response = self.llm_agent.generate_response(
                    prompt,
                    user_message,
                    conversation_history,
                    next_question
                )

                # Send response via TTS
                self.tts_queue.put(qa_response)
                self.tts_done_event.wait()
                self.tts_done_event.clear()

                conversation_history.append({
                    "user": user_message,
                    "bank": qa_response
                })

        self.end_conversation()

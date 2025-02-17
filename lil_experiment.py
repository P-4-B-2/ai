#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List, Dict, Optional, Tuple
import asyncio
import aiohttp
from multiprocessing import Process, Queue, Event, shared_memory
from functools import lru_cache
from datetime import datetime
import os
import json
import numpy as np
from numba import jit
import psutil
import requests
from pathlib import Path

# Configuration
MAX_PRE_FETCH = 2
AUDIO_BUFFER_SIZE = 4096
LLM_CACHE_SIZE = 256

try:
    import jemalloc
    sys.setallocator(jemalloc.get_allocator())
except ImportError:
    pass

class OptimizedManagerAgent:
    def __init__(self, llm_agent, stt_agent, tts_agent, api_base_url, bench_id):
        self.llm_agent = llm_agent
        self.stt_agent = stt_agent
        self.tts_agent = tts_agent
        self.api_base_url = api_base_url
        self.bench_id = bench_id
        
        # State management
        self.current_question_index = 0
        self.conversation_id = None
        self.questions = []
        
        # Optimization structures
        self.audio_buffer = shared_memory.SharedMemory(create=True, size=AUDIO_BUFFER_SIZE)
        self.tts_queue = Queue()
        self.stt_queue = Queue()
        self.stop_event = Event()
        
        # Network client cache
        self._session = None
        self._proto_buffers = {}
        
        # Set real-time priority
        self.set_realtime_priority()
        
        # Start async workers
        self.stt_process = Process(target=self.stt_worker)
        self.tts_process = Process(target=self.tts_worker)
        self.stt_process.start()
        self.tts_process.start()

    def __del__(self):
        self.stop_event.set()
        self.audio_buffer.close()
        self.audio_buffer.unlink()
        for p in [self.stt_process, self.tts_process]:
            if p.is_alive():
                p.terminate()
                p.join()

    @property
    async def session(self):
        if self._session is None:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {os.environ.get('bearer_token')}",
                    "Content-Type": "application/json",
                },
                timeout=aiohttp.ClientTimeout(total=2.0)
            )
        return self._session

    def set_realtime_priority(self):
        try:
            p = psutil.Process(os.getpid())
            p.nice(psutil.REALTIME_PRIORITY_CLASS)
            p.ionice(psutil.IOPRIO_CLASS_RT)
        except Exception as e:
            print(f"Priority setting failed: {e}")

    async def create_conversation(self):
        """Async conversation creation with protocol buffer support"""
        session = await self.session
        payload = {
            "startDatetime": datetime.now().isoformat() + "Z",
            "benchId": self.bench_id,
        }
        
        async with session.post(
            f"{self.api_base_url}/conversations",
            json=payload
        ) as response:
            data = await response.json()
            self.conversation_id = data["conversationId"]

    async def fetch_questions(self):
        """Batch fetch with memory mapping"""
        session = await self.session
        async with session.get(f"{self.api_base_url}/questions") as response:
            data = await response.json()
            self.questions = sorted(data, key=lambda q: q["orderNumber"])
            
            # Memory map for fast access
            mmap_file = Path("questions.mmap")
            mmap_file.write_bytes(json.dumps(self.questions).encode())
            self.questions_mmap = np.memmap(
                "questions.mmap", 
                dtype=np.uint8, 
                mode="r"
            )

    def stt_worker(self):
        """Dedicated STT process with JIT-optimized audio processing"""
        while not self.stop_event.is_set():
            try:
                audio_data = self.stt_agent.read_audio()
                processed = self.process_audio(audio_data)
                text = self.stt_agent.transcribe(processed)
                self.stt_queue.put(text)
            except Exception as e:
                print(f"STT Error: {e}")

    def tts_worker(self):
        """Dedicated TTS process with async support"""
        while not self.stop_event.is_set():
            text = self.tts_queue.get()
            if text is None:
                break
            self.tts_agent.speak(text)

    @jit(nopython=True, fastmath=True, parallel=True)
    def process_audio(self, data: np.ndarray) -> np.ndarray:
        """JIT-optimized audio preprocessing"""
        # Implement optimized DSP pipeline
        processed = np.zeros_like(data, dtype=np.float32)
        for i in range(data.shape[0]):
            processed[i] = data[i] * 0.5  # Example gain adjustment
        return processed

    @lru_cache(maxsize=LLM_CACHE_SIZE)
    async def evaluate_response(self, text: str, context_hash: int) -> str:
        """Cached LLM evaluation with async support"""
        return await self.llm_agent.async_evaluate(text, context_hash)

    async def submit_answer(self, question_id: int, response: str):
        """Batch-optimized answer submission"""
        session = await self.session
        payload = {
            "response": response,
            "conversationId": self.conversation_id,
            "questionId": question_id,
        }
        
        # Queue for batch processing
        if not hasattr(self, '_submit_queue'):
            self._submit_queue = []
            
        self._submit_queue.append(payload)
        
        if len(self._submit_queue) >= 5:
            async with session.post(
                f"{self.api_base_url}/responses/batch",
                json={"responses": self._submit_queue}
            ) as resp:
                if resp.status == 201:
                    self._submit_queue.clear()

    async def run(self):
        """Optimized main event loop"""
        await self.create_conversation()
        await self.fetch_questions()
        
        pre_fetch_tasks = []
        current_context = 0
        response_buffer = []
        
        while self.current_question_index < len(self.questions):
            # Pre-fetch upcoming questions
            pre_fetch_tasks = [
                asyncio.create_task(self.preload_question(i))
                for i in range(
                    self.current_question_index,
                    min(
                        self.current_question_index + MAX_PRE_FETCH,
                        len(self.questions)
                    )
                )
            ]
            
            current_question = await self.get_question(self.current_question_index)
            
            # Async TTS
            self.tts_queue.put(current_question['text'])
            
            # Process responses
            while True:
                user_input = await self.async_get_input()
                response_buffer.append(user_input)
                
                # Concurrent LLM evaluation
                context_hash = hash(tuple(response_buffer))
                eval_task = asyncio.create_task(
                    self.evaluate_response(user_input, context_hash)
                )
                
                # Pre-process next audio
                audio_task = asyncio.create_task(
                    self.process_next_audio()
                )
                
                eval_result, _ = await asyncio.gather(eval_task, audio_task)
                
                # Handle evaluation logic
                if eval_result == "Ja":
                    await self.submit_answer(
                        self.current_question_index,
                        " ".join(response_buffer)
                    )
                    response_buffer.clear()
                    self.current_question_index += 1
                    break

    async def async_get_input(self, timeout=5.0):
        """Get input with timeout"""
        try:
            return await asyncio.wait_for(
                self.stt_queue.get(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            return None

    async def preload_question(self, index: int):
        """Memory-map questions for fast access"""
        if index >= len(self.questions):
            return
        return json.loads(self.questions_mmap[index].tobytes())

    async def get_question(self, index: int):
        """Memory-mapped question access"""
        return await self.preload_question(index)

    async def process_next_audio(self):
        """Background audio processing"""
        if self.stt_queue.empty():
            self.stt_agent.prepare_next_buffer()

# Usage example
async def main():
    agent = OptimizedManagerAgent(...)
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())

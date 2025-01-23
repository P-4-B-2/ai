import whisper
import numpy as np
import sounddevice as sd
import torch
from pathlib import Path

from typing import Optional

class SpeechToTextAgent:
    def __init__(self, 
                 model_name: str = "base",
                 sample_rate: int = 16000,
                 recording_duration: float = 360.0,
                 silence_threshold: float = 0.05,
                 silence_duration: float = 9.0,
                 language = "nl"):
        """
        Initialize the Speech-to-Text agent using Whisper.
        
        Args:
            model_name: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
            sample_rate: Audio sampling rate in Hz
            recording_duration: Maximum recording duration in seconds
            silence_threshold: Amplitude threshold for silence detection
            silence_duration: Duration of silence to stop recording (seconds)
        """
        self.model = whisper.load_model(model_name)
        self.sample_rate = sample_rate
        self.recording_duration = recording_duration
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.default_language= language

        
        # Check for CUDA availability
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def record_audio(self) -> Optional[np.ndarray]:
        """
        Record audio from the microphone with silence detection.
        
        Returns:
            numpy.ndarray: Recorded audio data, or None if recording failed
        """
        try:
            print("Listening... (speak now)")
            
            # Initialize recording buffer
            recording = []
            silence_samples = 0
            max_samples = int(self.recording_duration * self.sample_rate)
            
            def audio_callback(indata, frames, time, status):
                if status:
                    print(f"Audio callback status: {status}")
                recording.append(indata.copy())

            with sd.InputStream(samplerate=self.sample_rate,
                              channels=1,
                              callback=audio_callback):
                
                while len(recording) * 1024 < max_samples:
                    # Convert latest audio chunk to amplitude
                    if recording:
                        latest_chunk = np.abs(recording[-1]).mean()
                        
                        # Check for silence
                        if latest_chunk < self.silence_threshold:
                            silence_samples += len(recording[-1])
                            if silence_samples > self.silence_duration * self.sample_rate:
                                break
                        else:
                            silence_samples = 0
                            
                    sd.sleep(10)  # Small sleep to prevent CPU overload

            if not recording:
                return None

            # Concatenate all recorded chunks
            audio_data = np.concatenate(recording, axis=0)
            return audio_data.flatten()

        except Exception as e:
            print(f"Error recording audio: {e}")
            return None

    def transcribe_audio(self) -> str:
        """
        Record and transcribe audio to text.
        
        Returns:
            str: Transcribed text, or empty string if transcription failed
        """
        try:
            # Record audio
            audio_data = self.record_audio()
            if audio_data is None:
                return ""

            print("Processing speech...")
            
            # Transcribe using Whisper
            result = self.model.transcribe(
                audio_data,
                fp16=torch.cuda.is_available(),
                language=self.default_language  # You can change this for other languages
            )
            
            transcribed_text = result["text"].strip()
            
            return transcribed_text

        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return ""



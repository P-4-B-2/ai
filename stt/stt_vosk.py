import sounddevice as sd
import numpy as np
from vosk import Model, KaldiRecognizer
import json
import sys
import queue

# Audio settings
SAMPLE_RATE = 16000
CHANNELS = 1
DURATION = 10

class SpeechToTextAgent:

    def load_vosk_model(model_path=r"C:\Users\r0916586\Documents\ai\models\vosk-model-small-en-us-0.15"):
    # def load_vosk_model(model_path=r"C:\Users\r0916586\Documents\ai\models\vosk-model-nl-spraakherkenning-0.6"):

        """
        Load the Vosk model from the specified path.
        Download models from https://alphacephei.com/vosk/models
        """
        try:
            model = Model(model_path)
            return model
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Please download a model from https://alphacephei.com/vosk/models")
            sys.exit(1)

    def create_recognizer(self, sample_rate):
        """
        Create a KaldiRecognizer instance with the specified model and sample rate.
        """
        model=self.load_vosk_model()
        return KaldiRecognizer(model, sample_rate)

    def record_audio(self, duration, sample_rate, channels):
        """
        Record audio from the microphone and return it as a NumPy array.
        """
        print("Recording... Speak now!")
        audio_queue = queue.Queue()
    
        def callback(indata, frames, time, status):
            if status:
                print(status)
            audio_queue.put(bytes(indata))
    
        with sd.RawInputStream(samplerate=sample_rate, 
                            channels=channels,
                            dtype=np.int16,
                            blocksize=8000,
                            callback=callback):
            print("Recording...")
            audio_data = []
            for _ in range(int(duration * sample_rate / 8000)):
                audio_data.append(audio_queue.get())
    
        print("Recording complete!")
        return b''.join(audio_data)

    def transcribe_audio(self):
        """
        Transcribe audio data using Vosk.
        """
        recognizer = self.create_recognizer(SAMPLE_RATE)
        audio_data = self.record_audio(DURATION, SAMPLE_RATE, CHANNELS)

        print("Transcribing audio...")
        if recognizer.AcceptWaveform(audio_data):
            result = json.loads(recognizer.Result())
            return result['text']
        else:
            result = json.loads(recognizer.PartialResult())
            return result.get('partial', '')

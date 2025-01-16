import torch
import sounddevice as sd
import numpy as np
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

# Device and model settings
device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

model_id = "openai/whisper-large-v3"

print("Loading Whisper model...")
model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
)
model.to(device)

processor = AutoProcessor.from_pretrained(model_id)

pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    torch_dtype=torch_dtype,
    device=device,
)

# Audio settings
SAMPLE_RATE = 16000  # Required by Whisper
CHANNELS = 1         # Mono audio
DURATION = 10        # Duration in seconds

def record_audio(duration, sample_rate, channels):
    """
    Record audio from the microphone and return it as a NumPy array.
    """
    print("Recording... Speak now!")
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=channels, dtype=np.float32)
    sd.wait()  # Wait until the recording is finished
    print("Recording complete!")
    return audio_data.flatten()

def transcribe_audio(audio_data, sample_rate):
    """
    Transcribe audio data using the Whisper pipeline.
    """
    print("Transcribing audio...")
    result = pipe({"array": audio_data, "sampling_rate": sample_rate,  "language": "en"})
    print("Transcription complete!")
    return result['text']




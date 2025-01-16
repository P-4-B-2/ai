from gtts import gTTS
import pygame
import tempfile
import os
def text_to_speech(text, language='en'):
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
        temp_filename = temp_file.name
        
    # Create a gTTS object
    tts = gTTS(text=text, lang=language, slow=False)
    # Save the audio to the temporary file
    tts.save(temp_filename)
    # Play the audio file
    os.system(f"start {temp_filename}")

    # finally:
    #     # Clean up: remove the temporary file
    #     if os.path.exists(temp_filename):
    #         os.remove(temp_filename)
    #         print(f"Temporary file {temp_filename} has been removed.")



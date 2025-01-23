from gtts import gTTS
import pygame
import tempfile
import os

class TTSAgent():

    def __init__(self, language="nl"):
        """
        Initialize the TTSAgent with a default language.
        
        :param language: The default language for text-to-speech. Defaults to 'nl' (Dutch).
        """
        self.default_language = language
        
    def text_to_speech(self, text):
        """
        Convert text to speech and play synchronously using gTTS and pygame.

        :param text: The text to convert to speech.
        :param language: The language for the speech. Defaults to 'nl' (Dutch).
        """
        # Create a temporary file for the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_filename = temp_file.name

        try:
            # Convert text to speech using gTTS and save it to the temporary file
            tts = gTTS(text=text, lang=self.default_language, slow=False)
            tts.save(temp_filename)

            # Initialize pygame mixer and play the audio
            pygame.mixer.init()
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()

            # Wait for the audio to finish playing
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

        finally:
            # Stop the mixer and clean up resources
            pygame.mixer.quit()

            # Remove the temporary file
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

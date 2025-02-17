
import pyttsx3

class TTSAgent():
    def __init__(self):
        """
        Initialize the TTSAgent with a default language.
        
        :param language: The default language for text-to-speech. Defaults to 'nl' (Dutch).
        """
        self.engine = pyttsx3.init(driverName='nsss')
    

    def text_to_speech(self, text):
        """
        Convert text to speech and play synchronously using pyttsx3.

        :param text: The text to convert to speech.
        """
        self.engine.setProperty('voice', 'com.apple.voice.compact.nl-NL.Xander')
        self.engine.setProperty('rate', 150) # Speed of speech
        self.engine.setProperty('volume', 1) # Volume level (0.0 to 1.0)
        self.engine.say(text)
        self.engine.runAndWait()


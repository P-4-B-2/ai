import firebase_admin
from firebase_admin import credentials, firestore
import os

# Path to your Firebase credentials file
CREDENTIALS_PATH = 'credentials/talking-bench-firebase-adminsdk-j1avt-4881810775.json'  # Replace with your path

# Initialize Firebase
def initialize_database():
    if not firebase_admin._apps:
        cred = credentials.Certificate(CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
    print("Firebase initialized successfully!")

# Get Firestore client
def get_firestore_client():
    return firestore.client()

# Log interaction in Firestore
def log_interaction(question, transcription,  reasoning, classification):
    db = get_firestore_client()
    interactions_ref = db.collection('interactions')
    interaction_data = {
        "question": question,
        "transcription": transcription,
        "reasoning": reasoning,
        "classification": classification,
        "timestamp": firestore.SERVER_TIMESTAMP  # Automatically sets timestamp
    }
    interactions_ref.add(interaction_data)
    print(f"Logged interaction: {interaction_data}")

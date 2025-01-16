import json 


# Load questions from the JSON file
def load_questions(file_path="questions_nl.json"):
    """
    Loads the questions from a JSON file.
    """
    with open(file_path, "r") as file:
        return json.load(file)

def get_question(index):
    questions = load_questions()

    """
    Returns the next question in the questionnaire, or None if complete.
    """
    return questions[index]["question"] if index < len(questions) else None


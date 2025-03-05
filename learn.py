import random
import sys
import json
import os
import firebase_admin
from firebase_admin import credentials, firestore
from colorama import Fore, Style
from words.words import terms, LIST_NAME

PROGRESS_FILE = "progress.json"
LEARNING_SET_SIZE = 10

# Initialize Firebase
cred = credentials.Certificate("firebase_credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Firestore collection reference (unique for each list)
progress_ref = db.collection("learning_progress").document(LIST_NAME)


def load_progress():
    """Load progress from Firestore, falling back to local JSON if offline."""
    try:
        doc = progress_ref.get()
        if doc.exists:
            return doc.to_dict()
    except Exception:
        print("Firestore unavailable, using local storage.")
    
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    
    return {}


def save_progress(progress):
    """Save progress to Firestore and local JSON."""
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f)

    try:
        progress_ref.set(progress)  # Sync to Firestore
    except Exception:
        print("Failed to sync with Firestore, saving locally.")


def highlight_mistakes(user_input, correct_answer):
    """Highlight incorrect characters in user input."""
    result = []
    for i, c_char in enumerate(correct_answer):
        if i < len(user_input) and user_input[i] == c_char:
            result.append(Fore.GREEN + user_input[i] + Style.RESET_ALL)
        elif i < len(user_input):
            result.append(Fore.RED + user_input[i] + Style.RESET_ALL)
        else:
            result.append(Fore.YELLOW + c_char + Style.RESET_ALL)
    return ''.join(result)


def start_quiz(reverse=False):
    """Main learning loop, using Firestore for persistence."""
    progress = load_progress()

    for term in terms:
        if term not in progress:
            progress[term] = 0

    learning_set = [t for t, c in progress.items() if c < 2][:LEARNING_SET_SIZE]

    while len(learning_set) > 0:
        for russian_term in learning_set[:]:
            french_term = terms[russian_term]
            question, answer = (french_term, russian_term) if reverse else (russian_term, french_term)
            user_answer = input(f"Traduisez : '{Fore.CYAN + question + Style.RESET_ALL}'\nVotre réponse : ").strip()

            if user_answer.lower() == answer.lower():
                print(Fore.GREEN + "Correct !" + Style.RESET_ALL)
                progress[russian_term] += 1
                if progress[russian_term] >= 2:
                    learning_set.remove(russian_term)
                    new_candidates = [t for t in progress.keys() if t not in learning_set and progress[t] < 2]
                    if new_candidates:
                        learning_set.append(random.choice(new_candidates))
            else:
                print("Erreur ! Votre réponse : ", highlight_mistakes(user_answer, answer))
                print(Fore.YELLOW + f"La bonne réponse est : {answer}" + Style.RESET_ALL)
                progress[russian_term] = max(0, progress[russian_term] - 1)

            save_progress(progress)

        next_step = input("Voulez-vous continuer ? (O/n) : ").strip().lower()
        if next_step == 'n':
            break


if __name__ == "__main__":
    reverse_mode = '-r' in sys.argv
    start_quiz(reverse=reverse_mode)

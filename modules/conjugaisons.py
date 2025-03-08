import os
import sqlite3
from pick import pick
from datetime import datetime
import random
from colorama import Fore, Style
from modules.common import *
from modules.openai import fetch_conjugation


# Constants
CORRECT_REQUIRED = 3  # Number of correct answers required to mark as learned
ACTIVE_WORDS = 20  # Number of active words in learning queue

INBOUND_PATH = "inbound/"


# List of tenses for B2 level
tenses = ["Présent", "Passé Composé", "Imparfait", "Plus-que-parfait", "Futur Simple", "Futur Antérieur", "Conditionnel Présent", "Subjonctif Présent"]


DB_PATH = "words/verbs.db"
def setup():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conjugations (
        verb TEXT,
        tense TEXT,
        pronoun TEXT,
        conjugation TEXT,
        translation_ru TEXT,
        last_update TIMESTAMP,
        correct_count INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()


def show_help(correct_conjugation):
    masked_conjugation = correct_conjugation[0] + "_" * (len(correct_conjugation) - 2) + correct_conjugation[-1]
    print(f"Hint: {masked_conjugation}")

def import_verbs():
    """Reads verbs from inbound folder and stores conjugations."""
    files = [f for f in os.listdir(INBOUND_PATH) if f.endswith(".txt")]
    if not files:
        print("No verb files found in inbound folder.")
        return
    
    title, index = pick(files, "Select a file to import:")
    file_path = os.path.join(INBOUND_PATH, title)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    with open(file_path, "r", encoding="utf-8") as f:
        verbs = [line.strip() for line in f.readlines() if line.strip()]
    
    imported_count = 0
    total_verbs = len(verbs)
    for verb in verbs:
        for tense in tenses:
            existing = cursor.execute("SELECT * FROM conjugations WHERE verb=? AND tense=?", (verb, tense)).fetchone()
            print(f"Checking if {verb} in {tense} already exists in the database: {'Found' if existing else 'Not found'}")
            if not existing:
                conjugations = fetch_conjugation(verb, tense)
                for pronoun, conjugated_form in conjugations.items():
                    if pronoun != "translation_ru":
                        cursor.execute("INSERT INTO conjugations VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                       (verb, tense, pronoun, conjugated_form, conjugations["translation_ru"], datetime.now().isoformat(), 0))
                        conn.commit()
        imported_count += 1
        print(f"Words Imported: {imported_count}/{total_verbs}")
    
    conn.close()

# Update progress and manage learning queue
def update_progress(verb, tense, pronoun, score):
    """Updates progress in SQLite and Firebase, resetting on mistakes."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    current = cursor.execute("SELECT correct_count FROM conjugations WHERE verb=? AND tense=? AND pronoun=?", (verb, tense, pronoun)).fetchone()
    
    if not current:
        conn.close()
        return
    correct_count = current[0] + score

    if correct_count < 0: 
        correct_count = 0

    print(f"NEW CORRECT{correct_count}")    
    
    cursor.execute("UPDATE conjugations SET correct_count=? WHERE verb=? AND tense=? AND pronoun=?", (correct_count, verb, tense, pronoun))
    conn.commit()
    conn.close()
    
    # doc_ref = db.collection("progress").document(f"{verb}-{tense}-{pronoun}")
    # doc_ref.set({
    #     "verb": verb,
    #     "tense": tense,
    #     "pronoun": pronoun,
    #     "correct_count": correct_count,
    #     "last_update": datetime.now().isoformat()
    # }, merge=True)

def get_active_words(tense):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if tense == "Mixed":
        words = cursor.execute("""
            SELECT verb, tense, pronoun FROM conjugations
            WHERE correct_count < ?
            ORDER BY last_update , RANDOM()
            LIMIT ?
        """, (CORRECT_REQUIRED, ACTIVE_WORDS)).fetchall()
    else:
        words = cursor.execute("""
            SELECT verb, tense, pronoun FROM conjugations
            WHERE correct_count < ? AND tense = ?
            ORDER BY last_update ,  RANDOM()
            LIMIT ?
        """, (CORRECT_REQUIRED, tense, ACTIVE_WORDS)).fetchall()
    conn.close()
    return words

# Verb Learning Function
def verb_quiz(tenseTitle):
    """Runs a quiz for learning verb conjugations with progress tracking."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    active_words = get_active_words(tenseTitle)
    
    if not active_words:
        print("No verbs available to learn. Please import first.")
        return
    
    while True:
        verb, tense, pronoun = random.choice(active_words)
        result = cursor.execute("SELECT conjugation, translation_ru, correct_count FROM conjugations WHERE verb=? AND tense=? AND pronoun=?", (verb, tense, pronoun)).fetchone()
        
        if not result:
            continue
        
        correct_conjugation, translation_ru, correct_count = result
        helpFactor = 0;
        print(f"{Fore.CYAN}{translation_ru}{Style.RESET_ALL} / {Fore.MAGENTA}{tense}{Style.RESET_ALL}")
        user_input = input(f"Traduisez : {pronoun} ______ Votre réponse : ").strip()
        print(f"Progress: {correct_count}/{CORRECT_REQUIRED}")

        if user_input ==  "/mh":
            helpFactor = -0.5
            show_help(correct_conjugation)
            user_input = input("Votre responce est >> ")
        if user_input == "/q":
            quit()    


        if user_input.lower() == correct_conjugation.lower():
            print("✅ Bien!")
            update_progress(verb, tense, pronoun, 1 + helpFactor)
        else:
            print("Erreur ! Votre réponse : ", highlight_mistakes(user_input, correct_conjugation))
            print(Fore.YELLOW + f"La bonne réponse est : {Fore.LIGHTGREEN_EX}{correct_conjugation.upper()}" + Style.RESET_ALL)
            update_progress(verb, tense, pronoun, -1)

# Verb Menu
def menu():
    """Menu for selecting verb learning mode."""
    title, index = pick(["Mixed"] + tenses + ["Import Words List"], "Select a mode:")
    
    if title == "Import Words List":
        import_verbs()
    else:
        verb_quiz(title)

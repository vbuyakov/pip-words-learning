import os
import sqlite3
from pick import pick
from datetime import datetime
import random
from colorama import Fore, Style
from modules.common import *
from modules.openai import fetch_conjugation


# Constants
CORRECT_REQUIRED = 2  # Number of correct answers required to mark as learned
ACTIVE_WORDS = 10  # Number of active words in learning queue
DONT_REPEAT_LEN = 3 

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


def show_word_hint(correct_conjugation):
    masked_conjugation = correct_conjugation[0] + "_" * (len(correct_conjugation) - 2) + correct_conjugation[-1]
    print(f"Hint: {masked_conjugation}")
def show_help(): 
    print(f"-------- \n {Fore.MAGENTA}/q{Style.RESET_ALL} or {Fore.MAGENTA}!q{Style.RESET_ALL} - Sortir de app \n {Fore.MAGENTA}/mh{Style.RESET_ALL} or {Fore.MAGENTA}!mh{Style.RESET_ALL} - Aidez moi \n -------- ")

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
    conn = sqlite3.connect(DB_PATH, autocommit=True)
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
    conn.close()
    return correct_count

def get_active_words(tense, words_count= ACTIVE_WORDS):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.row_factory = lambda cursor, row: list(row)
    
    if tense == "Mixed":
        words = cursor.execute("""
            SELECT verb, tense, pronoun, conjugation, translation_ru, correct_count FROM conjugations
            WHERE correct_count < ?
            ORDER BY  RANDOM()
            LIMIT ?
        """, (CORRECT_REQUIRED, words_count)).fetchall()
    else:
        words = cursor.execute("""
            SELECT verb, tense, pronoun, conjugation, translation_ru, correct_count FROM conjugations
            WHERE correct_count < ? AND tense = ?
            ORDER BY  RANDOM()
            LIMIT ?
        """, (CORRECT_REQUIRED, tense, words_count)).fetchall()
    conn.close()
    return words



def get_random_word_idx(active_words, showed_words):
    verbIdx = random.randint(0, len(active_words) -1 );
    verb, tense, pronoun, correct_conjugation, translation_ru, correct_count  = active_words[verbIdx]
    if f"{verb}-{tense}-{pronoun}" in showed_words:
        return get_random_word_idx(active_words, showed_words)
    else: 
        return verbIdx;

def word_showed(showed_words, word_key):
    if len(showed_words) >= DONT_REPEAT_LEN:
        showed_words.pop(0)
    showed_words.append(word_key)

    


# Verb Learning Function
def verb_quiz(tenseTitle):
    """Runs a quiz for learning verb conjugations with progress tracking."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    active_words = get_active_words(tenseTitle)
    
    if not active_words:
        print("No verbs available to learn. Please import first.")
        return
    
    showed_words = []

    while len(active_words) > 0:

        verbIdx = get_random_word_idx(active_words, showed_words)
        verb, tense, pronoun, correct_conjugation, translation_ru, correct_count  = active_words[verbIdx]



        helpFactor = 0;
        print(f"{Fore.CYAN}{translation_ru}{Style.RESET_ALL} / {Fore.MAGENTA}{tense}{Style.RESET_ALL}")
        user_input = input(f"Traduisez : {pronoun} ______ Votre réponse : ").strip()
        

        if user_input ==  "":
            show_help()
            user_input = input("Votre responce est >> ")
        if user_input ==  "/am" or user_input == "!am":
            helpFactor = -0.5
            show_word_hint(correct_conjugation)
            user_input = input("Votre responce est >> ")
        if user_input == "/q" or user_input == "!q":
            quit()    

        successScore = 0;

        if user_input.lower() == correct_conjugation.lower():
            successScore = 1 + helpFactor;
        else:
            successScore = - 1

        newCorrectCount = update_progress(verb, tense, pronoun, successScore)

        if newCorrectCount >= CORRECT_REQUIRED:
            del active_words[verbIdx]
            active_words = active_words + get_active_words(tenseTitle, 1)
            print(f"{Fore.LIGHTGREEN_EX} APPRIS! {Style.RESET_ALL}")
        else:
            active_words[verbIdx][-1] = newCorrectCount
            word_showed(showed_words, f"{verb}-{tense}-{pronoun}")
            if successScore < 0:
                print("Erreur ! Votre réponse : ", highlight_mistakes(user_input, correct_conjugation))
                print(f"{Fore.YELLOW}La bonne réponse est : {Fore.LIGHTGREEN_EX}{correct_conjugation.upper()}{Style.RESET_ALL}{Style.RESET_ALL}")
            else:
                print(f"{Fore.LIGHTGREEN_EX} Beien! {Style.RESET_ALL}{Fore.LIGHTBLACK_EX}{newCorrectCount}/{CORRECT_REQUIRED}{Style.RESET_ALL}")
                
# Verb Menu
def menu():
    """Menu for selecting verb learning mode."""
    title, index = pick(["Mixed"] + tenses + ["Import Words List"], "Select a mode:")
    
    if title == "Import Words List":
        import_verbs()
    else:
        verb_quiz(title)

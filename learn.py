from modules.progress_db import *
from modules.electrowords import words_quiz
import modules.conjugaisons 
from pick import pick


# Main Menu
def main():
    modules.conjugaisons.setup()
    while True:
        title, index = pick(["Words", "Verbs", "Exit"], "Select what to learn:")
        
        if title == "Exit":
            break
        elif title == "Verbs":
            modules.conjugaisons.menu()
        elif title == "Words":
            word_quiz()

if __name__ == "__main__":
    main()

from colorama import Fore, Style    

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

from colorama import Fore, Style    

def highlight_mistakes(user_input, correct_answer):
    """Highlight incorrect characters in user input."""
    result = []
    max_len = max(len(user_input), len(correct_answer))
    for i in range(max_len):
        if i < len(user_input) and i < len(correct_answer):
            if user_input[i] == correct_answer[i]:
                result.append(Fore.GREEN + user_input[i] + Style.RESET_ALL)
            else:
                result.append(Fore.RED + user_input[i].upper() + Style.RESET_ALL)
        elif i < len(user_input):
            result.append(Fore.RED + user_input[i].upper() + Style.RESET_ALL)
        else:
            result.append(Fore.RED + correct_answer[i].upper() + Style.RESET_ALL)
    return ''.join(result)

from colorama import Fore, Style, init


# initialize colorama
init(autoreset=True)
def print_colored_text(text, color):
    # Print the processed text in the specified color
    if color == "red":
        print(Fore.RED + text)
    elif color == "green":
        print(Fore.GREEN + text)
    elif color == "blue":
        print(Fore.BLUE + text)
    else:
        print(text)


# Example usage
print_colored_text("Hello, world!", "red")
print_colored_text("This is a test.", "green")
print_colored_text("Python is fun!", "blue")
print_colored_text("No color for this one.", "none")
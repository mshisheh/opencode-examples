import os
import random

WORDS = ["python", "terminal", "keyboard", "developer", "hangman",
         "giraffe", "puzzle", "jazz", "cobweb", "rhythm"]

STAGES = [
    """
       -----
       |   |
           |
           |
           |
           |
      =========""",
    """
       -----
       |   |
       O   |
           |
           |
           |
      =========""",
    """
       -----
       |   |
       O   |
       |   |
           |
           |
      =========""",
    """
       -----
       |   |
       O   |
      /|   |
           |
           |
      =========""",
    """
       -----
       |   |
       O   |
      /|\\  |
           |
           |
      =========""",
    """
       -----
       |   |
       O   |
      /|\\  |
      /    |
           |
      =========""",
    """
       -----
       |   |
       O   |
      /|\\  |
      / \\  |
           |
      =========""",
]

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def main():
    word = random.choice(WORDS)
    guessed = set()
    wrong = 0

    while wrong < len(STAGES) - 1:
        clear()
        print(" HANGMAN\n")
        print(STAGES[wrong])
        display = " ".join(c if c in guessed else "_" for c in word)
        print(f"\n  {display}\n")
        print(f" Guessed: {', '.join(sorted(guessed)) if guessed else 'none'}")
        letter = input("\n  Guess a letter: ").lower().strip()

        if len(letter) != 1 or not letter.isalpha():
            continue
        if letter in guessed:
            continue

        guessed.add(letter)

        if letter not in word:
            wrong += 1
        elif all(c in guessed for c in word):
            clear()
            print(STAGES[wrong])
            print(f"\n  {word}")
            print("\n  You win!\n")
            return

    clear()
    print(STAGES[wrong])
    print(f"\n  The word was: {word}")
    print("\n  Game over!\n")

if __name__ == "__main__":
    main()

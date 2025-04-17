import hunspell

# load dictionaries once globally
uk_dict = hunspell.HunSpell('/usr/share/hunspell/en_GB.dic', '/usr/share/hunspell/en_GB.aff')
us_dict = hunspell.HunSpell('/usr/share/hunspell/en_US.dic', '/usr/share/hunspell/en_US.aff')

def change_british_to_american(word):
    # check if it is a British spelling not accepted in US
    if uk_dict.spell(word) and not us_dict.spell(word):
        suggestions = us_dict.suggest(word)
        return suggestions[0] if suggestions else word
    return word

if __name__ == '__main__':
    print(change_british_to_american("colour"))  # "color"
    print(change_british_to_american("organise"))  # "organize"
    print(change_british_to_american("center"))  # "center" (no change)
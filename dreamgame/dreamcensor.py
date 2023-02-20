def dreamcensor(censored, names):
    suffixes = ["", "’s", "'s", "s", ",", ".", "?", "!", ")", "(", '"']
    prefixes = ["", ",", ".", "?", "!", ")", "(", '"']
    # nested for loop to search for names and censor them
    for i in range(len(censored)):
        for name in names:
            if name in censored[i].capitalize(): # this line is only for optimization
                # names followed by a suffix
                for suffix in suffixes:
                    if censored[i].capitalize() == name + suffix:
                        censored[i] = "###" + suffix
                # names preceeded by a prefix
                for prefix in prefixes:
                    if censored[i].capitalize() == prefix + name:
                        censored[i] = prefix + "###"
    return ((" ").join(censored))
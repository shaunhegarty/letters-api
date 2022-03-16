def is_anagram(word1, word2):
    """
    Is word1 an anagram of word2
    :param word1:
    :param word2:
    :return:
    """
    if len(word1) != len(word2):
        return False

    sorted_word1 = "".join(sorted(word1.lower()))
    sorted_word2 = "".join(sorted(word2.lower()))
    return sorted_word1 == sorted_word2


def is_sub_anagram(word1, word2):
    """
    Are all the letters of word1 contained in word2
    :param word1:
    :param word2:
    :return:
    """
    # word2 must be longer in this case

    if len(word2) < len(word1):
        return False
    if len(word1) == 0:
        return False
        # raise ValueError("First word is empty")

    sorted_word1 = sorted(word1.lower())
    sorted_word2 = sorted(word2.lower())

    # Step along word2 and and increment word1_index when a match is found.
    # If we're not at the end of word1 by the time we reach the end of word2, return False
    # This only works because their sorted

    word1_index = 0
    for word in sorted_word2:
        if sorted_word1[word1_index] == word:
            word1_index += 1
        if word1_index >= len(sorted_word1):
            break
    # print(f'word1_index: {word1_index}; length of sorted word1: {len(sorted_word1)}')

    return word1_index == len(sorted_word1)

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
    elif len(word1) == 0:
        return False
        # raise ValueError("First word is empty")

    sorted_word1 = sorted(word1.lower())
    sorted_word2 = sorted(word2.lower())

    # Step along word2 and and increment word1_index when a match is found.
    # If we're not at the end of word1 by the time we reach the end of word2, return False
    # This only works because their sorted

    word1_index = 0
    for x in range(len(sorted_word2)):
        if sorted_word1[word1_index] == sorted_word2[x]:
            word1_index += 1
        if word1_index >= len(sorted_word1):
            break
    # print('word1_index: ' + str(word1_index) + '; length of sorted word1: ' + str(len(sorted_word1)))

    return word1_index == len(sorted_word1)

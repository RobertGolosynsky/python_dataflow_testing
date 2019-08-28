def percent(covered, available):
    l_a = len(available)
    if l_a == 0:
        return 0
    return len(covered) * 100 / l_a

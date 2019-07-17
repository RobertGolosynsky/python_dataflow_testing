def testing():
    try:
        in_try = 1
    except IOError:
        in_except = 2
    else:
        in_else = 3
    finally:
        in_finally = 4

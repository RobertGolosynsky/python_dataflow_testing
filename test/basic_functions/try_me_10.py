def testing():
    try:
        in_try = 1
    except:
        a = -100
        raise
    finally:
        a = 0
    out = a

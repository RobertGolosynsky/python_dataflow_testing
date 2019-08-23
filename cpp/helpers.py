def print_rows(rows_grouped):
    for group in rows_grouped:
        print("New scope")
        for row in group:
            print(dump(row))
            # print(repr_row(row))


def dump(obj):
    if isinstance(obj, (int, float, str, dict, set)):
        return str(obj)
    if isinstance(obj, list):
        s = "["
        for el in obj:
            s += dump(el) + ","
        return s + "]"
    s = obj.__class__.__name__ + "{"
    for attr in dir(obj):
        if attr[0] == "_":
            continue
        val = getattr(obj, attr)
        if isinstance(val, (int, float, str, dict, set)):
            s += attr + ":" + str(val) + ","
        elif isinstance(val, list):
            s += attr + ":" + dump(val) + ","
        else:
            s += dump(val) + ""
    return s + "}"
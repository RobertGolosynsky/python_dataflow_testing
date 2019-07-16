def testing(self,a,b):
    x = 3
    # The bug was the except jumping back
    # to the beginning of this for loop
    # for stmt in self:
    try:
        print(a)
        a = 1/0
    except :
        x = 3
        pass
    finally:
        code = 3
    some = 3
    return None

testing(1,2,3)
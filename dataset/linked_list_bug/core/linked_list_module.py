class Node(object):

    def __init__(self, el=None, next=None):
        self.el = el
        self.next = next


class LinkedList(object):

    def __init__(self, seq=None):
        self.root = None
        if isinstance(seq, list):
            for el in seq:
                self.append(el)

    def _last_node(self):
        if not self.root:
            return None
        else:
            node = self.root
            while True:
                if not node.next:
                    return node
                else:
                    node = node.next

    def _get_node(self, i):
        node = self.root
        for j in range(i):
            node = node.next
            if not node:
                return None
        return node

    def append(self, el):
        new_node = Node(el=el, next=None)
        if not self.root:
            self.root = new_node
        else:
            self._last_node().next = new_node

    def get(self, i):
        node = self._get_node(i)
        if not node:
            raise IndexError()
        return node.el

    def remove(self, i):
        if i == 0:
            if self.root:
                self.root = self.root.next
            else:
                raise IndexError()
        else:
            prev_node = self._get_node(i - 1)
            if not prev_node:
                raise IndexError()
            this_node = prev_node.next
            if not this_node:
                raise IndexError()
            prev_node.next = this_node.next

    def len(self):
        l = 0
        node = self.root
        while True:
            if node:
                l += 1
                node = node.next
            else:
                break
        return l

    def as_list(self):
        l = []
        node = self.root
        while node:
            l.append(node.el)
            node = node.next
        return l


def some_annotation(func):
    def some_wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return some_wrapper


@some_annotation
def check(a, b, c, *args, **kwargs):
    print(a, b, c, args, kwargs)


def print_list(l: LinkedList, every_x_el):
    res = []
    for i in range(l.len()):
        if i % every_x_el == 0:
            res = l.get(i)
    while len(res) < 10:
        res.append(0)
    return res

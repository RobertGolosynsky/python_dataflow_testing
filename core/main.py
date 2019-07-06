import graphs.create


class FunctionCFG:
    def __init__(self, func):
        # create a networkx line wise control flow graph
        # node attributes: {
        #   instructions : nx.DiGraph - instructions on the line
        #   line number : int - line number of the line
        #   file path : pathlib.Path - file containing the function
        #
        #   }

        self.g = graphs.create.create_cfg(func)
        self.local_definition_use_pairs = []
        pass


class MethodCFG:
    def __init__(self, method):
        pass


class ClassCFG:
    def __init__(self, cls):
        pass


class ModuleCFG:
    def __init__(self, module):
        pass


class ProjectCFG:
    def __init__(self, project):
        pass


import dataflow.def_use as du


class FunctionCFG:
    def __init__(self, function_object):
        # create a networkx line wise control flow graph
        # node attributes: {
        #   instructions : nx.DiGraph - instructions on the line
        #   line number : int - line number of the line
        #   file path : pathlib.Path - file containing the function
        #
        #   }

        self.cfg = du.try_create_cfg_with_definitions_and_uses(function_object)
        pass


import reflection
import ctrl_flow
import def_use


class ModuleCFG(object):
    def __init__(self, module_path):
        module = reflection.load_module(module_path, "amodule")

        self.cfgs = {}
        self.classes = dict(reflection.module_classes(module))
        self.module_functions = dict(reflection.module_functions(module))
        self.class_functions = {}

        for cls_name, cls in self.classes.items():
            funcs = {}
            for fn_name, fn_descriptor in reflection.class_functions(cls):
                if reflection.method_type(cls, fn_name) == "inherited" and fn_name.startswith("__"):
                    continue
                funcs[fn_name] = fn_descriptor
            self.class_functions[cls_name] = funcs

        for function_name, function_descriptor in self.module_functions.items():
            function_obj = getattr(module, function_name)
            self.cfgs[function_name] = ctrl_flow.create_cfg(function_obj, function_name)

        for class_name, cls_descriptor in self.classes.items():
            cls_object = getattr(module, class_name)

            for function_name, function_descriptor in self.class_functions[class_name].items():
                name = class_name + "." + function_name
                function_obj = getattr(cls_object, function_name)
                self.cfgs[name] = ctrl_flow.create_cfg(function_obj, name)

    def nodes_on_line(self, line_num):
        for func_name, cfg in self.cfgs.items():
            nodes = [x for x, y in cfg.nodes(data=True) if
                     ctrl_flow.line_key in y and y[ctrl_flow.line_key] == line_num]
            if len(nodes) > 0:
                return cfg, nodes
        return None, None

    def defs_for_line(self, line_num: str):
        cfg, nodes = self.nodes_on_line(line_num)
        if cfg:
            for node in nodes:
                varname = def_use.get_def(cfg, node)
                if varname:
                    yield varname

    def uses_for_line(self, line_num: str):
        cfg, nodes = self.nodes_on_line(line_num)
        if cfg:
            for node in nodes:
                varname = def_use.get_use(cfg, node)
                if varname:
                    yield varname


module_cfg = ModuleCFG("dataset/linked_list/core/ll.py")
print(list(module_cfg.defs_for_line("62")))
print(list(module_cfg.uses_for_line("16")))

import ast


def compile_func(function_def):
    # print("compiling function:", function_def.name)
    line = function_def.lineno
    args = _get_function_arg_names(function_def)
    fn_name = function_def.name
    fake_module = ast.Module([_clean_function_node(function_def)])
    namespace = {}
    fake_module_code = compile(fake_module, "", mode="exec")
    exec(fake_module_code, namespace)
    return namespace[fn_name], line, args


def _get_function_arg_names(function_def):
    args = [arg.arg for arg in function_def.args.args]
    if function_def.args.vararg:
        args.append(function_def.args.vararg.arg)
    if function_def.args.kwarg:
        args.append(function_def.args.kwarg.arg)
    return args

def find_end_line(first_line, first_lines):
    filtered = [l for l in first_lines if l > first_line]
    if len(filtered) == 0:
        return None
    return min(filtered)


def compile_module(module_path):
    with open(module_path) as f:
        txt = f.read()
        fns, clss = parse(txt)
    nodes = fns+clss
    first_lines = [n.lineno for n in nodes]

    functions = []
    classes = {}

    for f in fns:
        end = find_end_line(f.lineno, first_lines)
        functions.append((*compile_func(f), end))

    for cls in clss:
        methods = []
        for f in functions_of(cls):
            end = find_end_line(f.lineno, first_lines)
            methods.append((*compile_func(f), end))
        classes[cls.name] = methods

    return functions, classes


def parse(module_code):
    module_ast = ast.parse(module_code)
    return functions_of(module_ast), classes_of(module_ast)


def base_class_names(class_):
    for base_class in class_.bases:
        if isinstance(base_class, ast.Attribute):
            yield base_class.attrname
        else:
            yield base_class.name


def classes_with_base_class(module, base_class):
    return [class_ for class_ in classes_of(module) if base_class in base_class_names(class_)]


def _filter_type(l, t):
    return [node for node in l if isinstance(node, t)]


def classes_of(module):
    return _filter_type(module.body, ast.ClassDef)


def functions_of(module_or_class):
    return _filter_type(module_or_class.body, ast.FunctionDef)


def imports_of(module):
    return _filter_type(module.body, ast.Import) + _filter_type(module.body, ast.ImportFrom)


def function_name(function_node):
    function_parent = function_node.parent
    parent_name = str(function_parent.name)
    return parent_name + "." + function_node.name


def _clean_function_node(func: ast.FunctionDef):
    # print(ast.dump(func))
    func.decorator_list = []
    func.returns = None
    func.args.defaults = []
    # if func.returns:
    #     func.returns.elts = []
    for arg in func.args.args:
        arg.annotation = None
    # print(ast.dump(func))
    return func

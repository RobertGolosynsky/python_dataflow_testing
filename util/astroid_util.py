import ast
import textwrap
import traceback

import asttokens as asttokens
from loguru import logger


class Function:

    def __init__(self, func, first_line, argument_names):
        self.func = func
        self.first_line = first_line
        self.argument_names = argument_names
        self.end_line = None

    @staticmethod
    def from_ast(function_def, first_lines=None):
        logger.debug("Compiling function {n}", n=function_def.name)
        line = function_def.lineno
        args = _get_function_arg_names(function_def)
        fn_name = function_def.name
        fake_module = ast.Module([_clean_function_node(function_def)])
        namespace = {}
        fake_module_code = compile(fake_module, "", mode="exec")
        try:
            exec(fake_module_code, namespace)
        except Exception as e:
            logger.error(traceback.format_exc(e))
            logger.error("Ast dump of function: {d}", d=ast.dump(function_def))
            # TODO: fix this error
        function = Function(namespace[fn_name], line, args)
        if first_lines:
            function.add_end_line(first_lines)
        return function

    def add_end_line(self, first_lines):
        filtered = [l for l in first_lines if l > self.first_line]
        if len(filtered) > 0:
            self.end_line = min(filtered)


def _get_function_arg_names(function_def):
    args = [arg.arg for arg in function_def.args.args]
    if function_def.args.vararg:
        args.append(function_def.args.vararg.arg)
    if function_def.args.kwarg:
        args.append(function_def.args.kwarg.arg)
    return args


def compile_module(module_path):
    logger.debug("Compiling module {p}", p=module_path)
    with open(module_path) as f:
        txt = f.read()
    return _compile_module(txt)


def _compile_module(source):
    ast_functions, ast_classes, calls = parse(source)

    nodes = ast_functions + ast_classes
    first_lines = [n.lineno for n in nodes]

    functions = []
    classes = {}

    for f in ast_functions:
        functions.append(Function.from_ast(f, first_lines))

    for cls in ast_classes:
        methods = []

        for f in functions_of(cls):
            methods.append(Function.from_ast(f, first_lines))

        classes[cls.name] = methods

    return functions, classes, calls


def parse(module_code):
    module_ast = ast.parse(module_code)
    return functions_of(module_ast), classes_of(module_ast), get_calls(module_ast)


def base_class_names(class_):
    for base_class in class_.bases:
        if isinstance(base_class, ast.Attribute):
            yield base_class.attrname
        else:
            yield base_class.name


def find_class_with_name(name, module):
    for cls in classes_of(module):
        if cls.name == name:
            return cls
    return None


def classes_with_base_class(module, base_class):
    return [class_ for class_ in classes_of(module) if base_class in base_class_names(class_)]


def _filter_type(l, t):
    return [node for node in l if isinstance(node, t)]


def classes_of(module):
    return _filter_type(module.body, ast.ClassDef)


def functions_of(module_or_class):
    return _filter_type(module_or_class.body, ast.FunctionDef)


def function_name(function_node):
    function_parent = function_node.parent
    parent_name = str(function_parent.name)
    return parent_name + "." + function_node.name


def _clean_function_node(func: ast.FunctionDef):
    func.decorator_list = []
    func.returns = None
    func.args.defaults = []
    func.args = RemoveAnnotations().visit(func.args)
    ast.fix_missing_locations(func.args)
    return func


class RemoveAnnotations(ast.NodeTransformer):

    def visit(self, node):
        if isinstance(node, ast.Name):
            return ast.Name(id='str', ctx=ast.Load())
        if hasattr(node, "annotation"):
            node.annotation = None
        self.generic_visit(node)
        return node


def resolve_function_name(node):
    if type(node) == ast.Name:
        return node.id
    elif type(node) == ast.Attribute:
        # Recursion on series of calls to attributes.
        func_name = resolve_function_name(node.value)
        func_name += "." + node.attr
        return func_name
    elif type(node) == ast.Str:
        return node.s
    elif type(node) == ast.Subscript:
        return node.value.id
    else:
        raise ValueError("Unexpected node type {}".format(ast.dump(node)))


def get_calls(node, call_number=0):
    calls = []
    successors_in_order = []
    if type(node) == ast.Call:
        call_node = node
        try:
            function_name = resolve_function_name(call_node.func)
            call_entry = (call_node.lineno, call_number, function_name)
            calls.append(call_entry)
            call_number += 1
        except:
            # well that's buggy,
            # but those calls that fail to have their name resolved
            # are not interesting for us anyway
            pass

        # resolve call order, reversing means last call child comes first,
        # this means that it will get smaller call number
        # nodes with higher call number are called before the ones with smaller call number
        successors_in_order = reversed(list(ast.iter_child_nodes(call_node)))
    elif type(node) == ast.BoolOp:
        bool_op_node = node
        successors_in_order = reversed(list(ast.iter_child_nodes(bool_op_node)))
    else:
        successors_in_order = ast.iter_child_nodes(node)
    for some_child in successors_in_order:
        new_calls = get_calls(some_child, call_number)
        calls.extend(new_calls)
        call_number += len(calls)
    return calls


def get_function_sources(fname, source):
    atok = asttokens.ASTTokens(source, parse=True, filename=fname)
    atok.mark_tokens(atok.tree)
    res = []
    for node in ast.walk(atok.tree):
        if isinstance(node, ast.FunctionDef):
            deindented_text = textwrap.dedent(atok.get_text(node))
            res.append((node.lineno, deindented_text))
    return res
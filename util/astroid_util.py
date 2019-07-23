import ast


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
    return parent_name+"."+function_node.name

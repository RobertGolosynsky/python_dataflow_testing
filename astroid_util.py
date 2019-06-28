import astroid


def parse(module_code):
    module_ast = astroid.parse(module_code)
    return functions_of(module_ast), classes_of(module_ast), imports_of(module_ast)


def base_class_names(class_):
    for base_class in class_.bases:
        if isinstance(base_class, astroid.Attribute):
            yield base_class.attrname
        else:
            yield base_class.name


def classes_with_base_class(module, base_class):
    for class_ in classes_of(module):
        if base_class in base_class_names(class_):
            yield class_


def _filter_type(l, t):
    return [node for node in l if isinstance(node, t)]


def classes_of(module):
    return _filter_type(module.body, astroid.ClassDef)


def functions_of(module):
    return _filter_type(module.body, astroid.FunctionDef)


def imports_of(module):
    return _filter_type(module.body, astroid.Import) + _filter_type(module.body, astroid.ImportFrom)

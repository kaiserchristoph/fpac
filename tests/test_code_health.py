import ast
import pytest
import os

def test_no_imports_in_functions_app_py():
    """
    Strictly enforce that no Python imports occur inside function definitions within `app.py`.
    """
    filepath = 'app.py'
    assert os.path.exists(filepath), f"{filepath} does not exist"

    with open(filepath, 'r') as f:
        tree = ast.parse(f.read(), filename=filepath)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in ast.walk(node):
                if isinstance(child, (ast.Import, ast.ImportFrom)):
                    pytest.fail(f"Import found inside function '{node.name}' at line {child.lineno} in {filepath}")

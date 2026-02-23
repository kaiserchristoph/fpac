import ast
import os

def check_file(filepath):
    with open(filepath, 'r') as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            return

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in node.body:
                if isinstance(child, (ast.Import, ast.ImportFrom)):
                    print(f"{filepath}:{child.lineno} Import inside function '{node.name}'")

for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.py') and 'venv' not in root:
            check_file(os.path.join(root, file))

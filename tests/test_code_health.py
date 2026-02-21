import unittest
import ast
import os

class CodeHealthTestCase(unittest.TestCase):
    def test_no_imports_inside_functions_in_app(self):
        """
        Ensure that there are no import statements inside function definitions in app.py.
        This enforces the code health rule that imports should be at the top level.
        """
        # Determine the path to app.py relative to this test file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filename = os.path.join(base_dir, 'app.py')

        if not os.path.exists(filename):
            self.skipTest(f"{filename} not found")

        with open(filename, 'r') as f:
            tree = ast.parse(f.read())

        class ContextAwareVisitor(ast.NodeVisitor):
            def __init__(self):
                self.in_function = False
                self.errors = []

            def visit_FunctionDef(self, node):
                # Save previous state
                outer_in_function = self.in_function
                # Enter function scope
                self.in_function = True
                self.generic_visit(node)
                # Restore previous state
                self.in_function = outer_in_function

            def visit_AsyncFunctionDef(self, node):
                # Same for async functions
                outer_in_function = self.in_function
                self.in_function = True
                self.generic_visit(node)
                self.in_function = outer_in_function

            def visit_Import(self, node):
                if self.in_function:
                    self.errors.append(f"Line {node.lineno}: import statement found inside a function")
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                if self.in_function:
                    self.errors.append(f"Line {node.lineno}: from ... import statement found inside a function")
                self.generic_visit(node)

        visitor = ContextAwareVisitor()
        visitor.visit(tree)

        if visitor.errors:
            self.fail("\n".join(visitor.errors))

if __name__ == '__main__':
    unittest.main()

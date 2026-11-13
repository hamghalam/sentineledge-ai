import ast
import operator


class CalculatorTool:
    """
    Safely evaluates basic arithmetic expressions.
    Does not use eval() or execute arbitrary Python code.
    """

    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def calculate(self, expression: str):
        if len(expression) > 100:
            raise ValueError("Expression is too long.")

        tree = ast.parse(expression, mode="eval")

        return self._evaluate(tree.body)

    def _evaluate(self, node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)) and not isinstance(
                node.value, bool
            ):
                return node.value
            raise ValueError("Only numeric values are allowed.")

        if isinstance(node, ast.BinOp):
            operation = self.OPERATORS.get(type(node.op))

            if operation is None:
                raise ValueError("Operator is not supported.")

            left = self._evaluate(node.left)
            right = self._evaluate(node.right)

            if isinstance(node.op, ast.Pow) and abs(right) > 10:
                raise ValueError("Exponent is too large.")

            result = operation(left, right)

            if isinstance(result, (int, float)) and abs(result) > 1e100:
                raise ValueError("Result is too large.")

            return result

        if isinstance(node, ast.UnaryOp):
            operation = self.OPERATORS.get(type(node.op))

            if operation is None:
                raise ValueError("Operator is not supported.")

            return operation(self._evaluate(node.operand))

        raise ValueError("Expression contains unsupported syntax.")
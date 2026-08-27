import re
import ast
import operator
from utils.logger import log


class CalculatorModule:
    """Einfacher Taschenrechner fuer mathematische Ausdruecke."""

    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }

    def calculate(self, expression: str) -> str:
        """Berechnet einen mathematischen Ausdruck sicher."""
        expression = expression.strip()
        expression = expression.replace("hoch", "**")
        expression = expression.replace("mal", "*").replace("geteilt", "/")
        expression = expression.replace("plus", "+").replace("minus", "-")
        expression = re.sub(r"[^\d\+\-\*\/\%\.\(\)\s]", "", expression).strip()

        if not expression:
            return "Der Ausdruck ist ungueltig."

        try:
            result = self._safe_eval(expression)
            if isinstance(result, float) and result == int(result) and abs(result) < 1e15:
                result = int(result)
            log.info(f"Berechnung: {expression} = {result}")
            return f"Das Ergebnis ist: {result}"
        except ZeroDivisionError:
            return "Fehler: Division durch Null ist nicht erlaubt."
        except Exception as e:
            log.error(f"Berechnungsfehler: {e}")
            return f"Den Ausdruck '{expression}' konnte ich nicht berechnen."

    def _safe_eval(self, expression: str) -> float:
        """Sichere Auswertung eines mathematischen Ausdrucks."""
        tree = ast.parse(expression, mode="eval")
        return self._eval_node(tree.body)

    def _eval_node(self, node) -> float:
        """Rekursive Auswertung eines AST-Knotens."""
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_type = type(node.op)
            if op_type not in self.OPERATORS:
                raise ValueError(f"Unbekannter Operator: {op_type.__name__}")
            return self.OPERATORS[op_type](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op_type = type(node.op)
            if op_type not in self.OPERATORS:
                raise ValueError(f"Unbekannter Operator: {op_type.__name__}")
            return self.OPERATORS[op_type](operand)
        else:
            raise ValueError(f"Unbekannter Ausdruck: {ast.dump(node)}")

"""Tool: calculadora aritmética segura.

Avalia expressões matemáticas básicas (+, -, *, /, **, parênteses).
Usada principalmente pelo EducIAção em exemplos de matemática.
"""
import ast
import operator

# Operadores permitidos
_OPS: dict = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(node: ast.AST) -> float:
    """Avalia AST de forma segura, sem chamar eval() bruto."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _OPS:
            raise ValueError(f"Operador {op_type.__name__} não permitido")
        return _OPS[op_type](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _OPS:
            raise ValueError(f"Operador unário {op_type.__name__} não permitido")
        return _OPS[op_type](_safe_eval(node.operand))
    raise ValueError(f"Nó AST não permitido: {type(node).__name__}")


def run_calculator(expression: str) -> str:
    """Avalia uma expressão matemática e retorna string formatada."""
    try:
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval(tree.body)
        # Formato: inteiro se possível, senão float com 6 casas
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        elif isinstance(result, float):
            result = round(result, 6)
        return f"{expression} = {result}"
    except (SyntaxError, ValueError, ZeroDivisionError) as exc:
        return f"ERRO ao calcular '{expression}': {exc}"


calculator_tool: dict = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": (
            "Avalia uma expressão matemática (números, +, -, *, /, **, parênteses). "
            "Use SEMPRE que precisar fazer conta exata. Não invente resultados."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": (
                        "Expressão matemática em formato Python. "
                        "Exemplos: '3/4 * 5/2', '2 ** 10', '(15 + 7) * 3'"
                    ),
                }
            },
            "required": ["expression"],
            "additionalProperties": False,
        },
    },
}

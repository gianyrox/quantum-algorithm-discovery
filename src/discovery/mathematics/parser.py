from __future__ import annotations

import re

from discovery.mathematics.schema import MathNode

_TOKEN_RE = re.compile(
    r"\\[A-Za-z]+|[A-Za-z][A-Za-z0-9_]*|\d+(?:\.\d+)?|==|<=|>=|!=|[-+*/^_=<>()[\]{},]"
)


def tokenize_latex(source: str) -> list[str]:
    return _TOKEN_RE.findall(source)


def shallow_ast(source: str) -> MathNode:
    """Transparent non-CAS expression tree used as one comparison view.

    This intentionally does not claim full LaTeX semantics. It preserves token
    order and recognizes only top-level relation/additive/multiplicative hints.
    """

    tokens = tokenize_latex(source)
    for symbol, name in (("=", "equals"), ("<=", "le"), (">=", "ge"), ("<", "lt"), (">", "gt")):
        if symbol in tokens:
            index = tokens.index(symbol)
            return MathNode(
                operator=name,
                children=[
                    MathNode(operator="sequence", value=" ".join(tokens[:index])),
                    MathNode(operator="sequence", value=" ".join(tokens[index + 1 :])),
                ],
            )
    return MathNode(operator="sequence", value=" ".join(tokens))

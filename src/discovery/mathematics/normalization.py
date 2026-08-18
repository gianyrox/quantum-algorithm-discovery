from __future__ import annotations

import re

_SYMBOL = re.compile(r"\\?[A-Za-z]+")


def alpha_normalize_latex(latex: str) -> str:
    """Very conservative lexical alpha-normalization baseline.

    This is not semantic math parsing. It exists only as a transparent baseline
    until a real parser/AST pipeline is connected.
    """
    mapping: dict[str, str] = {}
    counter = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal counter
        token = match.group(0)
        if token.startswith("\\"):
            return token
        if token not in mapping:
            counter += 1
            mapping[token] = f"v{counter}"
        return mapping[token]

    return _SYMBOL.sub(replace, latex)

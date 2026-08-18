from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field

from discovery.mathematics.normalization import alpha_normalize_latex

_COMMAND_RE = re.compile(r"\\([A-Za-z]+)")
_SYMBOL_RE = re.compile(r"(?<!\\)\b[A-Za-z]\b")

_OPERATOR_HINTS: dict[str, tuple[str, ...]] = {
    "sum": ("\\sum",),
    "product": ("\\prod",),
    "integral": ("\\int", "\\oint"),
    "derivative": ("\\partial", "\\frac{d", "\\nabla"),
    "expectation": ("\\mathbb{E}", "\\operatorname{E}"),
    "norm": ("\\lVert", "\\|"),
    "inner_product": ("\\langle",),
    "matrix": ("\\begin{matrix}", "\\begin{bmatrix}", "\\begin{pmatrix}"),
    "tensor_product": ("\\otimes",),
    "commutator": (r"[", r"]"),
    "eigenproblem": ("\\lambda",),
}


class MathFeatureSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alpha_normalized: str | None = None
    commands: list[str] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=list)
    operators: list[str] = Field(default_factory=list)
    has_equality: bool = False
    has_inequality: bool = False
    has_probability: bool = False
    has_matrix_like_structure: bool = False


def extract_math_features(latex: str | None, mathml: str | None = None) -> MathFeatureSet:
    source = latex or mathml or ""
    commands = sorted(set(_COMMAND_RE.findall(source)))
    symbols = sorted(set(_SYMBOL_RE.findall(source)))
    operators: list[str] = []
    for name, hints in _OPERATOR_HINTS.items():
        if any(hint in source for hint in hints):
            operators.append(name)
    lowered = source.casefold()
    return MathFeatureSet(
        alpha_normalized=alpha_normalize_latex(latex) if latex else None,
        commands=commands,
        symbols=symbols,
        operators=sorted(set(operators)),
        has_equality="=" in source,
        has_inequality=any(token in source for token in ("<", ">", "\\le", "\\ge")),
        has_probability=any(token in lowered for token in ("prob", "\\mathbb{p}", "expect")),
        has_matrix_like_structure=any(name in operators for name in ("matrix", "tensor_product")),
    )

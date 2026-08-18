from __future__ import annotations

import hashlib
import re
from collections import Counter

from pydantic import BaseModel, ConfigDict, Field

from discovery.mathematics.features import MathFeatureSet, extract_math_features
from discovery.mathematics.normalization import alpha_normalize_latex
from discovery.mathematics.parser import shallow_ast, tokenize_latex
from discovery.mathematics.schema import MathExpression, MathNode


class MathematicalFingerprint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expression_id: str
    exact_sha256: str
    alpha_sha256: str | None = None
    token_multiset: dict[str, int] = Field(default_factory=dict)
    operator_signature: list[str] = Field(default_factory=list)
    relation_type: str | None = None
    tree_depth: int = Field(default=1, ge=1)
    features: MathFeatureSet


def _depth(node: MathNode) -> int:
    if not node.children:
        return 1
    return 1 + max(_depth(child) for child in node.children)


def _relation(node: MathNode) -> str | None:
    return node.operator if node.operator in {"equals", "le", "ge", "lt", "gt"} else None


def fingerprint_expression(expression: MathExpression) -> MathematicalFingerprint:
    source = expression.latex or expression.raw_source or expression.presentation_mathml or ""
    normalized = re.sub(r"\s+", " ", source).strip()
    alpha = expression.alpha_normalized
    if alpha is None and expression.latex:
        alpha = alpha_normalize_latex(expression.latex)
    ast = expression.ast or shallow_ast(source)
    tokens = tokenize_latex(source)
    features = extract_math_features(expression.latex, expression.presentation_mathml)
    return MathematicalFingerprint(
        expression_id=expression.id,
        exact_sha256=hashlib.sha256(normalized.encode()).hexdigest(),
        alpha_sha256=hashlib.sha256(alpha.encode()).hexdigest() if alpha else None,
        token_multiset=dict(sorted(Counter(tokens).items())),
        operator_signature=features.operators,
        relation_type=_relation(ast),
        tree_depth=_depth(ast),
        features=features,
    )

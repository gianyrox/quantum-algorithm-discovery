from discovery.mathematics.schema import MathExpression
from discovery.mathematics.similarity import compare_fingerprints
from discovery.mathematics.structural import fingerprint_expression


def test_alpha_equivalent_math_fingerprints() -> None:
    left = fingerprint_expression(MathExpression(id="a", work_id="w", latex="x + y = z"))
    right = fingerprint_expression(MathExpression(id="b", work_id="w", latex="a + b = c"))
    similarity = compare_fingerprints(left, right)
    assert left.relation_type == "equals"
    assert right.relation_type == "equals"
    assert similarity.relation_match == 1.0
    assert similarity.structural_score > 0.0


def test_exact_math_match_is_high() -> None:
    left = fingerprint_expression(MathExpression(id="a", work_id="w", latex=r"\sum_i x_i = 1"))
    right = fingerprint_expression(MathExpression(id="b", work_id="w", latex=r"\sum_i x_i = 1"))
    similarity = compare_fingerprints(left, right)
    assert similarity.exact == 1.0
    assert similarity.structural_score >= 0.75

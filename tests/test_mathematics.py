from __future__ import annotations

from discovery.mathematics.normalization import alpha_normalize_latex


def test_alpha_normalization_is_reproducible() -> None:
    assert alpha_normalize_latex("A x = lambda x") == "v1 v2 = v3 v2"

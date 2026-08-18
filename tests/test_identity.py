from discovery.corpus.identity import exact_identity_evidence, possible_identity_evidence
from discovery.corpus.schema import IdentifierScheme, Work


def test_exact_identity_uses_normalized_doi() -> None:
    left = Work.from_primary_identifier(scheme=IdentifierScheme.DOI, value="10.1/ABC", title="A")
    right = Work.from_primary_identifier(
        scheme=IdentifierScheme.DOI,
        value="https://doi.org/10.1/abc",
        title="B",
    )
    evidence = exact_identity_evidence(left, right)
    assert evidence is not None
    assert evidence.relation == "same_work"


def test_title_similarity_never_auto_promotes() -> None:
    left = Work(id="a", title="Sparse spectral estimation in networks", publication_year=2020)
    right = Work(id="b", title="Sparse spectral estimation in networks", publication_year=2020)
    evidence = possible_identity_evidence(left, right)
    assert evidence is not None
    assert evidence.relation == "possible_same_work"

from discovery.documents.intelligence import analyze_document
from discovery.documents.references import infer_reference_identifiers
from discovery.documents.schema import (
    DocumentSection,
    EquationOccurrence,
    ParsedDocument,
    ReferenceOccurrence,
)


def test_document_intelligence_preserves_structure() -> None:
    document = ParsedDocument(
        work_id="w1",
        asset_id="a1",
        source_format="tex",
        parser="test",
        sections=[
            DocumentSection(
                id="s1", title="Problem", order=0, text="We solve an optimization problem."
            ),
            DocumentSection(
                id="s2",
                title="Method",
                order=1,
                text="Our algorithm uses a numerical solver.",
            ),
        ],
        equations=[
            EquationOccurrence(id="e1", section_id="s1", latex="x=1"),
            EquationOccurrence(id="e2", section_id="s1", latex="y=2"),
        ],
        references=[ReferenceOccurrence(id="r1", order=0, raw_text="A reference")],
    )
    result = analyze_document(document)
    assert result.section_count == 2
    assert result.equation_count == 2
    assert result.reference_count == 1
    assert result.math_dense_sections == ["s1"]
    assert "s1" in result.likely_problem_sections
    assert "s2" in result.likely_method_sections


def test_reference_identifier_inference() -> None:
    ids = infer_reference_identifiers(
        "Example. doi:10.1234/ABC.123. PMID: 12345678 arXiv:2401.01234v2"
    )
    assert ids["doi"] == "10.1234/abc.123"
    assert ids["pmid"] == "12345678"
    assert ids["arxiv"] == "2401.01234v2"


def test_jats_parser_recovers_reference_identifiers() -> None:
    from discovery.documents.parsers import JATSParser

    xml = (
        b"<article><body><sec><title>Methods</title><p>We solve a problem.</p></sec></body>"
        b"<back><ref-list><ref id='r1'><mixed-citation>Doe 2020 doi:10.5555/XYZ.1"
        b"</mixed-citation></ref></ref-list></back></article>"
    )
    document = JATSParser().parse(work_id="w", asset_id="a", content=xml)
    assert len(document.references) == 1
    assert document.references[0].identifiers["doi"] == "10.5555/xyz.1"


def test_latex_parser_recovers_bibitem_reference() -> None:
    from discovery.documents.parsers import LatexParser

    tex = br"""\section{Method}We solve a problem.
    \begin{thebibliography}{9}\bibitem{a} Example doi:10.1234/TEST.2\end{thebibliography}"""
    document = LatexParser().parse(work_id="w", asset_id="a", content=tex)
    assert len(document.references) == 1
    assert document.references[0].identifiers["doi"] == "10.1234/test.2"

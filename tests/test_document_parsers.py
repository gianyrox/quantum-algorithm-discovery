from discovery.documents.parsers import JATSParser, LatexParser, PlainTextParser


def test_plain_text_parser() -> None:
    document = PlainTextParser().parse(work_id="w", asset_id="a", content=b"hello world")
    assert document.sections[0].text == "hello world"


def test_latex_parser_extracts_sections_and_equations() -> None:
    content = br"""\section{Methods}
We solve an eigenvalue problem.
\begin{equation}
A x = \lambda x
\end{equation}
"""
    document = LatexParser().parse(work_id="w", asset_id="a", content=content)
    assert document.sections[0].title == "Methods"
    assert len(document.equations) == 1
    assert "lambda" in (document.equations[0].latex or "")


def test_jats_parser_preserves_sections_and_formula() -> None:
    content = b"""<article><body><sec id='s1'><title>Methods</title><p>We simulate a system.</p>
    <disp-formula id='e1'><tex-math>A x = lambda x</tex-math></disp-formula>
    </sec></body></article>"""
    document = JATSParser().parse(work_id="w", asset_id="a", content=content)
    assert document.sections[0].title == "Methods"
    assert document.equations[0].label == "e1"

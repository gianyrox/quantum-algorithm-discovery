from discovery.documents.schema import DocumentSection, ParsedDocument
from discovery.problems.baseline_extractor import TransparentBaselineProblemExtractor
from discovery.problems.ensemble import ProblemExtractorEnsemble


def test_ensemble_records_extractor_votes() -> None:
    document = ParsedDocument(
        work_id="w",
        asset_id="a",
        source_format="txt",
        parser="test",
        sections=[DocumentSection(id="s", order=0, text="We optimize a sparse matrix objective.")],
    )
    result = ProblemExtractorEnsemble([TransparentBaselineProblemExtractor()]).extract(document)
    assert result.work_id == "w"
    assert len(result.votes) == 1
    assert result.problems


def test_baseline_extractor_emits_field_addressable_evidence() -> None:
    document = ParsedDocument(
        work_id="w",
        asset_id="a",
        source_format="txt",
        parser="test",
        sections=[DocumentSection(id="s", order=0, text="We optimize a sparse objective.")],
    )
    problems = TransparentBaselineProblemExtractor().extract(document)
    assert problems
    assert problems[0].evidence_spans
    assert problems[0].evidence_spans[0].field == "task_family"
    assert problems[0].field_confidence

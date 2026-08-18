from discovery.ontology.history import HistoricalTerm, HistoricalVocabularyIndex
from discovery.retrieval.cascade import RetrievalStage, default_high_recall_cascade


def test_historical_terms_are_release_addressable() -> None:
    index = HistoricalVocabularyIndex(
        [
            HistoricalTerm(
                concept_id="c1",
                term="old phrase",
                vocabulary="example",
                source_release="2000",
                successor=["new phrase"],
            ),
            HistoricalTerm(
                concept_id="c1",
                term="new phrase",
                vocabulary="example",
                source_release="2020",
                predecessor=["old phrase"],
            ),
        ]
    )
    assert index.releases("example") == ["2000", "2020"]
    assert index.search("old")[0].source_release == "2000"


def test_retrieval_cascade_has_historical_and_citation_stages() -> None:
    cascade = default_high_recall_cascade()
    stages = {item.stage for item in cascade.steps}
    assert RetrievalStage.HISTORICAL_TERMS in stages
    assert RetrievalStage.CITATION_EXPANSION in stages
    assert any("No quantum relevance" in note for note in cascade.notes)

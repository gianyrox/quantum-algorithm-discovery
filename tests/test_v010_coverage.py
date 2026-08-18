from discovery.coverage.active import ActiveRetrievalPlanner
from discovery.coverage.feedback import FeedbackAction, FeedbackLoop
from discovery.coverage.saturation import AuditedSaturationPolicy, DiscoveryYield
from discovery.coverage.strata import build_coverage_report


def test_stratified_coverage() -> None:
    report = build_coverage_report(
        [
            {
                "discipline": "physics",
                "year": 1995,
                "language": "en",
                "document_type": "article",
                "provider": "openalex",
                "access": "open",
            },
            {
                "discipline": "ecology",
                "year": 2024,
                "language": "en",
                "document_type": "article",
                "provider": "crossref",
                "access": "unknown",
            },
        ]
    )
    assert report.total_works == 2
    assert report.decade_counts["1990s"] == 1
    assert report.provider_counts["openalex"] == 1


def test_audited_saturation_requires_stable_strata() -> None:
    policy = AuditedSaturationPolicy(minimum_iterations=3, window=3, novelty_threshold=0.05)
    yields = [
        DiscoveryYield(iteration=i, retrieved=100, new_works=1)
        for i in range(1, 4)
    ]
    assert not policy.saturated(yields, strata_stable=False)
    assert policy.saturated(yields, strata_stable=True)


def test_feedback_prefers_unknown_vocabulary_before_saturation() -> None:
    yields = [DiscoveryYield(iteration=1, retrieved=100, new_works=30)]
    priorities = ActiveRetrievalPlanner().prioritize(
        [{"scope_id": "field-a", "uncertainty": 0.9, "coverage_gap": 0.8, "novelty": 0.6}]
    )
    decision = FeedbackLoop().decide(
        yields, priorities, strata_stable=False, unknown_terms=["new mechanism"]
    )
    assert decision.action == FeedbackAction.EXPAND_TERMS

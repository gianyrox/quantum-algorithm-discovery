from discovery.corpus.schema import Asset, IdentifierScheme, Work
from discovery.retrieval.fixture import FixtureProvider
from discovery.retrieval.harvest import HarvestPolicy, ResearchHarvestEngine
from discovery.retrieval.models import (
    AssetResponse,
    CitationEdge,
    CitationResponse,
    QueryClause,
    QueryPlan,
    RetrievalHit,
)
from discovery.retrieval.planning import batch_query_plan
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)


def test_harvest_persists_search_and_expands_fixture_edges(tmp_path) -> None:
    work = Work.from_primary_identifier(scheme=IdentifierScheme.DOI, value="10.1/a", title="A")
    hit = RetrievalHit(provider="fixture", provider_rank=1, work=work)
    refs = CitationResponse(
        identifier="10.1/a",
        direction="references",
        edges=[CitationEdge(source_id="10.1/a", target_id="10.1/b", provider="fixture")],
    )
    assets = AssetResponse(
        identifier="10.1/a",
        assets=[Asset(id="asset-1", representation="metadata", provider="fixture")],
    )
    provider = FixtureProvider(hits=[hit], references={"10.1/a": refs}, assets={"10.1/a": assets})
    engine = create_database_engine(f"sqlite:///{tmp_path / 'harvest.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    plan = QueryPlan(
        id="plan",
        name="plan",
        clauses=[QueryClause(text="spectral", source="test")],
        rendered_query="spectral",
    )
    batch = batch_query_plan(plan)
    with session_scope(factory) as session:
        result = ResearchHarvestEngine(session, provider).execute(
            batch,
            plan=plan,
            policy=HarvestPolicy(expand_references=True, discover_assets=True),
        )
        assert result.hit_count == 1
        assert result.citation_edges_seen == 1
        assert result.assets_seen == 1


def test_harvest_reuses_completed_query_checkpoint(tmp_path) -> None:
    work = Work.from_primary_identifier(scheme=IdentifierScheme.DOI, value="10.1/c", title="C")
    provider = FixtureProvider(hits=[RetrievalHit(provider="fixture", provider_rank=1, work=work)])
    engine = create_database_engine(f"sqlite:///{tmp_path / 'resume.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    plan = QueryPlan(
        id="resume-plan",
        name="resume",
        clauses=[QueryClause(text="x", source="test")],
        rendered_query="x",
    )
    batch = batch_query_plan(plan)
    with session_scope(factory) as session:
        first = ResearchHarvestEngine(session, provider).execute(batch, plan=plan)
        second = ResearchHarvestEngine(session, provider).execute(batch, plan=plan)
        assert first.unique_work_ids == second.unique_work_ids


def test_harvest_can_stop_on_audited_saturation(tmp_path) -> None:
    from discovery.retrieval.models import SearchQuery
    from discovery.retrieval.planning import QueryBatch
    from discovery.retrieval.saturation import SaturationPolicy

    work = Work.from_primary_identifier(
        scheme=IdentifierScheme.DOI, value="10.1/repeat", title="Repeated"
    )
    provider = FixtureProvider(
        hits=[RetrievalHit(provider="fixture", provider_rank=1, work=work)]
    )
    engine = create_database_engine(f"sqlite:///{tmp_path / 'saturation.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    batch = QueryBatch(
        id="saturation-batch",
        plan_id="saturation-plan",
        queries=[SearchQuery(text=f"q{i}", limit=1) for i in range(5)],
    )
    with session_scope(factory) as session:
        result = ResearchHarvestEngine(session, provider).execute(
            batch,
            policy=HarvestPolicy(
                saturation=SaturationPolicy(
                    minimum_iterations=3,
                    window=2,
                    novelty_threshold=0.0,
                )
            ),
        )
    assert result.stopped_for_saturation is True
    assert result.query_count == 3
    assert result.planned_query_count == 5
    assert [item.new_unique_works for item in result.saturation_observations] == [1, 0, 0]

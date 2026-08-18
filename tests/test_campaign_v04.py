from __future__ import annotations

from discovery.corpus.schema import IdentifierScheme, Work
from discovery.execution.campaign import CampaignService
from discovery.execution.schema import CampaignConfig, CampaignScope
from discovery.retrieval.fixture import FixtureProvider
from discovery.retrieval.models import RetrievalHit
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)
from discovery.storage.models import CampaignRunRow, ResearchCampaignRow, WorkRow


def test_raw_query_campaign_persists_intent_run_and_canonical_work(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'campaign.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    work = Work.from_primary_identifier(
        scheme=IdentifierScheme.DOI,
        value="10.1000/campaign",
        title="Campaign work",
    )
    provider = FixtureProvider(
        hits=[RetrievalHit(provider="fixture", provider_rank=1, work=work)]
    )
    with session_scope(factory) as session:
        service = CampaignService(session)
        campaign = service.create(
            CampaignConfig(
                scope_type=CampaignScope.QUERY,
                scope_id="spectral optimization",
                result_limit=5,
            )
        )
        result = service.run(campaign.id, provider)
        assert result.status == "completed"
        assert result.retrieval_hits == 1
        assert session.get(ResearchCampaignRow, campaign.id) is not None
        assert session.get(CampaignRunRow, result.run_id) is not None
        assert session.query(WorkRow).count() == 1

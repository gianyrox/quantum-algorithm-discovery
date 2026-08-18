from discovery.analysis.similarity import SimilarityEvidence
from discovery.discovery.repository import DiscoveryRepository
from discovery.discovery.schema import CrossDomainCandidate
from discovery.problems.family import ProblemFamily
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)
from discovery.storage.models import CandidateRow, ProblemFamilyMemberRow, ProblemFamilyRow


def test_discovery_hypotheses_persist_idempotently(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'discovery.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    candidate = CrossDomainCandidate(
        id="candidate-1",
        problem_a_id="p1",
        problem_b_id="p2",
        field_a="ecology",
        field_b="physics",
        similarity=SimilarityEvidence(task=1.0, operator=0.8),
        candidate_score=0.7,
        evidence=["candidate only"],
    )
    family = ProblemFamily(
        id="family-1",
        name="test",
        description="candidate",
        problem_ids=["p1", "p2"],
    )
    with session_scope(factory) as session:
        repository = DiscoveryRepository(session)
        repository.upsert_candidate(candidate)
        repository.upsert_candidate(candidate)
        repository.upsert_family(family)
        repository.upsert_family(family)
        assert session.get(CandidateRow, "candidate-1") is not None
        assert session.get(ProblemFamilyRow, "family-1") is not None
        members = session.query(ProblemFamilyMemberRow).all()
        assert len(members) == 2

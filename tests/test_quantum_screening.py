from discovery.problems.enums import ExtractionMethod, TaskFamily
from discovery.problems.schema import ProblemInstance
from discovery.quantum.catalog import QuantumCatalog
from discovery.quantum.checks import CheckStatus, QuantumAdvantageChecklist
from discovery.quantum.schema import QuantumAlgorithm
from discovery.quantum.screening import QuantumScreeningService
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)


def test_quantum_checklist_unknown_is_not_pass() -> None:
    checklist = QuantumAdvantageChecklist()
    assert checklist.access_model == CheckStatus.UNKNOWN
    assert not checklist.blocking_failure


def test_quantum_screening_persists_unresolved_match(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'q.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    problem = ProblemInstance(
        id="p",
        source_work_id="w",
        natural_language_statement="Estimate an eigenvalue.",
        task_family=TaskFamily.EIGENPROBLEM,
        extraction_method=ExtractionMethod.HUMAN,
        extractor="human",
        confidence=1,
    )
    algorithm = QuantumAlgorithm(
        id="q", name="Example", family="example", problem_classes=["eigenproblem"]
    )
    catalog = QuantumCatalog(version="test", description="test", algorithms=[algorithm])
    with session_scope(factory) as session:
        result = QuantumScreeningService(session).screen([problem], catalog.algorithms)
        assert len(result.matches) == 1
        assert result.matches[0].category.value == "U_unresolved"

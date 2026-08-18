from discovery.analysis.multiview import compare_problems
from discovery.analysis.repository_v10 import StructureDiscoveryRepository
from discovery.documents.intelligence import DocumentIntelligence
from discovery.mathematics.schema import MathExpression
from discovery.mathematics.structural import fingerprint_expression
from discovery.problems.enums import ExtractionMethod, TaskFamily
from discovery.problems.quality import assess_problem_quality
from discovery.problems.schema import ProblemInstance
from discovery.reproducibility.manifest import ResearchManifest
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)


def _problem(identifier: str) -> ProblemInstance:
    return ProblemInstance(
        id=identifier,
        source_work_id=f"w-{identifier}",
        natural_language_statement="Optimize objective",
        task_family=TaskFamily.OPTIMIZATION,
        extraction_method=ExtractionMethod.HUMAN,
        extractor="test",
        confidence=1.0,
    )


def test_v010_repository_is_idempotent(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'db.sqlite'}")
    init_db(engine)
    factory = make_session_factory(engine)
    with session_scope(factory) as session:
        repo = StructureDiscoveryRepository(session)
        intelligence = DocumentIntelligence(
            work_id="w",
            section_count=0,
            equation_count=0,
            figure_count=0,
            table_count=0,
            reference_count=0,
            word_count=0,
        )
        assert repo.store_document_intelligence("d", intelligence).work_id == "w"
        problem = _problem("p")
        assert repo.store_problem_quality(assess_problem_quality(problem)).problem_id == "p"
        fp = fingerprint_expression(MathExpression(id="e", work_id="w", latex="x=y"))
        assert repo.store_math_fingerprint(fp).expression_id == "e"
        sim = compare_problems(problem, _problem("q"))
        assert repo.store_similarity(sim).aggregate_score == sim.aggregate_score
        manifest = ResearchManifest(id="m")
        assert repo.store_manifest(manifest).fingerprint == manifest.fingerprint()

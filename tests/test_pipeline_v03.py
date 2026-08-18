from discovery.pipeline.research import ScientificDiscoveryPipeline
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)


def test_pipeline_processes_latex_into_math_and_problem(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'pipe.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    content = br"""\section{Methods}
We estimate the dominant eigenvalue of a sparse matrix.
\begin{equation}A x = \lambda x\end{equation}
"""
    with session_scope(factory) as session:
        result = ScientificDiscoveryPipeline(session).process_document(
            work_id="w", asset_id="a", source_format="latex", content=content
        )
        assert result.equation_count == 1
        assert result.problem_ids

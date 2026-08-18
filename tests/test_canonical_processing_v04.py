from __future__ import annotations

import pytest

from discovery.corpus.schema import Asset, IdentifierScheme, Work
from discovery.execution.processing import CanonicalResearchProcessor
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)
from discovery.storage.models import DocumentRow, ProblemInstanceRow, WorkRow
from discovery.storage.repositories import WorkRepository


def test_canonical_processing_requires_work_and_links_every_output(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'canonical.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    content = br"""\section{Methods}
We estimate the dominant eigenvalue of a sparse matrix.
\begin{equation}A x = \lambda x\end{equation}
"""
    asset = Asset(id="asset-canonical", provider="fixture", representation="tex")
    with session_scope(factory) as session:
        processor = CanonicalResearchProcessor(session)
        with pytest.raises(KeyError):
            processor.process_bytes(
                work_id="missing",
                asset=asset,
                source_format="latex",
                content=content,
            )
        work_id = WorkRepository(session).upsert(
            Work.from_primary_identifier(
                scheme=IdentifierScheme.DOI,
                value="10.1000/canonical",
                title="Canonical",
            )
        ).id
        result = processor.process_bytes(
            work_id=work_id,
            asset=asset,
            source_format="latex",
            content=content,
        )
        assert session.get(WorkRow, work_id) is not None
        document = session.get(DocumentRow, result.document_id)
        assert document is not None
        assert document.work_id == work_id
        problems = session.query(ProblemInstanceRow).filter_by(source_work_id=work_id).all()
        assert problems
        assert result.equation_count == 1

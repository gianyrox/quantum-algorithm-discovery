from __future__ import annotations

import json

from discovery.corpus.schema import IdentifierScheme, Work
from discovery.execution.corpus_io import CorpusExporter
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)
from discovery.storage.repositories import WorkRepository


def test_corpus_export_is_deterministic_jsonl_snapshot(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'export.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    output = tmp_path / "corpus.jsonl"
    with session_scope(factory) as session:
        WorkRepository(session).upsert(
            Work.from_primary_identifier(
                scheme=IdentifierScheme.DOI,
                value="10.1000/export",
                title="Export",
            )
        )
        summary = CorpusExporter(session).export(output)
        assert summary.works == 1
        assert summary.identifiers == 1
    records = [json.loads(line) for line in output.read_text().splitlines()]
    assert records[0]["type"] == "work"
    assert records[1]["type"] == "identifier"

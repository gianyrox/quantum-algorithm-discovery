from discovery.documents.parsers import PlainTextParser
from discovery.ontology.gaps import UnknownVocabularyMiner
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)


def test_unknown_vocabulary_miner_finds_repeated_corpus_language(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'vocab.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    docs = [
        PlainTextParser().parse(
            work_id=f"w{i}",
            asset_id=f"a{i}",
            content=b"hypergraph diffusion motif",
        )
        for i in range(2)
    ]
    with session_scope(factory) as session:
        candidates = UnknownVocabularyMiner(session).mine(docs, minimum_document_frequency=2)
        assert any(item.term == "hypergraph" for item in candidates)

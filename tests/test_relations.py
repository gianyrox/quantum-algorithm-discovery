from discovery.corpus.relations import ResearchObjectRelation, ResearchObjectRelationRepository
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)


def test_provider_native_relation_is_preserved(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'relations.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    relation = ResearchObjectRelation(
        subject_type="work",
        subject_id="w",
        relation_type="is_supplemented_by",
        native_relation_type="IsSupplementedBy",
        object_type="dataset",
        object_id="d",
        provider="datacite",
    )
    with session_scope(factory) as session:
        row = ResearchObjectRelationRepository(session).upsert(relation)
        assert row.native_relation_type == "IsSupplementedBy"

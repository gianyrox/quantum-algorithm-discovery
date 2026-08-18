from discovery.ontology.native import NativeVocabularyImporter, parse_obo, parse_skos_rdfxml
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)
from discovery.storage.models import ConceptRelationRow, ConceptRow, TermRow


def test_native_obo_import_preserves_broader_and_release(tmp_path) -> None:
    path = tmp_path / "tiny.obo"
    path.write_text(
        """format-version: 1.2

[Term]
id: TEST:1
name: Parent

[Term]
id: TEST:2
name: Child
synonym: "Young concept" EXACT []
is_a: TEST:1 ! Parent
""",
        encoding="utf-8",
    )
    records = parse_obo(path)
    engine = create_database_engine(f"sqlite:///{tmp_path / 'native.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    with session_scope(factory) as session:
        report = NativeVocabularyImporter(session).import_records(
            records,
            source_id="test-obo",
            source_name="Test OBO",
            release="2026-01",
        )
        assert report.concepts_added == 2
        assert session.query(ConceptRow).count() == 2
        assert session.query(TermRow).filter_by(term_type="synonym").count() == 1
        relation = session.query(ConceptRelationRow).one()
        assert relation.relationship == "broader"


def test_skos_rdfxml_parser_keeps_native_relation_semantics(tmp_path) -> None:
    path = tmp_path / "tiny.rdf"
    path.write_text(
        """<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:skos="http://www.w3.org/2004/02/skos/core#">
  <skos:Concept rdf:about="urn:test:2">
    <skos:prefLabel>Child</skos:prefLabel>
    <skos:altLabel>Alternative</skos:altLabel>
    <skos:broader rdf:resource="urn:test:1"/>
  </skos:Concept>
</rdf:RDF>
""",
        encoding="utf-8",
    )
    records = parse_skos_rdfxml(path)
    assert records[0].preferred_label == "Child"
    assert records[0].broader_ids == ["urn:test:1"]

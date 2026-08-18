from __future__ import annotations

from pathlib import Path

from discovery.ontology.importer import OntologySeedImporter
from discovery.ontology.query_compiler import OntologyQueryCompiler
from discovery.ontology.service import ontology_stats
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)


def _seed(path: Path) -> None:
    path.mkdir()
    (path / "DISCIPLINES.csv").write_text(
        "discipline_id,name,parent_id,level,description\n"
        "ROOT,Science,,0,root\n"
        "D1,Physics,ROOT,1,test\n",
        encoding="utf-8",
    )
    (path / "CONCEPTS.csv").write_text(
        "concept_id,discipline_id,canonical_concept,concept_type,short_definition\n"
        "C1,D1,Rare event sampling,problem,test concept\n",
        encoding="utf-8",
    )
    (path / "TERMS.csv").write_text(
        "concept_id,term,term_type,context\n"
        "C1,rare-event simulation,synonym,field synonym\n"
        "C1,importance sampling,related,method\n",
        encoding="utf-8",
    )
    (path / "RELATIONSHIPS.csv").write_text(
        "source_concept_id,relationship,target_concept_id\n",
        encoding="utf-8",
    )
    (path / "MODELS_EQUATIONS_METHODS.csv").write_text(
        "concept_id,name,type,discipline,related_concepts\n"
        "C1,Importance sampling,method,statistics,rare event sampling\n",
        encoding="utf-8",
    )


def test_seed_import_is_idempotent_and_compiles_query(tmp_path) -> None:
    seed = tmp_path / "seed"
    _seed(seed)
    engine = create_database_engine(f"sqlite:///{tmp_path / 'test.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    with session_scope(factory) as session:
        importer = OntologySeedImporter(session)
        first = importer.import_directory(seed)
        second = importer.import_directory(seed)
        assert first.concepts == 1
        assert second.concepts == 0
        assert ontology_stats(session) == {"disciplines": 2, "concepts": 1, "terms": 2}
        plan = OntologyQueryCompiler(session).compile_concept("C1")
        assert '"Rare event sampling"' in plan.rendered_query
        assert '"rare-event simulation"' in plan.rendered_query
        assert plan.notes

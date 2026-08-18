from __future__ import annotations

from discovery.corpus.integrity import IntegrityService
from discovery.corpus.resolution import IdentityGraphService
from discovery.corpus.schema import IdentifierScheme, Work
from discovery.retrieval.gateway_models import (
    IdentityAssertion,
    IdentityResolution,
    IntegrityAssertion,
    IntegrityReport,
)
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)
from discovery.storage.models import WorkIdentifierRow
from discovery.storage.repositories import WorkRepository


def test_provider_asserted_exact_identity_can_attach_alias_but_fuzzy_cannot(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'identity.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    work = Work.from_primary_identifier(
        scheme=IdentifierScheme.DOI,
        value="10.1000/identity",
        title="Identity",
    )
    with session_scope(factory) as session:
        work_id = WorkRepository(session).upsert(work).id
        report = IdentityResolution(
            query_identifier="10.1000/identity",
            assertions=[
                IdentityAssertion(
                    source_identifier="10.1000/identity",
                    relation_type="same_work",
                    target_identifier="W123",
                    provider="openalex",
                ),
                IdentityAssertion(
                    source_identifier="10.1000/identity",
                    relation_type="possible_same_work",
                    target_identifier="2401.12345",
                    provider="fixture",
                    confidence=0.99,
                ),
            ],
        )
        result = IdentityGraphService(session).ingest(report)
        assert result.assertions_persisted == 2
        assert result.exact_aliases_attached == 1
        aliases = session.query(WorkIdentifierRow).filter_by(work_id=work_id).all()
        assert {(item.scheme, item.value) for item in aliases} >= {
            ("doi", "10.1000/identity"),
            ("openalex", "W123"),
        }
        assert all(item.value != "2401.12345" for item in aliases)


def test_integrity_absence_is_unknown_and_retraction_requires_attention(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'integrity.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    work = Work.from_primary_identifier(
        scheme=IdentifierScheme.DOI,
        value="10.1000/integrity",
        title="Integrity",
    )
    with session_scope(factory) as session:
        work_id = WorkRepository(session).upsert(work).id
        service = IntegrityService(session)
        assert service.status(work_id).state == "unknown"
        service.ingest(
            IntegrityReport(
                query_identifier="10.1000/integrity",
                assertions=[
                    IntegrityAssertion(
                        subject_identifier="10.1000/integrity",
                        relation_type="retracted_by",
                        object_identifier="10.1000/retraction",
                        provider="crossref",
                    )
                ],
            ),
            work_id=work_id,
        )
        status = service.status(work_id)
        assert status.state == "attention_required"
        assert status.assertions == 1


def test_identifier_parser_preserves_full_doi_path_and_recognizes_common_native_ids() -> None:
    from discovery.corpus.resolution import parse_identifier

    assert parse_identifier("https://doi.org/10.1000/foo/bar") == ("doi", "10.1000/foo/bar")
    assert parse_identifier("PMC12345") == ("pmcid", "PMC12345")
    assert parse_identifier("2401.12345v2") == ("arxiv", "2401.12345v2")

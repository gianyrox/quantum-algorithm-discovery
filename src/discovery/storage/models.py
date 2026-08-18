from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from discovery.storage.base import Base


class SourceRow(Base):
    __tablename__ = "source"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    source_type: Mapped[str] = mapped_column(String(100), default="unknown", nullable=False)
    status: Mapped[str] = mapped_column(String(60), default="seed", nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class SourceReleaseRow(Base):
    __tablename__ = "source_release"
    __table_args__ = (UniqueConstraint("source_id", "release", name="uq_source_release"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("source.id"), index=True)
    release: Mapped[str] = mapped_column(String(160), nullable=False)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    checksum: Mapped[str | None] = mapped_column(String(160))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class DisciplineRow(Base):
    __tablename__ = "discipline"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    name: Mapped[str] = mapped_column(String(500), index=True)
    parent_id: Mapped[str | None] = mapped_column(String(160), index=True)
    level: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str | None] = mapped_column(Text)
    source_id: Mapped[str] = mapped_column(String(160), default="ontology_v0_1")


class ConceptRow(Base):
    __tablename__ = "concept"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    discipline_id: Mapped[str | None] = mapped_column(String(160), index=True)
    canonical_concept: Mapped[str] = mapped_column(String(1000), index=True)
    concept_type: Mapped[str] = mapped_column(String(120), default="other")
    short_definition: Mapped[str | None] = mapped_column(Text)
    origin: Mapped[str] = mapped_column(String(120), default="ontology_v0_1")
    status: Mapped[str] = mapped_column(String(60), default="seed")
    confidence: Mapped[str] = mapped_column(String(60), default="scaffold")


class TermRow(Base):
    __tablename__ = "term"
    __table_args__ = (
        UniqueConstraint("concept_id", "term", "term_type", "context", name="uq_term_identity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    concept_id: Mapped[str] = mapped_column(String(160), index=True)
    term: Mapped[str] = mapped_column(String(1200), index=True)
    term_type: Mapped[str] = mapped_column(String(100), index=True)
    context: Mapped[str] = mapped_column(Text, default="")


class ConceptRelationRow(Base):
    __tablename__ = "concept_relation"
    __table_args__ = (
        UniqueConstraint(
            "source_concept_id", "relationship", "target_concept_id", name="uq_concept_relation"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_concept_id: Mapped[str] = mapped_column(String(160), index=True)
    relationship: Mapped[str] = mapped_column(String(160), index=True)
    target_concept_id: Mapped[str] = mapped_column(String(160), index=True)


class ModelMethodRow(Base):
    __tablename__ = "model_equation_method"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    concept_id: Mapped[str | None] = mapped_column(String(160), index=True)
    name: Mapped[str] = mapped_column(String(1000), index=True)
    object_type: Mapped[str] = mapped_column(String(100))
    discipline: Mapped[str | None] = mapped_column(String(500))
    related_concepts: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)


class WorkRow(Base):
    __tablename__ = "work"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[str | None] = mapped_column(Text)
    publication_year: Mapped[int | None] = mapped_column(Integer, index=True)
    work_type: Mapped[str | None] = mapped_column(String(100), index=True)
    primary_language: Mapped[str | None] = mapped_column(String(40))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class WorkVersionRow(Base):
    __tablename__ = "work_version"
    __table_args__ = (UniqueConstraint("work_id", "version_label", name="uq_work_version"),)

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    work_id: Mapped[str] = mapped_column(ForeignKey("work.id"), index=True)
    version_label: Mapped[str] = mapped_column(String(120), default="record")
    version_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    provider: Mapped[str | None] = mapped_column(String(120), index=True)
    raw_record: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class WorkIdentifierRow(Base):
    __tablename__ = "work_identifier"
    __table_args__ = (UniqueConstraint("scheme", "value", name="uq_work_identifier"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    work_id: Mapped[str] = mapped_column(ForeignKey("work.id"), index=True)
    scheme: Mapped[str] = mapped_column(String(80), index=True)
    value: Mapped[str] = mapped_column(String(800), index=True)
    version: Mapped[str | None] = mapped_column(String(80))
    canonical_url: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str | None] = mapped_column(String(120))
    raw_value: Mapped[str | None] = mapped_column(Text)


class AuthorRow(Base):
    __tablename__ = "author"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(500), index=True)
    identifiers_json: Mapped[dict[str, str]] = mapped_column(JSON, default=dict, nullable=False)


class OrganizationRow(Base):
    __tablename__ = "organization"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(500), index=True)
    identifiers_json: Mapped[dict[str, str]] = mapped_column(JSON, default=dict, nullable=False)


class AuthorshipRow(Base):
    __tablename__ = "authorship"
    __table_args__ = (UniqueConstraint("work_id", "author_id", "position", name="uq_authorship"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    work_id: Mapped[str] = mapped_column(ForeignKey("work.id"), index=True)
    author_id: Mapped[str] = mapped_column(ForeignKey("author.id"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    organization_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)


class AssetRow(Base):
    __tablename__ = "asset"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    work_id: Mapped[str] = mapped_column(ForeignKey("work.id"), index=True)
    provider: Mapped[str] = mapped_column(String(120), index=True)
    representation: Mapped[str] = mapped_column(String(120), index=True)
    url: Mapped[str | None] = mapped_column(Text)
    mime_type: Mapped[str | None] = mapped_column(String(200))
    availability: Mapped[str] = mapped_column(String(60), default="unknown")
    rights_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(200))


class CitationRow(Base):
    __tablename__ = "citation"
    __table_args__ = (
        UniqueConstraint("source_work_id", "target_work_id", "provider", name="uq_citation_edge"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_work_id: Mapped[str] = mapped_column(String(160), index=True)
    target_work_id: Mapped[str] = mapped_column(String(160), index=True)
    provider: Mapped[str] = mapped_column(String(120), index=True)
    provider_edge_id: Mapped[str | None] = mapped_column(String(300))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class RetrievalRunRow(Base):
    __tablename__ = "retrieval_run"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    provider: Mapped[str] = mapped_column(String(120), index=True)
    query_text: Mapped[str] = mapped_column(Text)
    query_plan_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    query_fingerprint: Mapped[str | None] = mapped_column(String(200), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(60), default="running")
    provider_reports_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False
    )


class RetrievalHitRow(Base):
    __tablename__ = "retrieval_hit"
    __table_args__ = (
        UniqueConstraint("retrieval_run_id", "provider", "provider_rank", name="uq_hit_rank"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    retrieval_run_id: Mapped[str] = mapped_column(ForeignKey("retrieval_run.id"), index=True)
    work_id: Mapped[str | None] = mapped_column(String(160), index=True)
    provider: Mapped[str] = mapped_column(String(120), index=True)
    provider_rank: Mapped[int] = mapped_column(Integer)
    provider_score: Mapped[float | None] = mapped_column(Float)
    fused_rank: Mapped[int | None] = mapped_column(Integer)
    raw_record: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    provenance_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class ProvenanceAssertionRow(Base):
    __tablename__ = "provenance_assertion"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    subject_type: Mapped[str] = mapped_column(String(100), index=True)
    subject_id: Mapped[str] = mapped_column(String(160), index=True)
    predicate: Mapped[str] = mapped_column(String(200), index=True)
    value_json: Mapped[Any] = mapped_column(JSON, nullable=False)
    provider: Mapped[str] = mapped_column(String(120), index=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    evidence_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class DocumentRow(Base):
    __tablename__ = "document"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    work_id: Mapped[str] = mapped_column(String(160), index=True)
    asset_id: Mapped[str] = mapped_column(String(160), index=True)
    source_format: Mapped[str] = mapped_column(String(120), index=True)
    parser: Mapped[str] = mapped_column(String(160), index=True)
    parser_version: Mapped[str | None] = mapped_column(String(120))
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class MathExpressionRow(Base):
    __tablename__ = "math_expression"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    work_id: Mapped[str] = mapped_column(String(160), index=True)
    document_id: Mapped[str | None] = mapped_column(String(160), index=True)
    equation_label: Mapped[str | None] = mapped_column(String(160))
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class EmbeddingRow(Base):
    __tablename__ = "embedding"
    __table_args__ = (
        UniqueConstraint(
            "object_type",
            "object_id",
            "provider",
            "model",
            "model_version",
            name="uq_embedding_identity",
        ),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    object_type: Mapped[str] = mapped_column(String(100), index=True)
    object_id: Mapped[str] = mapped_column(String(160), index=True)
    provider: Mapped[str] = mapped_column(String(160), index=True)
    model: Mapped[str] = mapped_column(String(300), index=True)
    model_version: Mapped[str] = mapped_column(String(160), default="unknown")
    dimensions: Mapped[int] = mapped_column(Integer)
    vector_json: Mapped[list[float]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProblemInstanceRow(Base):
    __tablename__ = "problem_instance"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    source_work_id: Mapped[str] = mapped_column(String(160), index=True)
    task_family: Mapped[str] = mapped_column(String(100), index=True)
    statement: Mapped[str] = mapped_column(Text)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    extraction_method: Mapped[str] = mapped_column(String(80))
    confidence: Mapped[float] = mapped_column(Float)
    review_status: Mapped[str] = mapped_column(String(80), index=True)


class ProblemEvidenceRow(Base):
    __tablename__ = "problem_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    problem_id: Mapped[str] = mapped_column(String(160), index=True)
    evidence_index: Mapped[int] = mapped_column(Integer)
    evidence_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class MathematicalObjectRow(Base):
    __tablename__ = "mathematical_object"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    name: Mapped[str] = mapped_column(String(1000), index=True)
    object_type: Mapped[str] = mapped_column(String(160), index=True)
    canonical_form: Mapped[str | None] = mapped_column(Text)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class ProblemMathRow(Base):
    __tablename__ = "problem_math"
    __table_args__ = (
        UniqueConstraint("problem_id", "math_object_id", "role", name="uq_problem_math"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    problem_id: Mapped[str] = mapped_column(String(160), index=True)
    math_object_id: Mapped[str] = mapped_column(String(160), index=True)
    role: Mapped[str] = mapped_column(String(160), default="unspecified")


class ScientificMethodRow(Base):
    __tablename__ = "scientific_method"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    name: Mapped[str] = mapped_column(String(1000), index=True)
    method_type: Mapped[str | None] = mapped_column(String(160), index=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class ProblemMethodRow(Base):
    __tablename__ = "problem_method"
    __table_args__ = (
        UniqueConstraint("problem_id", "method_id", "role", name="uq_problem_method"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    problem_id: Mapped[str] = mapped_column(String(160), index=True)
    method_id: Mapped[str] = mapped_column(String(160), index=True)
    role: Mapped[str] = mapped_column(String(160), default="known_method")


class SimilarityRunRow(Base):
    __tablename__ = "similarity_run"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    method: Mapped[str] = mapped_column(String(200), index=True)
    parameters_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProblemSimilarityRow(Base):
    __tablename__ = "problem_similarity"
    __table_args__ = (
        UniqueConstraint("run_id", "problem_a_id", "problem_b_id", name="uq_problem_similarity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("similarity_run.id"), index=True)
    problem_a_id: Mapped[str] = mapped_column(String(160), index=True)
    problem_b_id: Mapped[str] = mapped_column(String(160), index=True)
    score: Mapped[float] = mapped_column(Float, index=True)
    evidence_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class ProblemFamilyRow(Base):
    __tablename__ = "problem_family"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    name: Mapped[str] = mapped_column(String(500), index=True)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(80), default="candidate")
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class ProblemFamilyMemberRow(Base):
    __tablename__ = "problem_family_member"
    __table_args__ = (UniqueConstraint("family_id", "problem_id", name="uq_problem_family_member"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    family_id: Mapped[str] = mapped_column(String(160), index=True)
    problem_id: Mapped[str] = mapped_column(String(160), index=True)
    membership_score: Mapped[float | None] = mapped_column(Float)
    evidence_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class CandidateRow(Base):
    __tablename__ = "candidate"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    candidate_type: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(80), default="unreviewed", index=True)
    score: Mapped[float | None] = mapped_column(Float, index=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class CandidateEvidenceRow(Base):
    __tablename__ = "candidate_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[str] = mapped_column(String(160), index=True)
    evidence_type: Mapped[str] = mapped_column(String(120), index=True)
    evidence_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class QuantumPrimitiveRow(Base):
    __tablename__ = "quantum_primitive"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    name: Mapped[str] = mapped_column(String(500), index=True)
    family: Mapped[str | None] = mapped_column(String(200), index=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class QuantumAlgorithmRow(Base):
    __tablename__ = "quantum_algorithm"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    name: Mapped[str] = mapped_column(String(500), index=True)
    family: Mapped[str | None] = mapped_column(String(200), index=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class QuantumMatchRow(Base):
    __tablename__ = "quantum_match"
    __table_args__ = (UniqueConstraint("problem_id", "algorithm_id", name="uq_quantum_match"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    problem_id: Mapped[str] = mapped_column(String(160), index=True)
    algorithm_id: Mapped[str] = mapped_column(String(160), index=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    compatibility_score: Mapped[float] = mapped_column(Float, index=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class ExperimentRunRow(Base):
    __tablename__ = "experiment_run"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    name: Mapped[str] = mapped_column(String(500), index=True)
    experiment_type: Mapped[str] = mapped_column(String(160), index=True)
    status: Mapped[str] = mapped_column(String(80), default="running", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    config_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    metrics_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    artifacts_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class ResearchObjectRelationRow(Base):
    __tablename__ = "research_object_relation"
    __table_args__ = (
        UniqueConstraint(
            "subject_type",
            "subject_id",
            "relation_type",
            "object_type",
            "object_id",
            "provider",
            name="uq_research_object_relation",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_type: Mapped[str] = mapped_column(String(100), index=True)
    subject_id: Mapped[str] = mapped_column(String(200), index=True)
    relation_type: Mapped[str] = mapped_column(String(180), index=True)
    native_relation_type: Mapped[str | None] = mapped_column(String(300))
    object_type: Mapped[str] = mapped_column(String(100), index=True)
    object_id: Mapped[str] = mapped_column(String(200), index=True)
    provider: Mapped[str] = mapped_column(String(120), index=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class RetrievalQueryRow(Base):
    __tablename__ = "retrieval_query"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    batch_id: Mapped[str | None] = mapped_column(String(160), index=True)
    plan_id: Mapped[str | None] = mapped_column(String(160), index=True)
    query_text: Mapped[str] = mapped_column(Text)
    provider_scope_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    filters_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(80), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class HarvestCheckpointRow(Base):
    __tablename__ = "harvest_checkpoint"
    __table_args__ = (UniqueConstraint("batch_id", "query_index", name="uq_harvest_checkpoint"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[str] = mapped_column(String(160), index=True)
    query_index: Mapped[int] = mapped_column(Integer)
    query_text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(80), default="pending", index=True)
    retrieval_run_id: Mapped[str | None] = mapped_column(String(160), index=True)
    unique_work_count: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DocumentParseRunRow(Base):
    __tablename__ = "document_parse_run"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    work_id: Mapped[str] = mapped_column(String(160), index=True)
    asset_id: Mapped[str] = mapped_column(String(160), index=True)
    parser: Mapped[str] = mapped_column(String(160), index=True)
    parser_version: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(80), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    warnings_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)


class ProblemExtractionRunRow(Base):
    __tablename__ = "problem_extraction_run"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    work_id: Mapped[str] = mapped_column(String(160), index=True)
    document_id: Mapped[str | None] = mapped_column(String(160), index=True)
    extractor: Mapped[str] = mapped_column(String(200), index=True)
    extractor_version: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(80), index=True)
    problem_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)


class ReviewEventRow(Base):
    __tablename__ = "review_event"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    object_type: Mapped[str] = mapped_column(String(100), index=True)
    object_id: Mapped[str] = mapped_column(String(160), index=True)
    reviewer_id: Mapped[str] = mapped_column(String(160), index=True)
    decision: Mapped[str] = mapped_column(String(80), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class UnknownVocabularyCandidateRow(Base):
    __tablename__ = "unknown_vocabulary_candidate"
    __table_args__ = (
        UniqueConstraint("normalized_term", "corpus_scope", name="uq_unknown_vocab_candidate"),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    term: Mapped[str] = mapped_column(String(1000), index=True)
    normalized_term: Mapped[str] = mapped_column(String(1000), index=True)
    corpus_scope: Mapped[str] = mapped_column(String(200), default="default", index=True)
    frequency: Mapped[int] = mapped_column(Integer, default=0)
    document_frequency: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    status: Mapped[str] = mapped_column(String(80), default="candidate", index=True)
    evidence_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class CoverageSnapshotRow(Base):
    __tablename__ = "coverage_snapshot"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    scope: Mapped[str] = mapped_column(String(200), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metrics_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    gaps_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)


class QuantumScreeningRunRow(Base):
    __tablename__ = "quantum_screening_run"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    method: Mapped[str] = mapped_column(String(200), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    parameters_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class AlgorithmProposalRow(Base):
    __tablename__ = "algorithm_proposal"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    target_problem_family_id: Mapped[str] = mapped_column(String(160), index=True)
    status: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(String(1000))
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProposalEvaluationRow(Base):
    __tablename__ = "proposal_evaluation"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    proposal_id: Mapped[str] = mapped_column(String(160), index=True)
    evaluator: Mapped[str] = mapped_column(String(200), index=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProviderRequestRow(Base):
    __tablename__ = "provider_request"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    provider: Mapped[str] = mapped_column(String(160), index=True)
    operation: Mapped[str] = mapped_column(String(160), index=True)
    method: Mapped[str] = mapped_column(String(16))
    url_redacted: Mapped[str] = mapped_column(Text)
    request_fingerprint: Mapped[str] = mapped_column(String(200), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=1)
    status_code: Mapped[int | None] = mapped_column(Integer, index=True)
    response_sha256: Mapped[str | None] = mapped_column(String(200), index=True)
    response_object_key: Mapped[str | None] = mapped_column(Text)
    response_headers_json: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    error: Mapped[str | None] = mapped_column(Text)


class IdentityAssertionRow(Base):
    __tablename__ = "identity_assertion"
    __table_args__ = (
        UniqueConstraint(
            "source_identifier",
            "relation_type",
            "target_identifier",
            "provider",
            name="uq_identity_assertion",
        ),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    source_identifier: Mapped[str] = mapped_column(String(800), index=True)
    relation_type: Mapped[str] = mapped_column(String(120), index=True)
    target_identifier: Mapped[str] = mapped_column(String(800), index=True)
    provider: Mapped[str] = mapped_column(String(160), index=True)
    confidence: Mapped[float | None] = mapped_column(Float)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class IntegrityAssertionRow(Base):
    __tablename__ = "integrity_assertion"
    __table_args__ = (
        UniqueConstraint(
            "subject_identifier",
            "relation_type",
            "object_identifier",
            "provider",
            name="uq_integrity_assertion",
        ),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    work_id: Mapped[str | None] = mapped_column(String(160), index=True)
    subject_identifier: Mapped[str] = mapped_column(String(800), index=True)
    relation_type: Mapped[str] = mapped_column(String(120), index=True)
    object_identifier: Mapped[str | None] = mapped_column(String(800), index=True)
    provider: Mapped[str] = mapped_column(String(160), index=True)
    notice_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(80), default="asserted", index=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class ProviderSnapshotRow(Base):
    __tablename__ = "provider_snapshot"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    provider: Mapped[str] = mapped_column(String(160), index=True)
    snapshot_type: Mapped[str] = mapped_column(String(100), index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(80), default="observed", index=True)
    capabilities_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class ResearchCampaignRow(Base):
    __tablename__ = "research_campaign"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    name: Mapped[str] = mapped_column(String(500), index=True)
    scope_type: Mapped[str] = mapped_column(String(80), index=True)
    scope_id: Mapped[str] = mapped_column(String(500), index=True)
    status: Mapped[str] = mapped_column(String(80), default="planned", index=True)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CampaignRunRow(Base):
    __tablename__ = "campaign_run"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("research_campaign.id"), index=True)
    status: Mapped[str] = mapped_column(String(80), default="running", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    result_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    error: Mapped[str | None] = mapped_column(Text)


class ProcessingJobRow(Base):
    __tablename__ = "processing_job"
    __table_args__ = (
        UniqueConstraint("work_id", "asset_id", "stage", name="uq_processing_job"),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    work_id: Mapped[str] = mapped_column(String(160), index=True)
    asset_id: Mapped[str | None] = mapped_column(String(160), index=True)
    stage: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(80), default="pending", index=True)
    priority: Mapped[int] = mapped_column(Integer, default=0, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class ProviderHarvestCheckpointRow(Base):
    __tablename__ = "provider_harvest_checkpoint"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "query_fingerprint",
            "page_index",
            name="uq_provider_harvest_page",
        ),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    provider: Mapped[str] = mapped_column(String(160), index=True)
    query_fingerprint: Mapped[str] = mapped_column(String(200), index=True)
    query_text: Mapped[str] = mapped_column(Text)
    page_index: Mapped[int] = mapped_column(Integer)
    cursor_used: Mapped[str | None] = mapped_column(Text)
    next_cursor: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(80), default="pending", index=True)
    retrieval_run_id: Mapped[str | None] = mapped_column(String(160), index=True)
    retrieved_count: Mapped[int] = mapped_column(Integer, default=0)
    new_unique_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    error: Mapped[str | None] = mapped_column(Text)


class AssetAcquisitionRow(Base):
    __tablename__ = "asset_acquisition"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    work_id: Mapped[str] = mapped_column(String(160), index=True)
    asset_id: Mapped[str] = mapped_column(String(160), index=True)
    status: Mapped[str] = mapped_column(String(80), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stored_object_key: Mapped[str | None] = mapped_column(Text)
    sha256: Mapped[str | None] = mapped_column(String(200), index=True)
    parser_format: Mapped[str | None] = mapped_column(String(100))
    error: Mapped[str | None] = mapped_column(Text)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class DocumentIntelligenceRow(Base):
    __tablename__ = "document_intelligence"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    work_id: Mapped[str] = mapped_column(String(160), index=True)
    document_id: Mapped[str] = mapped_column(String(160), index=True)
    analyzer: Mapped[str] = mapped_column(String(160), default="document-intelligence-v010")
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProblemQualityRow(Base):
    __tablename__ = "problem_quality"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    problem_id: Mapped[str] = mapped_column(String(160), index=True)
    evaluator: Mapped[str] = mapped_column(String(160), default="problem-quality-v010")
    completeness: Mapped[float] = mapped_column(Float)
    evidence_coverage: Mapped[float] = mapped_column(Float)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MathFingerprintRow(Base):
    __tablename__ = "math_fingerprint"
    __table_args__ = (
        UniqueConstraint("expression_id", "fingerprinter_version", name="uq_math_fingerprint"),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    expression_id: Mapped[str] = mapped_column(String(160), index=True)
    fingerprinter_version: Mapped[str] = mapped_column(String(120), default="0.10")
    exact_sha256: Mapped[str] = mapped_column(String(64), index=True)
    alpha_sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class StructuralSimilarityRow(Base):
    __tablename__ = "structural_similarity"
    __table_args__ = (
        UniqueConstraint(
            "problem_a_id",
            "problem_b_id",
            "similarity_version",
            name="uq_structural_similarity",
        ),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    problem_a_id: Mapped[str] = mapped_column(String(160), index=True)
    problem_b_id: Mapped[str] = mapped_column(String(160), index=True)
    similarity_version: Mapped[str] = mapped_column(String(120), default="0.10")
    aggregate_score: Mapped[float] = mapped_column(Float, index=True)
    structural_score: Mapped[float] = mapped_column(Float, index=True)
    independence_score: Mapped[float] = mapped_column(Float, index=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CrossDomainRelationRow(Base):
    __tablename__ = "cross_domain_relation"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    problem_a_id: Mapped[str] = mapped_column(String(160), index=True)
    problem_b_id: Mapped[str] = mapped_column(String(160), index=True)
    relation_type: Mapped[str] = mapped_column(String(120), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    review_status: Mapped[str] = mapped_column(String(80), default="unreviewed", index=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DiscoveryIterationRow(Base):
    __tablename__ = "discovery_iteration"
    __table_args__ = (
        UniqueConstraint("campaign_id", "iteration", name="uq_discovery_iteration"),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(160), index=True)
    iteration: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(80), index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    yield_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    feedback_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class RetrievalFeedbackRow(Base):
    __tablename__ = "retrieval_feedback"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(160), index=True)
    scope_id: Mapped[str | None] = mapped_column(String(500), index=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    reason: Mapped[str] = mapped_column(Text)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ResearchManifestRow(Base):
    __tablename__ = "research_manifest"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class Feed402EnvelopeRow(Base):
    """Immutable feed402 response captured at the gateway research boundary."""

    __tablename__ = "feed402_envelope"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    campaign_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("campaign_run.id"), index=True
    )
    retrieval_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("retrieval_run.id"), index=True
    )
    operation: Mapped[str] = mapped_column(String(200), index=True)
    spec: Mapped[str | None] = mapped_column(String(80), index=True)
    merchant: Mapped[str] = mapped_column(String(200), index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(240), index=True)
    query_fingerprint: Mapped[str | None] = mapped_column(String(240), index=True)
    response_sha256: Mapped[str | None] = mapped_column(String(240), index=True)
    citation_count: Mapped[int] = mapped_column(Integer, default=0)
    lineage_count: Mapped[int] = mapped_column(Integer, default=0)
    envelope_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

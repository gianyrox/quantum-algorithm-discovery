from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from discovery.analysis.multiview import MultiViewSimilarity
from discovery.analysis.relations import RelationHypothesis
from discovery.core.ids import stable_id
from discovery.documents.intelligence import DocumentIntelligence
from discovery.mathematics.structural import MathematicalFingerprint
from discovery.problems.quality import ProblemQualityReport
from discovery.reproducibility.manifest import ResearchManifest
from discovery.storage.models import (
    CrossDomainRelationRow,
    DocumentIntelligenceRow,
    MathFingerprintRow,
    ProblemQualityRow,
    ResearchManifestRow,
    StructuralSimilarityRow,
)


class StructureDiscoveryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def store_document_intelligence(
        self, document_id: str, intelligence: DocumentIntelligence
    ) -> DocumentIntelligenceRow:
        row_id = stable_id("document-intelligence", f"{document_id}:v010")
        row = self.session.get(DocumentIntelligenceRow, row_id)
        if row is None:
            row = DocumentIntelligenceRow(
                id=row_id,
                work_id=intelligence.work_id,
                document_id=document_id,
                analyzer="document-intelligence-v010",
                payload_json=intelligence.model_dump(mode="json"),
                created_at=datetime.now(UTC),
            )
            self.session.add(row)
            self.session.flush()
        return row

    def store_problem_quality(self, report: ProblemQualityReport) -> ProblemQualityRow:
        row_id = stable_id("problem-quality", f"{report.problem_id}:v010")
        row = self.session.get(ProblemQualityRow, row_id)
        if row is None:
            row = ProblemQualityRow(
                id=row_id,
                problem_id=report.problem_id,
                evaluator="problem-quality-v010",
                completeness=report.completeness,
                evidence_coverage=report.evidence_coverage,
                payload_json=report.model_dump(mode="json"),
                created_at=datetime.now(UTC),
            )
            self.session.add(row)
            self.session.flush()
        return row

    def store_math_fingerprint(
        self, fingerprint: MathematicalFingerprint
    ) -> MathFingerprintRow:
        row_id = stable_id("math-fingerprint", f"{fingerprint.expression_id}:v010")
        row = self.session.get(MathFingerprintRow, row_id)
        if row is None:
            row = MathFingerprintRow(
                id=row_id,
                expression_id=fingerprint.expression_id,
                fingerprinter_version="0.10",
                exact_sha256=fingerprint.exact_sha256,
                alpha_sha256=fingerprint.alpha_sha256,
                payload_json=fingerprint.model_dump(mode="json"),
                created_at=datetime.now(UTC),
            )
            self.session.add(row)
            self.session.flush()
        return row

    def store_similarity(self, similarity: MultiViewSimilarity) -> StructuralSimilarityRow:
        left, right = sorted((similarity.problem_a_id, similarity.problem_b_id))
        row_id = stable_id("structural-similarity", f"{left}:{right}:v010")
        row = self.session.get(StructuralSimilarityRow, row_id)
        if row is None:
            row = StructuralSimilarityRow(
                id=row_id,
                problem_a_id=left,
                problem_b_id=right,
                similarity_version="0.10",
                aggregate_score=similarity.aggregate_score,
                structural_score=similarity.structural_score,
                independence_score=similarity.independence_score,
                payload_json=similarity.model_dump(mode="json"),
                created_at=datetime.now(UTC),
            )
            self.session.add(row)
            self.session.flush()
        return row

    def store_relation(self, relation: RelationHypothesis) -> CrossDomainRelationRow:
        left, right = sorted((relation.problem_a_id, relation.problem_b_id))
        row_id = stable_id(
            "cross-domain-relation", f"{left}:{right}:{relation.relation.value}:v010"
        )
        row = self.session.get(CrossDomainRelationRow, row_id)
        if row is None:
            row = CrossDomainRelationRow(
                id=row_id,
                problem_a_id=left,
                problem_b_id=right,
                relation_type=relation.relation.value,
                confidence=relation.confidence,
                review_status="unreviewed",
                payload_json=relation.model_dump(mode="json"),
                created_at=datetime.now(UTC),
            )
            self.session.add(row)
            self.session.flush()
        return row

    def store_manifest(self, manifest: ResearchManifest) -> ResearchManifestRow:
        row = self.session.get(ResearchManifestRow, manifest.id)
        if row is None:
            row = ResearchManifestRow(
                id=manifest.id,
                fingerprint=manifest.fingerprint(),
                created_at=manifest.created_at,
                payload_json=manifest.model_dump(mode="json"),
            )
            self.session.add(row)
            self.session.flush()
        return row

from __future__ import annotations

from pydantic import BaseModel

from discovery.ai.schema import AlgorithmProposal, ProposalEvaluation
from discovery.analysis.cross_domain import CrossDomainDiscoveryCandidate
from discovery.analysis.discovery_loop import StructureDiscoveryResult
from discovery.analysis.embeddings import EmbeddingRecord
from discovery.analysis.multiview import MultiViewSimilarity, SimilarityWeights
from discovery.analysis.relations import RelationHypothesis
from discovery.analysis.similarity import SimilarityEvidence
from discovery.corpus.citations import CitationIngestReport
from discovery.corpus.integrity import WorkIntegrityStatus
from discovery.corpus.resolution import IdentityResolutionIngestReport
from discovery.coverage.active import RetrievalPriority
from discovery.coverage.feedback import FeedbackDecision
from discovery.coverage.saturation import AuditedSaturationPolicy, DiscoveryYield
from discovery.coverage.strata import CoverageStratum, StratifiedCoverageReport
from discovery.discovery.schema import CrossDomainCandidate
from discovery.documents.acquisition import AssetAcquisitionResult
from discovery.documents.ingestion import DocumentIngestionResult
from discovery.documents.intelligence import DocumentIntelligence
from discovery.documents.schema import ParsedDocument
from discovery.documents.selection import RankedAsset
from discovery.evaluation.agreement import AnnotationAgreement
from discovery.evaluation.benchmark import ProblemAnnotation, ProblemAnnotationBundle
from discovery.evaluation.completeness import ProblemCompleteness
from discovery.evaluation.corpus import BenchmarkCorpus, BenchmarkWork
from discovery.evaluation.math_similarity import MathSimilarityEvaluation, MathSimilarityExample
from discovery.evaluation.problem_extraction import ExtractionEvaluation
from discovery.evaluation.retrieval import RetrievalJudgment, RetrievalMetrics
from discovery.execution.iterations import DiscoveryIteration
from discovery.execution.processing import CanonicalProcessingResult
from discovery.execution.schema import (
    CampaignConfig,
    CampaignRunResult,
    CorpusExportSummary,
    ProcessingJob,
    QueueStats,
)
from discovery.execution.v010 import PreQuantumAnalysisResult
from discovery.execution.worker import WorkerResult
from discovery.experiments.schema import ExperimentRun
from discovery.mathematics.features import MathFeatureSet
from discovery.mathematics.schema import MathematicalStructure, MathExpression
from discovery.mathematics.similarity import MathematicalSimilarity
from discovery.mathematics.structural import MathematicalFingerprint
from discovery.observability.coverage import CoverageSnapshot
from discovery.observability.health import DoctorReport
from discovery.observability.operations import OperationalSnapshot
from discovery.ontology.feedback import VocabularyFeedback
from discovery.ontology.gaps import UnknownVocabularyCandidate
from discovery.ontology.history import HistoricalTerm
from discovery.ontology.native import NativeVocabularyImportReport, NativeVocabularyRecord
from discovery.pipeline.research import AnalysisResult, DocumentProcessingResult
from discovery.problems.ensemble import EnsembleExtractionResult
from discovery.problems.evidence import EvidenceSpan, FieldConfidence
from discovery.problems.family import ProblemFamily
from discovery.problems.quality import ProblemQualityReport
from discovery.problems.schema import ProblemInstance
from discovery.problems.signature import ProblemSignature
from discovery.quantum.catalog import QuantumCatalog
from discovery.quantum.checks import QuantumAdvantageChecklist
from discovery.quantum.schema import QuantumAlgorithm, QuantumMatch, QuantumPrimitive
from discovery.quantum.screening import QuantumScreeningResult
from discovery.reproducibility.manifest import ResearchManifest, SoftwareComponent
from discovery.retrieval.boundary import ResearchBoundaryReport
from discovery.retrieval.budget import RetrievalBudget
from discovery.retrieval.cascade import RetrievalCascade
from discovery.retrieval.coordinator import (
    MultiProviderHarvestPolicy,
    MultiProviderHarvestResult,
)
from discovery.retrieval.deep_harvest import DeepHarvestPolicy, DeepHarvestResult
from discovery.retrieval.feed402 import (
    Feed402Asset,
    Feed402Citation,
    Feed402Envelope,
    Feed402ExecutionProvenance,
    Feed402LineageEntry,
    Feed402Receipt,
    Feed402RetrievalProvenance,
    Feed402Rights,
    Feed402RightsScope,
)
from discovery.retrieval.gateway_harvest import (
    GatewayCursorHarvestPolicy,
    GatewayCursorHarvestResult,
)
from discovery.retrieval.gateway_models import (
    GatewayCoverageReport,
    GatewayHarvestPage,
    GatewaySyncProvider,
    GatewaySyncReport,
    IdentityAssertion,
    IdentityResolution,
    IntegrityAssertion,
    IntegrityReport,
)
from discovery.retrieval.harvest import HarvestPolicy, HarvestResult
from discovery.retrieval.http import HttpCallRecord, RetryPolicy
from discovery.retrieval.manifest import GatewayManifest, GatewayOperation
from discovery.retrieval.models import QueryPlan, SearchResponse
from discovery.retrieval.paging import SearchPage
from discovery.retrieval.planning import QueryBatch
from discovery.retrieval.registry import ProviderDescriptor
from discovery.retrieval.runtime import DirectProviderConfig
from discovery.retrieval.saturation import SaturationObservation, SaturationPolicy
from discovery.review.schema import ReviewEvent
from discovery.storage.object_store import StoredObject

SCHEMA_MODELS: dict[str, type[BaseModel]] = {
    "audited-saturation-policy": AuditedSaturationPolicy,
    "coverage-stratum": CoverageStratum,
    "cross-domain-discovery-candidate": CrossDomainDiscoveryCandidate,
    "discovery-iteration": DiscoveryIteration,
    "discovery-yield": DiscoveryYield,
    "document-intelligence": DocumentIntelligence,
    "ensemble-extraction-result": EnsembleExtractionResult,
    "evidence-span": EvidenceSpan,
    "extraction-evaluation": ExtractionEvaluation,
    "feedback-decision": FeedbackDecision,
    "feed402-asset": Feed402Asset,
    "feed402-citation": Feed402Citation,
    "feed402-envelope": Feed402Envelope,
    "feed402-execution-provenance": Feed402ExecutionProvenance,
    "feed402-lineage-entry": Feed402LineageEntry,
    "feed402-receipt": Feed402Receipt,
    "feed402-retrieval-provenance": Feed402RetrievalProvenance,
    "feed402-rights": Feed402Rights,
    "feed402-rights-scope": Feed402RightsScope,
    "field-confidence": FieldConfidence,
    "historical-term": HistoricalTerm,
    "math-similarity-evaluation": MathSimilarityEvaluation,
    "math-similarity-example": MathSimilarityExample,
    "mathematical-fingerprint": MathematicalFingerprint,
    "mathematical-similarity": MathematicalSimilarity,
    "multi-view-similarity": MultiViewSimilarity,
    "pre-quantum-analysis-result": PreQuantumAnalysisResult,
    "problem-quality-report": ProblemQualityReport,
    "relation-hypothesis": RelationHypothesis,
    "research-manifest": ResearchManifest,
    "research-boundary-report": ResearchBoundaryReport,
    "retrieval-budget": RetrievalBudget,
    "retrieval-cascade": RetrievalCascade,
    "retrieval-priority": RetrievalPriority,
    "similarity-weights": SimilarityWeights,
    "software-component": SoftwareComponent,
    "stratified-coverage-report": StratifiedCoverageReport,
    "structure-discovery-result": StructureDiscoveryResult,
    "vocabulary-feedback": VocabularyFeedback,
    "algorithm-proposal": AlgorithmProposal,
    "analysis-result": AnalysisResult,
    "annotation-agreement": AnnotationAgreement,
    "asset-acquisition-result": AssetAcquisitionResult,
    "benchmark-corpus": BenchmarkCorpus,
    "benchmark-work": BenchmarkWork,
    "campaign-config": CampaignConfig,
    "campaign-run-result": CampaignRunResult,
    "canonical-processing-result": CanonicalProcessingResult,
    "citation-ingest-report": CitationIngestReport,
    "corpus-export-summary": CorpusExportSummary,
    "coverage-snapshot": CoverageSnapshot,
    "cross-domain-candidate": CrossDomainCandidate,
    "deep-harvest-policy": DeepHarvestPolicy,
    "deep-harvest-result": DeepHarvestResult,
    "direct-provider-config": DirectProviderConfig,
    "document-ingestion-result": DocumentIngestionResult,
    "document-processing-result": DocumentProcessingResult,
    "doctor-report": DoctorReport,
    "embedding-record": EmbeddingRecord,
    "experiment": ExperimentRun,
    "gateway-coverage-report": GatewayCoverageReport,
    "gateway-cursor-harvest-policy": GatewayCursorHarvestPolicy,
    "gateway-cursor-harvest-result": GatewayCursorHarvestResult,
    "gateway-harvest-page": GatewayHarvestPage,
    "gateway-manifest": GatewayManifest,
    "gateway-operation": GatewayOperation,
    "gateway-sync-provider": GatewaySyncProvider,
    "gateway-sync-report": GatewaySyncReport,
    "harvest-policy": HarvestPolicy,
    "harvest-result": HarvestResult,
    "http-call-record": HttpCallRecord,
    "identity-assertion": IdentityAssertion,
    "identity-resolution": IdentityResolution,
    "identity-resolution-ingest-report": IdentityResolutionIngestReport,
    "integrity-assertion": IntegrityAssertion,
    "integrity-report": IntegrityReport,
    "math-expression": MathExpression,
    "multi-provider-harvest-policy": MultiProviderHarvestPolicy,
    "multi-provider-harvest-result": MultiProviderHarvestResult,
    "math-feature-set": MathFeatureSet,
    "mathematical-structure": MathematicalStructure,
    "native-vocabulary-import-report": NativeVocabularyImportReport,
    "native-vocabulary-record": NativeVocabularyRecord,
    "operational-snapshot": OperationalSnapshot,
    "parsed-document": ParsedDocument,
    "problem-annotation": ProblemAnnotation,
    "problem-annotation-bundle": ProblemAnnotationBundle,
    "problem-completeness": ProblemCompleteness,
    "problem-family": ProblemFamily,
    "problem-instance": ProblemInstance,
    "problem-signature": ProblemSignature,
    "processing-job": ProcessingJob,
    "proposal-evaluation": ProposalEvaluation,
    "provider-descriptor": ProviderDescriptor,
    "quantum-advantage-checklist": QuantumAdvantageChecklist,
    "quantum-algorithm": QuantumAlgorithm,
    "quantum-catalog": QuantumCatalog,
    "quantum-match": QuantumMatch,
    "quantum-primitive": QuantumPrimitive,
    "quantum-screening-result": QuantumScreeningResult,
    "query-batch": QueryBatch,
    "query-plan": QueryPlan,
    "queue-stats": QueueStats,
    "ranked-asset": RankedAsset,
    "retrieval-judgment": RetrievalJudgment,
    "retrieval-metrics": RetrievalMetrics,
    "retry-policy": RetryPolicy,
    "review-event": ReviewEvent,
    "saturation-observation": SaturationObservation,
    "saturation-policy": SaturationPolicy,
    "search-page": SearchPage,
    "search-response": SearchResponse,
    "similarity-evidence": SimilarityEvidence,
    "stored-object": StoredObject,
    "unknown-vocabulary-candidate": UnknownVocabularyCandidate,
    "work-integrity-status": WorkIntegrityStatus,
    "worker-result": WorkerResult,
}

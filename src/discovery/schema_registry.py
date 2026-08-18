from __future__ import annotations

from pydantic import BaseModel

from discovery.ai.schema import AlgorithmProposal, ProposalEvaluation
from discovery.analysis.embeddings import EmbeddingRecord
from discovery.analysis.similarity import SimilarityEvidence
from discovery.corpus.citations import CitationIngestReport
from discovery.corpus.integrity import WorkIntegrityStatus
from discovery.corpus.resolution import IdentityResolutionIngestReport
from discovery.discovery.schema import CrossDomainCandidate
from discovery.documents.acquisition import AssetAcquisitionResult
from discovery.documents.ingestion import DocumentIngestionResult
from discovery.documents.schema import ParsedDocument
from discovery.documents.selection import RankedAsset
from discovery.evaluation.agreement import AnnotationAgreement
from discovery.evaluation.benchmark import ProblemAnnotation, ProblemAnnotationBundle
from discovery.evaluation.completeness import ProblemCompleteness
from discovery.evaluation.corpus import BenchmarkCorpus, BenchmarkWork
from discovery.evaluation.retrieval import RetrievalJudgment, RetrievalMetrics
from discovery.execution.processing import CanonicalProcessingResult
from discovery.execution.schema import (
    CampaignConfig,
    CampaignRunResult,
    CorpusExportSummary,
    ProcessingJob,
    QueueStats,
)
from discovery.execution.worker import WorkerResult
from discovery.experiments.schema import ExperimentRun
from discovery.mathematics.features import MathFeatureSet
from discovery.mathematics.schema import MathematicalStructure, MathExpression
from discovery.observability.coverage import CoverageSnapshot
from discovery.observability.health import DoctorReport
from discovery.observability.operations import OperationalSnapshot
from discovery.ontology.gaps import UnknownVocabularyCandidate
from discovery.ontology.native import NativeVocabularyImportReport, NativeVocabularyRecord
from discovery.pipeline.research import AnalysisResult, DocumentProcessingResult
from discovery.problems.family import ProblemFamily
from discovery.problems.schema import ProblemInstance
from discovery.problems.signature import ProblemSignature
from discovery.quantum.catalog import QuantumCatalog
from discovery.quantum.checks import QuantumAdvantageChecklist
from discovery.quantum.schema import QuantumAlgorithm, QuantumMatch, QuantumPrimitive
from discovery.quantum.screening import QuantumScreeningResult
from discovery.retrieval.coordinator import (
    MultiProviderHarvestPolicy,
    MultiProviderHarvestResult,
)
from discovery.retrieval.deep_harvest import DeepHarvestPolicy, DeepHarvestResult
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

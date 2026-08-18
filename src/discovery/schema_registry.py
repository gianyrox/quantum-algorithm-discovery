from __future__ import annotations

from pydantic import BaseModel

from discovery.ai.schema import AlgorithmProposal, ProposalEvaluation
from discovery.analysis.embeddings import EmbeddingRecord
from discovery.analysis.similarity import SimilarityEvidence
from discovery.discovery.schema import CrossDomainCandidate
from discovery.documents.ingestion import DocumentIngestionResult
from discovery.documents.schema import ParsedDocument
from discovery.evaluation.agreement import AnnotationAgreement
from discovery.evaluation.benchmark import ProblemAnnotation, ProblemAnnotationBundle
from discovery.evaluation.completeness import ProblemCompleteness
from discovery.evaluation.corpus import BenchmarkCorpus, BenchmarkWork
from discovery.evaluation.retrieval import RetrievalJudgment, RetrievalMetrics
from discovery.experiments.schema import ExperimentRun
from discovery.mathematics.features import MathFeatureSet
from discovery.mathematics.schema import MathematicalStructure, MathExpression
from discovery.observability.coverage import CoverageSnapshot
from discovery.observability.health import DoctorReport
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
from discovery.retrieval.harvest import HarvestPolicy, HarvestResult
from discovery.retrieval.manifest import GatewayManifest, GatewayOperation
from discovery.retrieval.models import QueryPlan, SearchResponse
from discovery.retrieval.planning import QueryBatch
from discovery.retrieval.saturation import SaturationObservation, SaturationPolicy
from discovery.review.schema import ReviewEvent
from discovery.storage.object_store import StoredObject

SCHEMA_MODELS: dict[str, type[BaseModel]] = {
    "algorithm-proposal": AlgorithmProposal,
    "analysis-result": AnalysisResult,
    "annotation-agreement": AnnotationAgreement,
    "benchmark-corpus": BenchmarkCorpus,
    "benchmark-work": BenchmarkWork,
    "coverage-snapshot": CoverageSnapshot,
    "cross-domain-candidate": CrossDomainCandidate,
    "document-ingestion-result": DocumentIngestionResult,
    "document-processing-result": DocumentProcessingResult,
    "doctor-report": DoctorReport,
    "embedding-record": EmbeddingRecord,
    "experiment": ExperimentRun,
    "gateway-manifest": GatewayManifest,
    "gateway-operation": GatewayOperation,
    "harvest-policy": HarvestPolicy,
    "harvest-result": HarvestResult,
    "math-expression": MathExpression,
    "math-feature-set": MathFeatureSet,
    "mathematical-structure": MathematicalStructure,
    "native-vocabulary-import-report": NativeVocabularyImportReport,
    "native-vocabulary-record": NativeVocabularyRecord,
    "parsed-document": ParsedDocument,
    "problem-annotation": ProblemAnnotation,
    "problem-annotation-bundle": ProblemAnnotationBundle,
    "problem-completeness": ProblemCompleteness,
    "problem-family": ProblemFamily,
    "problem-instance": ProblemInstance,
    "problem-signature": ProblemSignature,
    "proposal-evaluation": ProposalEvaluation,
    "quantum-advantage-checklist": QuantumAdvantageChecklist,
    "quantum-algorithm": QuantumAlgorithm,
    "quantum-catalog": QuantumCatalog,
    "quantum-match": QuantumMatch,
    "quantum-primitive": QuantumPrimitive,
    "quantum-screening-result": QuantumScreeningResult,
    "query-batch": QueryBatch,
    "query-plan": QueryPlan,
    "retrieval-judgment": RetrievalJudgment,
    "retrieval-metrics": RetrievalMetrics,
    "review-event": ReviewEvent,
    "saturation-observation": SaturationObservation,
    "saturation-policy": SaturationPolicy,
    "stored-object": StoredObject,
    "search-response": SearchResponse,
    "similarity-evidence": SimilarityEvidence,
    "unknown-vocabulary-candidate": UnknownVocabularyCandidate,
}

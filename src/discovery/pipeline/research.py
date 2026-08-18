from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from discovery.analysis.candidates import generate_cross_domain_candidates
from discovery.analysis.engine import SimilarityEngine
from discovery.analysis.local_embeddings import HashingEmbeddingProvider
from discovery.discovery.repository import DiscoveryRepository
from discovery.discovery.schema import CrossDomainCandidate
from discovery.documents.service import DocumentService
from discovery.mathematics.service import MathematicsService
from discovery.ontology.query_compiler import OntologyQueryCompiler
from discovery.problems.baseline_extractor import TransparentBaselineProblemExtractor
from discovery.problems.schema import ProblemInstance
from discovery.problems.service import ProblemExtractionService
from discovery.quantum.catalog import QuantumCatalog
from discovery.quantum.screening import QuantumScreeningResult, QuantumScreeningService
from discovery.retrieval.harvest import HarvestPolicy, HarvestResult, ResearchHarvestEngine
from discovery.retrieval.planning import batch_query_plan
from discovery.retrieval.provider import ResearchProvider


class DocumentProcessingResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_id: str
    document_id: str
    equation_count: int = Field(ge=0)
    problem_ids: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    similarity_run_id: str
    pair_count: int = Field(ge=0)
    candidates: list[CrossDomainCandidate] = Field(default_factory=list)


class ScientificDiscoveryPipeline:
    """Composable high-level facade over the research engine.

    Each stage can still be invoked independently. This facade is for experiments
    and pilot runs, not for hiding provenance or collapsing stage boundaries.
    """

    def __init__(self, session: Session, provider: ResearchProvider | None = None) -> None:
        self.session = session
        self.provider = provider

    def retrieve_concept(
        self,
        concept_id: str,
        *,
        terms_per_query: int = 8,
        result_limit: int = 50,
        providers: list[str] | None = None,
        policy: HarvestPolicy | None = None,
    ) -> HarvestResult:
        if self.provider is None:
            raise RuntimeError("retrieval provider is not configured")
        plan = OntologyQueryCompiler(self.session).compile_concept(concept_id)
        batch = batch_query_plan(
            plan,
            terms_per_query=terms_per_query,
            result_limit=result_limit,
            providers=providers,
        )
        return ResearchHarvestEngine(self.session, self.provider).execute(
            batch,
            plan=plan,
            policy=policy,
        )

    def process_document(
        self,
        *,
        work_id: str,
        asset_id: str,
        source_format: str,
        content: bytes,
    ) -> DocumentProcessingResult:
        document_service = DocumentService(self.session)
        document = document_service.parse_bytes(
            work_id=work_id,
            asset_id=asset_id,
            source_format=source_format,
            content=content,
        )
        document_row = document_service.store(document)
        expressions = MathematicsService(self.session).from_document(
            document, document_id=document_row.id
        )
        problems = ProblemExtractionService(
            self.session, TransparentBaselineProblemExtractor()
        ).extract_and_store(document, document_id=document_row.id)
        return DocumentProcessingResult(
            work_id=work_id,
            document_id=document_row.id,
            equation_count=len(expressions),
            problem_ids=[item.id for item in problems],
        )

    def analyze(
        self,
        problems: list[ProblemInstance],
        disciplines: dict[str, str],
        *,
        embedding_dimensions: int = 256,
    ) -> AnalysisResult:
        run_id, similarities = SimilarityEngine(self.session).compare_all(
            problems,
            embedding_provider=HashingEmbeddingProvider(embedding_dimensions),
        )
        problem_map = {item.id: item for item in problems}
        candidates = generate_cross_domain_candidates(problem_map, similarities, disciplines)
        repository = DiscoveryRepository(self.session)
        for candidate in candidates:
            repository.upsert_candidate(candidate)
        return AnalysisResult(
            similarity_run_id=run_id,
            pair_count=len(similarities),
            candidates=candidates,
        )

    def screen_quantum(
        self,
        problems: list[ProblemInstance],
        catalog: QuantumCatalog,
    ) -> QuantumScreeningResult:
        return QuantumScreeningService(self.session).screen(problems, catalog.algorithms)

from __future__ import annotations

import json
from contextlib import ExitStack
from pathlib import Path
from typing import Annotated, cast

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from discovery import __version__
from discovery.analysis.engine import SimilarityEngine
from discovery.analysis.local_embeddings import HashingEmbeddingProvider
from discovery.analysis.similarity import baseline_problem_similarity
from discovery.config import Settings
from discovery.core.jsonl import read_jsonl, write_jsonl
from discovery.corpus.integrity import IntegrityService
from discovery.corpus.resolution import IdentityGraphService
from discovery.corpus.schema import Asset, Work
from discovery.documents.fetcher import RightsAwareAssetFetcher
from discovery.documents.ingestion import DocumentIngestionService
from discovery.documents.schema import ParsedDocument
from discovery.documents.service import DocumentService
from discovery.evaluation.benchmark import Annotator, ProblemAnnotation, ProblemAnnotationBundle
from discovery.evaluation.completeness import problem_completeness
from discovery.evaluation.corpus import BenchmarkCorpus, BenchmarkWork
from discovery.execution.campaign import CampaignService
from discovery.execution.corpus_io import CorpusExporter
from discovery.execution.processing import CanonicalResearchProcessor
from discovery.execution.queue import ProcessingQueue
from discovery.execution.schema import CampaignConfig, CampaignScope, ProcessingStage
from discovery.execution.worker import LocalProcessingWorker
from discovery.experiments.tracker import ExperimentTracker
from discovery.observability.coverage import CoverageService
from discovery.observability.health import DoctorReport, database_counts
from discovery.observability.operations import OperationalObservabilityService
from discovery.ontology.gaps import UnknownVocabularyMiner
from discovery.ontology.importer import OntologySeedImporter
from discovery.ontology.native import (
    NativeVocabularyImporter,
    parse_native_jsonl,
    parse_obo,
    parse_skos_rdfxml,
)
from discovery.ontology.query_compiler import OntologyQueryCompiler
from discovery.ontology.service import ontology_stats
from discovery.pipeline.research import ScientificDiscoveryPipeline
from discovery.problems.baseline_extractor import TransparentBaselineProblemExtractor
from discovery.problems.schema import ProblemInstance
from discovery.problems.service import ProblemExtractionService
from discovery.quantum.catalog import QuantumCatalog, QuantumCatalogRepository
from discovery.quantum.matching import baseline_quantum_match
from discovery.quantum.schema import QuantumAlgorithm
from discovery.quantum.screening import QuantumScreeningService
from discovery.retrieval.audit import BufferedRequestObserver
from discovery.retrieval.coordinator import DirectHarvestCoordinator, MultiProviderHarvestPolicy
from discovery.retrieval.deep_harvest import DeepHarvestEngine, DeepHarvestPolicy
from discovery.retrieval.gateway import GatewayProvider
from discovery.retrieval.gateway_harvest import (
    GatewayCursorHarvestEngine,
    GatewayCursorHarvestPolicy,
)
from discovery.retrieval.harvest import HarvestPolicy, ResearchHarvestEngine
from discovery.retrieval.models import SearchQuery
from discovery.retrieval.paging import PagedResearchProvider
from discovery.retrieval.planning import batch_query_plan
from discovery.retrieval.registry import ProviderRegistryService
from discovery.retrieval.runtime import (
    DirectProviderConfig,
    ProviderMode,
    create_direct_provider,
    create_gateway_provider,
)
from discovery.retrieval.saturation import SaturationPolicy
from discovery.retrieval.service import RetrievalService
from discovery.review.schema import ReviewDecision
from discovery.review.service import ReviewService
from discovery.schema_registry import SCHEMA_MODELS
from discovery.storage.database import (
    create_database_engine,
    database_health,
    init_db,
    make_session_factory,
    session_scope,
)
from discovery.storage.models import DocumentRow, ProblemInstanceRow, RetrievalRunRow, WorkRow
from discovery.storage.object_store import LocalContentAddressedStore
from discovery.storage.repositories import ProblemRepository, WorkRepository

app = typer.Typer(
    name="discovery",
    help="Cross-disciplinary scientific problem discovery research engine.",
    no_args_is_help=True,
)
console = Console()

db_app = typer.Typer(help="Canonical research database operations.")
ontology_app = typer.Typer(help="Ontology seed import, query planning, and vocabulary gaps.")
corpus_app = typer.Typer(help="Corpus inspection and persistence.")
retrieval_app = typer.Typer(help="Gateway retrieval, query batches, and citation expansion.")
documents_app = typer.Typer(help="Lawfully supplied document parsing and structure preservation.")
problems_app = typer.Typer(help="ProblemInstance extraction and evaluation baselines.")
analysis_app = typer.Typer(help="Structural similarity, embeddings, and discovery candidates.")
quantum_app = typer.Typer(help="Quantum target representation and structural screening.")
experiment_app = typer.Typer(help="Reproducible experiment tracking.")
benchmark_app = typer.Typer(help="Benchmark sampling and annotation workflow.")
coverage_app = typer.Typer(help="Coverage, gaps, and research observability.")
review_app = typer.Typer(help="Human review events for research objects.")
provider_app = typer.Typer(help="Gateway and direct-provider capability operations.")
campaign_app = typer.Typer(help="Durable scientific retrieval campaigns.")
queue_app = typer.Typer(help="Durable local processing queue.")

app.add_typer(db_app, name="db")
app.add_typer(ontology_app, name="ontology")
app.add_typer(corpus_app, name="corpus")
app.add_typer(retrieval_app, name="retrieval")
app.add_typer(documents_app, name="documents")
app.add_typer(problems_app, name="problems")
app.add_typer(analysis_app, name="analysis")
app.add_typer(quantum_app, name="quantum")
app.add_typer(experiment_app, name="experiment")
app.add_typer(benchmark_app, name="benchmark")
app.add_typer(coverage_app, name="coverage")
app.add_typer(review_app, name="review")
app.add_typer(provider_app, name="provider")
app.add_typer(campaign_app, name="campaign")
app.add_typer(queue_app, name="queue")


def _settings(database_url: str | None = None) -> Settings:
    settings = Settings.from_env()
    if database_url is not None:
        settings = settings.model_copy(update={"database_url": database_url})
    return settings


def _factory(
    database_url: str | None = None,
) -> tuple[Settings, Engine, sessionmaker[Session]]:
    settings = _settings(database_url)
    engine = create_database_engine(settings.database_url)
    init_db(engine)
    return settings, engine, make_session_factory(engine)



def _direct_provider_config(
    settings: Settings, providers: str | None = None
) -> DirectProviderConfig:
    selected = (
        [item.strip() for item in providers.split(",") if item.strip()]
        if providers is not None
        else settings.direct_providers
    )
    return DirectProviderConfig(
        providers=selected,
        openalex_api_key=settings.openalex_api_key,
        contact_email=settings.contact_email,
    )


def _load_problem(path: Path) -> ProblemInstance:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ProblemInstance.model_validate(payload)


def _load_document(path: Path) -> ParsedDocument:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ParsedDocument.model_validate(payload)


@app.command("doctor")
def doctor(
    gateway_url: str | None = typer.Option(None, "--gateway"),
    database_url: str | None = typer.Option(None, "--database"),
) -> None:
    """Check local engine health and, when configured, gateway manifest access."""
    settings, engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        counts = database_counts(session)
    resolved_gateway = gateway_url or settings.gateway_url
    gateway_healthy: bool | None = None
    gateway_error: str | None = None
    if resolved_gateway is not None:
        gateway = GatewayProvider(
            resolved_gateway, timeout_seconds=settings.gateway_timeout_seconds
        )
        try:
            gateway.manifest()
            gateway_healthy = True
        except Exception as exc:
            gateway_healthy = False
            gateway_error = f"{type(exc).__name__}: {exc}"
        finally:
            gateway.close()
    report = DoctorReport(
        version=__version__,
        database_healthy=database_health(engine),
        works=counts["works"],
        problems=counts["problems"],
        concepts=counts["concepts"],
        retrieval_runs=counts["retrieval_runs"],
        gateway_configured=resolved_gateway is not None,
        gateway_healthy=gateway_healthy,
        gateway_error=gateway_error,
    )
    console.print_json(report.model_dump_json(indent=2))


@app.command("validate-problem")
def validate_problem(path: Path) -> None:
    try:
        problem = _load_problem(path)
    except (json.JSONDecodeError, ValidationError) as exc:
        console.print(f"[bold red]INVALID[/bold red] {path}")
        console.print(str(exc))
        raise typer.Exit(code=1) from exc
    console.print(f"[bold green]VALID[/bold green] {problem.id}")
    console.print(f"Task family: {problem.task_family.value}")
    console.print(f"Confidence: {problem.confidence:.2f}")


@app.command("validate-benchmark")
def validate_benchmark(path: Path) -> None:
    valid = 0
    invalid = 0
    table = Table(title=f"Benchmark validation: {path.name}")
    table.add_column("Line")
    table.add_column("Status")
    table.add_column("Benchmark ID")
    table.add_column("Task")
    for line_number, record in enumerate(read_jsonl(path), start=1):
        try:
            annotation = ProblemAnnotation.model_validate(record)
        except ValidationError as exc:
            invalid += 1
            table.add_row(str(line_number), "INVALID", "-", str(exc.errors()[0].get("loc", "")))
            continue
        valid += 1
        table.add_row(
            str(line_number), "VALID", annotation.benchmark_id, annotation.problem.task_family.value
        )
    console.print(table)
    console.print(f"Valid: {valid}")
    console.print(f"Invalid: {invalid}")
    if invalid:
        raise typer.Exit(code=1)


@app.command("validate-corpus")
def validate_corpus(path: Path) -> None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        corpus = BenchmarkCorpus.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        console.print(f"[bold red]INVALID[/bold red] {path}")
        console.print(str(exc))
        raise typer.Exit(code=1) from exc
    console.print(f"[bold green]VALID[/bold green] {corpus.benchmark_name}")
    console.print(f"Version: {corpus.version}")
    console.print(f"Works: {len(corpus.works)}")
    console.print(f"Disciplines: {len({work.discipline for work in corpus.works})}")


@app.command("schema")
def print_schema(model: str) -> None:
    selected = SCHEMA_MODELS.get(model)
    if selected is None:
        choices = ", ".join(sorted(SCHEMA_MODELS))
        raise typer.BadParameter(f"unknown model {model!r}; choose one of: {choices}")
    console.print_json(json.dumps(selected.model_json_schema()))


@app.command("generate-schemas")
def generate_schemas(output_dir: Path = Path("schemas")) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, model in sorted(SCHEMA_MODELS.items()):
        path = output_dir / f"{name}.schema.json"
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    console.print(f"generated {len(SCHEMA_MODELS)} schemas in {output_dir}")


@app.command("search")
def search_concept(
    concept_id: str,
    gateway_url: str | None = typer.Option(None, "--gateway"),
    terms_per_query: int = typer.Option(8, min=1, max=50),
    limit: int = typer.Option(50, min=1, max=1000),
    database_url: str | None = typer.Option(None, "--database"),
) -> None:
    """Compile an ontology concept into a query batch, retrieve, and persist the corpus."""
    settings, _engine, factory = _factory(database_url)
    resolved_gateway = gateway_url or settings.gateway_url
    if resolved_gateway is None:
        raise typer.BadParameter("set --gateway or DISCOVERY_GATEWAY_URL")
    gateway = GatewayProvider(resolved_gateway, timeout_seconds=settings.gateway_timeout_seconds)
    try:
        with session_scope(factory) as session:
            plan = OntologyQueryCompiler(session).compile_concept(concept_id)
            batch = batch_query_plan(plan, terms_per_query=terms_per_query, result_limit=limit)
            result = ResearchHarvestEngine(session, gateway).execute(batch, plan=plan)
    finally:
        gateway.close()
    console.print_json(result.model_dump_json(indent=2))


def _load_benchmark_corpus(path: Path) -> BenchmarkCorpus:
    if not path.exists():
        return BenchmarkCorpus(
            benchmark_name="cross-disciplinary-scientific-problems",
            version="0.1",
            description="Cross-disciplinary scientific problem benchmark.",
            works=[],
        )
    return BenchmarkCorpus.model_validate_json(path.read_text(encoding="utf-8"))


@benchmark_app.command("add")
def benchmark_add(
    corpus_path: Path,
    benchmark_work_id: str = typer.Option(..., "--id"),
    title: str = typer.Option(...),
    discipline: str = typer.Option(...),
    reason: str = typer.Option(...),
    method: str = typer.Option("manual breadth-first pilot sampling"),
    doi: str | None = typer.Option(None),
    publication_year: int | None = typer.Option(None, "--year"),
) -> None:
    corpus = _load_benchmark_corpus(corpus_path)
    if any(work.benchmark_work_id == benchmark_work_id for work in corpus.works):
        raise typer.BadParameter(f"benchmark work already exists: {benchmark_work_id}")
    corpus.works.append(
        BenchmarkWork(
            benchmark_work_id=benchmark_work_id,
            title=title,
            discipline=discipline,
            publication_year=publication_year,
            doi=doi,
            selection_reason=reason,
            selection_method=method,
        )
    )
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_path.write_text(corpus.model_dump_json(indent=2) + "\n", encoding="utf-8")
    console.print(f"[green]added[/green] {benchmark_work_id}")


@benchmark_app.command("list")
def benchmark_list(corpus_path: Path) -> None:
    corpus = _load_benchmark_corpus(corpus_path)
    table = Table(title=f"{corpus.benchmark_name} v{corpus.version}")
    for name in ("ID", "Discipline", "Year", "Status", "Title"):
        table.add_column(name)
    for work in corpus.works:
        table.add_row(
            work.benchmark_work_id,
            work.discipline,
            str(work.publication_year or ""),
            work.status.value,
            work.title,
        )
    console.print(table)


@benchmark_app.command("summary")
def benchmark_summary(corpus_path: Path) -> None:
    corpus = _load_benchmark_corpus(corpus_path)
    by_discipline: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for work in corpus.works:
        by_discipline[work.discipline] = by_discipline.get(work.discipline, 0) + 1
        by_status[work.status.value] = by_status.get(work.status.value, 0) + 1
    console.print(f"Works: {len(corpus.works)}")
    console.print_json(json.dumps({"disciplines": by_discipline, "statuses": by_status}))


@benchmark_app.command("scaffold-annotation")
def benchmark_scaffold_annotation(
    corpus_path: Path,
    benchmark_work_id: str,
    output: Path,
    annotator_id: str = typer.Option("human-001", "--annotator"),
) -> None:
    corpus = _load_benchmark_corpus(corpus_path)
    work = next(
        (item for item in corpus.works if item.benchmark_work_id == benchmark_work_id), None
    )
    if work is None:
        raise typer.BadParameter(f"unknown benchmark work: {benchmark_work_id}")
    source_id = work.doi or work.arxiv_id or work.pmid or work.openalex_id or benchmark_work_id
    bundle = ProblemAnnotationBundle(
        benchmark_id=corpus.benchmark_name,
        benchmark_work_id=work.benchmark_work_id,
        discipline=work.discipline,
        subdiscipline=work.subdiscipline,
        work_id=source_id,
        work_title=work.title,
        publication_year=work.publication_year,
        annotator=Annotator(id=annotator_id),
        problems=[],
        notes="Add zero or more ProblemInstance objects after reading the work.",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(bundle.model_dump_json(indent=2) + "\n", encoding="utf-8")
    console.print(f"[green]created[/green] {output}")


@benchmark_app.command("export-annotations")
def benchmark_export_annotations(annotation_dir: Path, output: Path) -> None:
    records: list[dict[str, object]] = []
    for path in sorted(annotation_dir.glob("*.json")):
        bundle = ProblemAnnotationBundle.model_validate_json(path.read_text(encoding="utf-8"))
        records.extend(annotation.model_dump(mode="json") for annotation in bundle.annotations())
    write_jsonl(output, records)
    console.print(f"[green]exported[/green] {len(records)} annotations to {output}")


@db_app.command("init")
def db_init(database_url: str | None = typer.Option(None, "--database")) -> None:
    settings, _engine, _factory_value = _factory(database_url)
    console.print(f"[green]initialized[/green] {settings.database_url}")


@db_app.command("info")
def db_info(database_url: str | None = typer.Option(None, "--database")) -> None:
    _settings_value, engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        counts = {
            "works": int(session.scalar(select(func.count()).select_from(WorkRow)) or 0),
            "documents": int(session.scalar(select(func.count()).select_from(DocumentRow)) or 0),
            "problems": int(
                session.scalar(select(func.count()).select_from(ProblemInstanceRow)) or 0
            ),
            "retrieval_runs": int(
                session.scalar(select(func.count()).select_from(RetrievalRunRow)) or 0
            ),
        }
    console.print(f"Healthy: {database_health(engine)}")
    console.print_json(json.dumps(counts))


@ontology_app.command("import-seed")
def ontology_import_seed(
    path: Annotated[Path, typer.Argument(exists=True, file_okay=False)],
    database_url: str | None = typer.Option(None, "--database"),
) -> None:
    _settings_value, _engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        report = OntologySeedImporter(session).import_directory(path)
    console.print_json(report.model_dump_json(indent=2))


@ontology_app.command("import-native")
def ontology_import_native(
    path: Path,
    source_id: str = typer.Option(..., "--source-id"),
    source_name: str = typer.Option(..., "--source-name"),
    release: str = typer.Option(..., "--release"),
    source_format: str = typer.Option(..., "--format"),
    database_url: str | None = typer.Option(None, "--database"),
) -> None:
    """Import OBO, SKOS RDF/XML, or normalized JSONL without semantic strengthening."""
    normalized_format = source_format.casefold()
    if normalized_format == "obo":
        records = parse_obo(path)
    elif normalized_format in {"skos", "skos-rdfxml", "rdfxml"}:
        records = parse_skos_rdfxml(path)
    elif normalized_format == "jsonl":
        records = parse_native_jsonl(path)
    else:
        raise typer.BadParameter("--format must be obo, skos-rdfxml, or jsonl")
    _settings_value, _engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        report = NativeVocabularyImporter(session).import_records(
            records,
            source_id=source_id,
            source_name=source_name,
            release=release,
        )
    console.print_json(report.model_dump_json(indent=2))


@ontology_app.command("stats")
def ontology_statistics(database_url: str | None = typer.Option(None, "--database")) -> None:
    _settings_value, _engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        stats = ontology_stats(session)
    console.print_json(json.dumps(stats))


@ontology_app.command("plan")
def ontology_plan(
    concept_id: str,
    max_terms: int = typer.Option(24, min=1, max=100),
    database_url: str | None = typer.Option(None, "--database"),
) -> None:
    _settings_value, _engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        plan = OntologyQueryCompiler(session).compile_concept(concept_id, max_terms=max_terms)
    console.print_json(plan.model_dump_json(indent=2))


@ontology_app.command("unknown-vocab")
def ontology_unknown_vocab(
    document_dir: Path,
    minimum_document_frequency: int = typer.Option(2, "--min-df", min=1),
    database_url: str | None = typer.Option(None, "--database"),
) -> None:
    documents = [
        _load_document(path) for path in sorted(document_dir.glob("*.json")) if path.is_file()
    ]
    _settings_value, _engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        candidates = UnknownVocabularyMiner(session).mine(
            documents,
            minimum_document_frequency=minimum_document_frequency,
        )
    console.print_json(json.dumps([item.model_dump(mode="json") for item in candidates[:50]]))


@corpus_app.command("stats")
def corpus_stats(database_url: str | None = typer.Option(None, "--database")) -> None:
    _settings_value, _engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        works = int(session.scalar(select(func.count()).select_from(WorkRow)) or 0)
        console.print(f"Works: {works}")
        problems = int(
            session.scalar(select(func.count()).select_from(ProblemInstanceRow)) or 0
        )
        console.print(f"Problems: {problems}")


@corpus_app.command("import-work")
def corpus_import_work(
    path: Path,
    database_url: Annotated[str | None, typer.Option("--database")] = None,
) -> None:
    work = Work.model_validate_json(path.read_text(encoding="utf-8"))
    _settings_value, _engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        row = WorkRepository(session).upsert(work)
    console.print(row.id)


@corpus_app.command("add-problem")
def corpus_add_problem(
    path: Path,
    database_url: str | None = typer.Option(None, "--database"),
) -> None:
    problem = _load_problem(path)
    _settings_value, _engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        ProblemRepository(session).upsert(problem)
    console.print(f"[green]stored[/green] {problem.id}")


@retrieval_app.command("plan")
def retrieval_plan(
    concept_id: str,
    database_url: str | None = typer.Option(None, "--database"),
) -> None:
    _settings_value, _engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        plan = OntologyQueryCompiler(session).compile_concept(concept_id)
    console.print(plan.rendered_query)


@retrieval_app.command("batch")
def retrieval_batch(
    concept_id: str,
    terms_per_query: int = typer.Option(8, min=1, max=50),
    result_limit: int = typer.Option(50, min=1, max=1000),
    database_url: str | None = typer.Option(None, "--database"),
) -> None:
    _settings_value, _engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        plan = OntologyQueryCompiler(session).compile_concept(concept_id)
        batch = batch_query_plan(plan, terms_per_query=terms_per_query, result_limit=result_limit)
    console.print_json(batch.model_dump_json(indent=2))


@retrieval_app.command("manifest")
def retrieval_manifest(gateway_url: str | None = typer.Option(None, "--gateway")) -> None:
    settings = _settings()
    resolved = gateway_url or settings.gateway_url
    if resolved is None:
        raise typer.BadParameter("set --gateway or DISCOVERY_GATEWAY_URL")
    gateway = GatewayProvider(resolved, timeout_seconds=settings.gateway_timeout_seconds)
    try:
        manifest = gateway.manifest()
    finally:
        gateway.close()
    console.print_json(manifest.model_dump_json(indent=2))


@retrieval_app.command("gateway-search")
def gateway_search(
    query: str,
    gateway_url: str | None = typer.Option(None, "--gateway"),
    limit: int = typer.Option(25, min=1, max=1000),
    database_url: str | None = typer.Option(None, "--database"),
) -> None:
    settings, _engine, factory = _factory(database_url)
    resolved_gateway = gateway_url or settings.gateway_url
    if resolved_gateway is None:
        raise typer.BadParameter("set --gateway or DISCOVERY_GATEWAY_URL")
    gateway = GatewayProvider(resolved_gateway, timeout_seconds=settings.gateway_timeout_seconds)
    try:
        with session_scope(factory) as session:
            response = RetrievalService(session, gateway).execute(
                SearchQuery(text=query, limit=limit)
            )
    finally:
        gateway.close()
    console.print(f"Hits: {len(response.hits)}")
    for hit in response.hits[:20]:
        title = hit.work.title if hit.work else "<unparsed record>"
        console.print(f"{hit.provider_rank:>3} {hit.provider:<20} {title}")


@retrieval_app.command("concept")
def retrieval_concept(
    concept_id: str,
    gateway_url: str | None = typer.Option(None, "--gateway"),
    terms_per_query: int = typer.Option(8, min=1, max=50),
    result_limit: int = typer.Option(50, min=1, max=1000),
    expand_references: bool = typer.Option(False, "--references"),
    expand_cited_by: bool = typer.Option(False, "--cited-by"),
    saturation_novelty: float | None = typer.Option(
        None, "--saturation-novelty", min=0.0, max=1.0
    ),
    database_url: str | None = typer.Option(None, "--database"),
) -> None:
    settings, _engine, factory = _factory(database_url)
    resolved_gateway = gateway_url or settings.gateway_url
    if resolved_gateway is None:
        raise typer.BadParameter("set --gateway or DISCOVERY_GATEWAY_URL")
    gateway = GatewayProvider(resolved_gateway, timeout_seconds=settings.gateway_timeout_seconds)
    try:
        with session_scope(factory) as session:
            plan = OntologyQueryCompiler(session).compile_concept(concept_id)
            batch = batch_query_plan(
                plan,
                terms_per_query=terms_per_query,
                result_limit=result_limit,
            )
            result = ResearchHarvestEngine(session, gateway).execute(
                batch,
                plan=plan,
                policy=HarvestPolicy(
                    expand_references=expand_references,
                    expand_cited_by=expand_cited_by,
                    saturation=SaturationPolicy(novelty_threshold=saturation_novelty)
                    if saturation_novelty is not None
                    else None,
                ),
            )
    finally:
        gateway.close()
    console.print_json(result.model_dump_json(indent=2))


@documents_app.command("parse")
def documents_parse(
    work_id: str,
    asset_id: str,
    source_format: str,
    input_path: Path,
    output_path: Annotated[Path | None, typer.Option("--output")] = None,
    database_url: str | None = typer.Option(None, "--database"),
) -> None:
    _settings_value, _engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        document = DocumentService(session).parse_file(
            work_id=work_id,
            asset_id=asset_id,
            source_format=source_format,
            path=input_path,
        )
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(document.model_dump_json(indent=2) + "\n", encoding="utf-8")
    console.print(
        f"sections={len(document.sections)} equations={len(document.equations)} "
        f"figures={len(document.figures)} tables={len(document.tables)}"
    )


@documents_app.command("ingest")
def documents_ingest(
    work_id: str,
    asset_path: Path,
    object_store: Annotated[Path, typer.Option("--object-store")] = Path("data/objects"),
    source_format: str | None = typer.Option(None, "--format"),
    transient: bool = typer.Option(False, "--transient"),
    database_url: str | None = typer.Option(None, "--database"),
) -> None:
    """Fetch an explicitly permitted asset, optionally retain it, and parse it."""
    asset = Asset.model_validate_json(asset_path.read_text(encoding="utf-8"))
    _settings_value, _engine, factory = _factory(database_url)
    fetcher = RightsAwareAssetFetcher()
    try:
        with session_scope(factory) as session:
            result = DocumentIngestionService(
                session, fetcher, LocalContentAddressedStore(object_store)
            ).ingest_asset(
                work_id=work_id,
                asset=asset,
                source_format=source_format,
                persist_raw=not transient,
            )
    finally:
        fetcher.close()
    console.print_json(result.model_dump_json(indent=2))


@problems_app.command("extract")
def problems_extract(
    document_path: Path,
    output_path: Annotated[Path | None, typer.Option("--output")] = None,
    database_url: str | None = typer.Option(None, "--database"),
) -> None:
    document = _load_document(document_path)
    _settings_value, _engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        problems = ProblemExtractionService(
            session, TransparentBaselineProblemExtractor()
        ).extract_and_store(document)
    payload = [item.model_dump(mode="json") for item in problems]
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    console.print_json(json.dumps(payload))


@problems_app.command("completeness")
def problems_completeness(problem_path: Path) -> None:
    result = problem_completeness(_load_problem(problem_path))
    console.print_json(result.model_dump_json(indent=2))


@analysis_app.command("similarity")
def analysis_similarity(problem_a: Path, problem_b: Path) -> None:
    evidence = baseline_problem_similarity(_load_problem(problem_a), _load_problem(problem_b))
    payload = evidence.model_dump(mode="json")
    payload["structural_score"] = evidence.structural_score()
    console.print_json(json.dumps(payload))


@analysis_app.command("run")
def analysis_run(database_url: str | None = typer.Option(None, "--database")) -> None:
    _settings_value, _engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        problems = ProblemRepository(session).all()
        run_id, similarities = SimilarityEngine(session).compare_all(
            problems,
            embedding_provider=HashingEmbeddingProvider(),
        )
    console.print_json(json.dumps({"run_id": run_id, "pairs": len(similarities)}))


@quantum_app.command("match")
def quantum_match(problem_path: Path, algorithm_path: Path) -> None:
    problem = _load_problem(problem_path)
    algorithm = QuantumAlgorithm.model_validate_json(algorithm_path.read_text(encoding="utf-8"))
    match = baseline_quantum_match(problem, algorithm)
    console.print_json(match.model_dump_json(indent=2))


@quantum_app.command("catalog-import")
def quantum_catalog_import(
    catalog_path: Path,
    database_url: str | None = typer.Option(None, "--database"),
) -> None:
    catalog = QuantumCatalog.load(catalog_path)
    _settings_value, _engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        primitive_count, algorithm_count = QuantumCatalogRepository(session).import_catalog(catalog)
    console.print_json(
        json.dumps({"new_primitives": primitive_count, "new_algorithms": algorithm_count})
    )


@quantum_app.command("screen")
def quantum_screen(
    catalog_path: Path,
    database_url: str | None = typer.Option(None, "--database"),
) -> None:
    catalog = QuantumCatalog.load(catalog_path)
    _settings_value, _engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        problems = ProblemRepository(session).all()
        result = QuantumScreeningService(session).screen(problems, catalog.algorithms)
    console.print_json(result.model_dump_json(indent=2))


@experiment_app.command("start")
def experiment_start(
    name: str,
    experiment_type: str = typer.Option("manual"),
    database_url: str | None = typer.Option(None, "--database"),
) -> None:
    _settings_value, _engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        run = ExperimentTracker(session).start(name, experiment_type)
    console.print(run.id)


@coverage_app.command("snapshot")
def coverage_snapshot(database_url: str | None = typer.Option(None, "--database")) -> None:
    _settings_value, _engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        snapshot = CoverageService(session).snapshot()
    console.print_json(snapshot.model_dump_json(indent=2))


@coverage_app.command("operations")
def coverage_operations(
    database_url: Annotated[str | None, typer.Option("--database")] = None,
) -> None:
    _settings_value, _engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        snapshot = OperationalObservabilityService(session).snapshot()
    console.print_json(snapshot.model_dump_json(indent=2))


@review_app.command("record")
def review_record(
    object_type: str,
    object_id: str,
    decision: ReviewDecision,
    reviewer: str = typer.Option("human-001", "--reviewer"),
    notes: str | None = typer.Option(None),
    database_url: str | None = typer.Option(None, "--database"),
) -> None:
    _settings_value, _engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        event = ReviewService(session).record(
            object_type=object_type,
            object_id=object_id,
            reviewer_id=reviewer,
            decision=decision,
            notes=notes,
        )
    console.print_json(event.model_dump_json(indent=2))


@app.command("process-file")
def process_file(
    work_id: str,
    asset_id: str,
    source_format: str,
    input_path: Path,
    database_url: str | None = typer.Option(None, "--database"),
) -> None:
    """Parse, extract math, and run the transparent ProblemInstance baseline."""
    _settings_value, _engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        result = ScientificDiscoveryPipeline(session).process_document(
            work_id=work_id,
            asset_id=asset_id,
            source_format=source_format,
            content=input_path.read_bytes(),
        )
    console.print_json(result.model_dump_json(indent=2))


@provider_app.command("direct-search")
def provider_direct_search(
    query: str,
    providers: Annotated[str | None, typer.Option("--providers")] = None,
    limit: Annotated[int, typer.Option(min=1, max=1000)] = 25,
    database_url: Annotated[str | None, typer.Option("--database")] = None,
) -> None:
    """Search selected direct scholarly providers and persist canonical works."""
    settings, _engine, factory = _factory(database_url)
    audit = BufferedRequestObserver()
    with session_scope(factory) as session:
        config = _direct_provider_config(settings, providers)
        with create_direct_provider(config, observer=audit) as research_provider:
            response = RetrievalService(session, research_provider).execute(
                SearchQuery(text=query, limit=limit, providers=config.providers)
            )
        audit.drain(
            session,
            object_store=LocalContentAddressedStore(settings.object_store_path),
            persist_response_bodies=True,
        )
        payload = {
            "hits": len(response.hits),
            "providers": [item.model_dump(mode="json") for item in response.provider_reports],
            "work_ids": [item.work.id for item in response.hits if item.work is not None],
        }
    console.print_json(json.dumps(payload))


@provider_app.command("gateway-manifest")
def provider_gateway_manifest(
    gateway_url: Annotated[str | None, typer.Option("--gateway")] = None,
    database_url: Annotated[str | None, typer.Option("--database")] = None,
) -> None:
    settings, _engine, factory = _factory(database_url)
    resolved = gateway_url or settings.gateway_url
    if resolved is None:
        raise typer.BadParameter("set --gateway or DISCOVERY_GATEWAY_URL")
    audit = BufferedRequestObserver()
    with session_scope(factory) as session:
        with create_gateway_provider(
            resolved,
            timeout_seconds=settings.gateway_timeout_seconds,
            observer=audit,
        ) as provider:
            if not isinstance(provider, GatewayProvider):
                raise RuntimeError("gateway factory returned an unexpected provider")
            manifest = provider.manifest(refresh=True)
        audit.drain(session)
        ProviderRegistryService(session).store_gateway_manifest(manifest)
    console.print_json(manifest.model_dump_json(indent=2))


@provider_app.command("gateway-sync")
def provider_gateway_sync(
    gateway_url: Annotated[str | None, typer.Option("--gateway")] = None,
    database_url: Annotated[str | None, typer.Option("--database")] = None,
) -> None:
    settings, _engine, factory = _factory(database_url)
    resolved = gateway_url or settings.gateway_url
    if resolved is None:
        raise typer.BadParameter("set --gateway or DISCOVERY_GATEWAY_URL")
    with session_scope(factory) as session:
        gateway = GatewayProvider(resolved, timeout_seconds=settings.gateway_timeout_seconds)
        try:
            report = gateway.sync_status()
        finally:
            gateway.close()
        ProviderRegistryService(session).store_sync_report(report)
    console.print_json(report.model_dump_json(indent=2))


@provider_app.command("gateway-coverage")
def provider_gateway_coverage(
    gateway_url: Annotated[str | None, typer.Option("--gateway")] = None,
    field: Annotated[str | None, typer.Option("--field")] = None,
) -> None:
    settings = _settings()
    resolved = gateway_url or settings.gateway_url
    if resolved is None:
        raise typer.BadParameter("set --gateway or DISCOVERY_GATEWAY_URL")
    gateway = GatewayProvider(resolved, timeout_seconds=settings.gateway_timeout_seconds)
    try:
        params: dict[str, object] = {}
        if field is not None:
            params["field"] = field
        report = gateway.coverage_report(**params)
    finally:
        gateway.close()
    console.print_json(report.model_dump_json(indent=2))


@provider_app.command("resolve")
def provider_resolve_identity(
    identifier: str,
    gateway_url: Annotated[str | None, typer.Option("--gateway")] = None,
    database_url: Annotated[str | None, typer.Option("--database")] = None,
) -> None:
    settings, _engine, factory = _factory(database_url)
    resolved = gateway_url or settings.gateway_url
    if resolved is None:
        raise typer.BadParameter("set --gateway or DISCOVERY_GATEWAY_URL")
    gateway = GatewayProvider(resolved, timeout_seconds=settings.gateway_timeout_seconds)
    try:
        report = gateway.resolve_identity(identifier)
    finally:
        gateway.close()
    with session_scope(factory) as session:
        ingest = IdentityGraphService(session).ingest(report)
    console.print_json(
        json.dumps(
            {
                "resolution": report.model_dump(mode="json"),
                "ingest": ingest.model_dump(mode="json"),
            }
        )
    )


@provider_app.command("integrity")
def provider_integrity(
    identifier: str,
    gateway_url: Annotated[str | None, typer.Option("--gateway")] = None,
    database_url: Annotated[str | None, typer.Option("--database")] = None,
) -> None:
    settings, _engine, factory = _factory(database_url)
    resolved = gateway_url or settings.gateway_url
    if resolved is None:
        raise typer.BadParameter("set --gateway or DISCOVERY_GATEWAY_URL")
    gateway = GatewayProvider(resolved, timeout_seconds=settings.gateway_timeout_seconds)
    try:
        report = gateway.integrity(identifier)
    finally:
        gateway.close()
    with session_scope(factory) as session:
        count = IntegrityService(session).ingest(report)
    console.print_json(
        json.dumps({"report": report.model_dump(mode="json"), "assertions_persisted": count})
    )


@retrieval_app.command("deep-search")
def retrieval_deep_search(
    provider_name: str,
    query: str,
    pages: Annotated[int, typer.Option("--pages", min=1, max=100000)] = 10,
    page_size: Annotated[int, typer.Option("--page-size", min=1, max=1000)] = 100,
    database_url: Annotated[str | None, typer.Option("--database")] = None,
) -> None:
    """Cursor/offset harvest one direct provider with resumable page checkpoints."""
    settings, _engine, factory = _factory(database_url)
    audit = BufferedRequestObserver()
    with session_scope(factory) as session:
        with create_direct_provider(
            _direct_provider_config(settings, provider_name),
            observer=audit,
        ) as provider:
            if not hasattr(provider, "search_page"):
                raise typer.BadParameter(f"provider {provider_name!r} does not support paging")
            paged_provider = cast(PagedResearchProvider, provider)
            result = DeepHarvestEngine(session, paged_provider).execute(
                SearchQuery(text=query, limit=page_size, providers=[provider_name]),
                policy=DeepHarvestPolicy(max_pages=pages),
            )
        audit.drain(
            session,
            object_store=LocalContentAddressedStore(settings.object_store_path),
            persist_response_bodies=True,
        )
    console.print_json(result.model_dump_json(indent=2))


@retrieval_app.command("deep-federated")
def retrieval_deep_federated(
    query: str,
    providers: Annotated[str | None, typer.Option("--providers")] = None,
    pages_per_provider: Annotated[
        int, typer.Option("--pages-per-provider", min=1, max=100000)
    ] = 20,
    page_size: Annotated[int, typer.Option("--page-size", min=1, max=1000)] = 100,
    database_url: Annotated[str | None, typer.Option("--database")] = None,
) -> None:
    """Run resumable provider-native paging across multiple direct sources."""
    settings, _engine, factory = _factory(database_url)
    config = _direct_provider_config(settings, providers)
    audit = BufferedRequestObserver()
    with session_scope(factory) as session:
        with ExitStack() as stack:
            paged: dict[str, PagedResearchProvider] = {}
            for provider_name in config.providers:
                manager = create_direct_provider(
                    config.model_copy(update={"providers": [provider_name]}),
                    observer=audit,
                )
                provider = stack.enter_context(manager)
                if not hasattr(provider, "search_page"):
                    raise typer.BadParameter(
                        f"provider {provider_name!r} does not support paging"
                    )
                paged[provider_name] = cast(PagedResearchProvider, provider)
            result = DirectHarvestCoordinator(session).execute(
                SearchQuery(text=query, limit=page_size, providers=config.providers),
                paged,
                policy=MultiProviderHarvestPolicy(
                    max_pages_per_provider=pages_per_provider
                ),
            )
        audit.drain(
            session,
            object_store=LocalContentAddressedStore(settings.object_store_path),
            persist_response_bodies=True,
        )
    console.print_json(result.model_dump_json(indent=2))


@retrieval_app.command("gateway-harvest")
def retrieval_gateway_harvest(
    payload_path: Path,
    pages: Annotated[int, typer.Option("--pages", min=1, max=100000)] = 100,
    gateway_url: Annotated[str | None, typer.Option("--gateway")] = None,
    database_url: Annotated[str | None, typer.Option("--database")] = None,
) -> None:
    settings, _engine, factory = _factory(database_url)
    resolved = gateway_url or settings.gateway_url
    if resolved is None:
        raise typer.BadParameter("set --gateway or DISCOVERY_GATEWAY_URL")
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise typer.BadParameter("gateway harvest payload must be a JSON object")
    gateway = GatewayProvider(resolved, timeout_seconds=settings.gateway_timeout_seconds)
    try:
        with session_scope(factory) as session:
            result = GatewayCursorHarvestEngine(session, gateway).execute(
                payload,
                policy=GatewayCursorHarvestPolicy(max_pages=pages),
            )
    finally:
        gateway.close()
    console.print_json(result.model_dump_json(indent=2))


@campaign_app.command("create")
def campaign_create(
    scope_type: CampaignScope,
    scope_id: str,
    name: Annotated[str | None, typer.Option("--name")] = None,
    providers: Annotated[str | None, typer.Option("--providers")] = None,
    result_limit: Annotated[int, typer.Option("--limit", min=1, max=1000)] = 50,
    enrich_identity: Annotated[bool, typer.Option("--identity/--no-identity")] = False,
    enrich_integrity: Annotated[bool, typer.Option("--integrity/--no-integrity")] = False,
    enqueue_assets: Annotated[bool, typer.Option("--enqueue-assets/--no-enqueue-assets")] = False,
    database_url: Annotated[str | None, typer.Option("--database")] = None,
) -> None:
    _settings_value, _engine, factory = _factory(database_url)
    selected = [item.strip() for item in providers.split(",") if item.strip()] if providers else []
    config = CampaignConfig(
        scope_type=scope_type,
        scope_id=scope_id,
        name=name,
        result_limit=result_limit,
        providers=selected,
        enrich_identity=enrich_identity,
        enrich_integrity=enrich_integrity,
        enqueue_asset_processing=enqueue_assets,
    )
    with session_scope(factory) as session:
        row = CampaignService(session).create(config)
    console.print(row.id)


@campaign_app.command("run")
def campaign_run(
    campaign_id: str,
    mode: Annotated[ProviderMode, typer.Option("--mode")] = ProviderMode.DIRECT,
    providers: Annotated[str | None, typer.Option("--providers")] = None,
    gateway_url: Annotated[str | None, typer.Option("--gateway")] = None,
    database_url: Annotated[str | None, typer.Option("--database")] = None,
) -> None:
    settings, _engine, factory = _factory(database_url)
    audit = BufferedRequestObserver()
    with session_scope(factory) as session:
        if mode == ProviderMode.DIRECT:
            manager = create_direct_provider(
                _direct_provider_config(settings, providers),
                observer=audit,
            )
        else:
            resolved = gateway_url or settings.gateway_url
            if resolved is None:
                raise typer.BadParameter("set --gateway or DISCOVERY_GATEWAY_URL")
            manager = create_gateway_provider(
                resolved,
                timeout_seconds=settings.gateway_timeout_seconds,
                observer=audit,
            )
        with manager as provider:
            enrichment = provider if isinstance(provider, GatewayProvider) else None
            result = CampaignService(session).run(
                campaign_id,
                provider,
                gateway_enrichment=enrichment,
            )
        audit.drain(
            session,
            object_store=LocalContentAddressedStore(settings.object_store_path),
            persist_response_bodies=True,
        )
    console.print_json(result.model_dump_json(indent=2))


@queue_app.command("enqueue")
def queue_enqueue(
    work_id: str,
    stage: ProcessingStage,
    asset_id: Annotated[str | None, typer.Option("--asset-id")] = None,
    priority: Annotated[int, typer.Option("--priority")] = 0,
    database_url: Annotated[str | None, typer.Option("--database")] = None,
) -> None:
    _settings_value, _engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        job = ProcessingQueue(session).enqueue(
            work_id=work_id,
            asset_id=asset_id,
            stage=stage,
            priority=priority,
        )
    console.print_json(job.model_dump_json(indent=2))


@queue_app.command("stats")
def queue_stats(
    database_url: Annotated[str | None, typer.Option("--database")] = None,
) -> None:
    _settings_value, _engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        stats = ProcessingQueue(session).stats()
    console.print_json(stats.model_dump_json(indent=2))


@queue_app.command("work-once")
def queue_work_once(
    database_url: Annotated[str | None, typer.Option("--database")] = None,
) -> None:
    settings, _engine, factory = _factory(database_url)
    fetcher = RightsAwareAssetFetcher()
    try:
        with session_scope(factory) as session:
            result = LocalProcessingWorker(
                session,
                LocalContentAddressedStore(settings.object_store_path),
                fetcher,
            ).run_once()
    finally:
        fetcher.close()
    console.print_json(result.model_dump_json(indent=2))


@corpus_app.command("export")
def corpus_export(
    output_path: Path,
    database_url: Annotated[str | None, typer.Option("--database")] = None,
) -> None:
    _settings_value, _engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        summary = CorpusExporter(session).export(output_path)
    console.print_json(summary.model_dump_json(indent=2))


@documents_app.command("process-canonical")
def documents_process_canonical(
    work_id: str,
    asset_path: Path,
    source_format: str,
    input_path: Path,
    database_url: Annotated[str | None, typer.Option("--database")] = None,
) -> None:
    asset = Asset.model_validate_json(asset_path.read_text(encoding="utf-8"))
    _settings_value, _engine, factory = _factory(database_url)
    with session_scope(factory) as session:
        result = CanonicalResearchProcessor(session).process_bytes(
            work_id=work_id,
            asset=asset,
            source_format=source_format,
            content=input_path.read_bytes(),
        )
    console.print_json(result.model_dump_json(indent=2))


if __name__ == "__main__":
    app()

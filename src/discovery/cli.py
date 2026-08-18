from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

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
from discovery.corpus.schema import Asset
from discovery.documents.fetcher import RightsAwareAssetFetcher
from discovery.documents.ingestion import DocumentIngestionService
from discovery.documents.schema import ParsedDocument
from discovery.documents.service import DocumentService
from discovery.evaluation.benchmark import Annotator, ProblemAnnotation, ProblemAnnotationBundle
from discovery.evaluation.completeness import problem_completeness
from discovery.evaluation.corpus import BenchmarkCorpus, BenchmarkWork
from discovery.experiments.tracker import ExperimentTracker
from discovery.observability.coverage import CoverageService
from discovery.observability.health import DoctorReport, database_counts
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
from discovery.retrieval.gateway import GatewayProvider
from discovery.retrieval.harvest import HarvestPolicy, ResearchHarvestEngine
from discovery.retrieval.models import SearchQuery
from discovery.retrieval.planning import batch_query_plan
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
from discovery.storage.repositories import ProblemRepository

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


if __name__ == "__main__":
    app()

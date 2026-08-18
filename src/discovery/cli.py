from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from pydantic import BaseModel, ValidationError
from rich.console import Console
from rich.table import Table
from sqlalchemy import func, select

from discovery.analysis.similarity import baseline_problem_similarity
from discovery.config import Settings
from discovery.core.jsonl import read_jsonl, write_jsonl
from discovery.corpus.schema import Work
from discovery.discovery.schema import CrossDomainCandidate
from discovery.documents.schema import ParsedDocument
from discovery.evaluation.benchmark import Annotator, ProblemAnnotation, ProblemAnnotationBundle
from discovery.evaluation.corpus import BenchmarkCorpus, BenchmarkWork
from discovery.experiments.schema import ExperimentRun
from discovery.experiments.tracker import ExperimentTracker
from discovery.mathematics.schema import MathExpression
from discovery.ontology.importer import OntologySeedImporter
from discovery.ontology.query_compiler import OntologyQueryCompiler
from discovery.ontology.service import ontology_stats
from discovery.problems.family import ProblemFamily
from discovery.problems.schema import ProblemInstance
from discovery.quantum.matching import baseline_quantum_match
from discovery.quantum.schema import QuantumAlgorithm, QuantumMatch, QuantumPrimitive
from discovery.retrieval.gateway import GatewayProvider
from discovery.retrieval.models import QueryPlan, SearchQuery
from discovery.retrieval.service import RetrievalService
from discovery.storage.database import (
    create_database_engine,
    database_health,
    init_db,
    make_session_factory,
    session_scope,
)
from discovery.storage.models import ProblemInstanceRow, RetrievalRunRow, WorkRow
from discovery.storage.repositories import ProblemRepository

app = typer.Typer(
    name="discovery",
    help="Cross-disciplinary scientific problem discovery research engine.",
    no_args_is_help=True,
)
console = Console()

db_app = typer.Typer(help="Canonical research database operations.")
ontology_app = typer.Typer(help="Ontology seed import and retrieval-language tooling.")
corpus_app = typer.Typer(help="Corpus inspection and persistence.")
retrieval_app = typer.Typer(help="Retrieval planning and gateway execution.")
analysis_app = typer.Typer(help="Transparent structural-analysis baselines.")
quantum_app = typer.Typer(help="Quantum target representation and structural screening.")
experiment_app = typer.Typer(help="Reproducible experiment tracking.")
benchmark_app = typer.Typer(help="Benchmark sampling and annotation workflow.")

app.add_typer(db_app, name="db")
app.add_typer(ontology_app, name="ontology")
app.add_typer(corpus_app, name="corpus")
app.add_typer(retrieval_app, name="retrieval")
app.add_typer(analysis_app, name="analysis")
app.add_typer(quantum_app, name="quantum")
app.add_typer(experiment_app, name="experiment")
app.add_typer(benchmark_app, name="benchmark")


def _settings(database_url: str | None = None) -> Settings:
    settings = Settings.from_env()
    if database_url is not None:
        settings = settings.model_copy(update={"database_url": database_url})
    return settings


def _load_problem(path: Path) -> ProblemInstance:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ProblemInstance.model_validate(payload)


@app.command("validate-problem")
def validate_problem(path: Path) -> None:
    """Validate one ProblemInstance JSON document."""
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
    """Validate a JSONL benchmark of ProblemAnnotation records."""
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
    """Validate a benchmark corpus selection file."""
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
    disciplines = sorted({work.discipline for work in corpus.works})
    console.print(f"Disciplines: {len(disciplines)}")
    for discipline in disciplines:
        count = sum(work.discipline == discipline for work in corpus.works)
        console.print(f"  {discipline}: {count}")


_SCHEMA_MODELS: dict[str, type[BaseModel]] = {
    "problem": ProblemInstance,
    "annotation": ProblemAnnotation,
    "annotation-bundle": ProblemAnnotationBundle,
    "benchmark-work": BenchmarkWork,
    "benchmark-corpus": BenchmarkCorpus,
    "work": Work,
    "query-plan": QueryPlan,
    "document": ParsedDocument,
    "math-expression": MathExpression,
    "problem-family": ProblemFamily,
    "cross-domain-candidate": CrossDomainCandidate,
    "quantum-primitive": QuantumPrimitive,
    "quantum-algorithm": QuantumAlgorithm,
    "quantum-match": QuantumMatch,
    "experiment": ExperimentRun,
}


@app.command("schema")
def print_schema(
    model: str = typer.Argument(help="Model name; invalid names print available choices."),
) -> None:
    """Print JSON Schema for a core research model."""
    selected = _SCHEMA_MODELS.get(model)
    if selected is None:
        choices = ", ".join(sorted(_SCHEMA_MODELS))
        raise typer.BadParameter(f"unknown model {model!r}; choose one of: {choices}")
    console.print_json(json.dumps(selected.model_json_schema()))


def _load_benchmark_corpus(path: Path) -> BenchmarkCorpus:
    if not path.exists():
        return BenchmarkCorpus(
            benchmark_name="cross-disciplinary-scientific-problems",
            version="0.1",
            description="Cross-disciplinary scientific problem benchmark.",
            works=[],
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    return BenchmarkCorpus.model_validate(payload)


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
    table.add_column("ID")
    table.add_column("Discipline")
    table.add_column("Year")
    table.add_column("Status")
    table.add_column("Title")
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
    console.print("Disciplines:")
    for name, count in sorted(by_discipline.items()):
        console.print(f"  {name}: {count}")
    console.print("Statuses:")
    for name, count in sorted(by_status.items()):
        console.print(f"  {name}: {count}")


@benchmark_app.command("scaffold-annotation")
def benchmark_scaffold_annotation(
    corpus_path: Path,
    benchmark_work_id: str,
    output: Path,
    annotator_id: str = typer.Option("human-001", "--annotator"),
) -> None:
    corpus = _load_benchmark_corpus(corpus_path)
    work = next(
        (item for item in corpus.works if item.benchmark_work_id == benchmark_work_id),
        None,
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
        payload = json.loads(path.read_text(encoding="utf-8"))
        bundle = ProblemAnnotationBundle.model_validate(payload)
        records.extend(annotation.model_dump(mode="json") for annotation in bundle.annotations())
    write_jsonl(output, records)
    console.print(f"[green]exported[/green] {len(records)} annotations to {output}")


@db_app.command("init")
def db_init(database_url: str | None = typer.Option(None, "--database")) -> None:
    settings = _settings(database_url)
    engine = create_database_engine(settings.database_url)
    init_db(engine)
    console.print(f"[green]initialized[/green] {settings.database_url}")


@db_app.command("info")
def db_info(database_url: str | None = typer.Option(None, "--database")) -> None:
    settings = _settings(database_url)
    engine = create_database_engine(settings.database_url)
    init_db(engine)
    factory = make_session_factory(engine)
    with session_scope(factory) as session:
        counts = {
            "works": int(session.scalar(select(func.count()).select_from(WorkRow)) or 0),
            "problems": int(
                session.scalar(select(func.count()).select_from(ProblemInstanceRow)) or 0
            ),
            "retrieval_runs": int(
                session.scalar(select(func.count()).select_from(RetrievalRunRow)) or 0
            ),
        }
    console.print(f"Healthy: {database_health(engine)}")
    for key, value in counts.items():
        console.print(f"{key}: {value}")


@ontology_app.command("import-seed")
def ontology_import_seed(
    path: Annotated[Path, typer.Argument(exists=True, file_okay=False)],
    database_url: str | None = typer.Option(None, "--database"),
) -> None:
    settings = _settings(database_url)
    engine = create_database_engine(settings.database_url)
    init_db(engine)
    factory = make_session_factory(engine)
    with session_scope(factory) as session:
        report = OntologySeedImporter(session).import_directory(path)
    console.print_json(report.model_dump_json(indent=2))


@ontology_app.command("stats")
def ontology_statistics(database_url: str | None = typer.Option(None, "--database")) -> None:
    settings = _settings(database_url)
    engine = create_database_engine(settings.database_url)
    init_db(engine)
    factory = make_session_factory(engine)
    with session_scope(factory) as session:
        stats = ontology_stats(session)
    console.print_json(json.dumps(stats))


@ontology_app.command("plan")
def ontology_plan(
    concept_id: str,
    max_terms: int = typer.Option(24, min=1, max=100),
    database_url: str | None = typer.Option(None, "--database"),
) -> None:
    settings = _settings(database_url)
    engine = create_database_engine(settings.database_url)
    init_db(engine)
    factory = make_session_factory(engine)
    with session_scope(factory) as session:
        plan = OntologyQueryCompiler(session).compile_concept(concept_id, max_terms=max_terms)
    console.print_json(plan.model_dump_json(indent=2))


@corpus_app.command("stats")
def corpus_stats(database_url: str | None = typer.Option(None, "--database")) -> None:
    settings = _settings(database_url)
    engine = create_database_engine(settings.database_url)
    init_db(engine)
    factory = make_session_factory(engine)
    with session_scope(factory) as session:
        works = int(session.scalar(select(func.count()).select_from(WorkRow)) or 0)
        console.print(f"Works: {works}")
        console.print(
            "Problems: "
            f"{int(session.scalar(select(func.count()).select_from(ProblemInstanceRow)) or 0)}"
        )


@corpus_app.command("add-problem")
def corpus_add_problem(
    path: Path,
    database_url: str | None = typer.Option(None, "--database"),
) -> None:
    problem = _load_problem(path)
    settings = _settings(database_url)
    engine = create_database_engine(settings.database_url)
    init_db(engine)
    factory = make_session_factory(engine)
    with session_scope(factory) as session:
        ProblemRepository(session).upsert(problem)
    console.print(f"[green]stored[/green] {problem.id}")


@retrieval_app.command("plan")
def retrieval_plan(
    concept_id: str,
    database_url: str | None = typer.Option(None, "--database"),
) -> None:
    settings = _settings(database_url)
    engine = create_database_engine(settings.database_url)
    init_db(engine)
    factory = make_session_factory(engine)
    with session_scope(factory) as session:
        plan = OntologyQueryCompiler(session).compile_concept(concept_id)
    console.print(plan.rendered_query)


@retrieval_app.command("gateway-search")
def gateway_search(
    query: str,
    gateway_url: str | None = typer.Option(None, "--gateway"),
    limit: int = typer.Option(25, min=1, max=1000),
    database_url: str | None = typer.Option(None, "--database"),
) -> None:
    settings = _settings(database_url)
    resolved_gateway = gateway_url or settings.gateway_url
    if resolved_gateway is None:
        raise typer.BadParameter("set --gateway or DISCOVERY_GATEWAY_URL")
    engine = create_database_engine(settings.database_url)
    init_db(engine)
    factory = make_session_factory(engine)
    gateway = GatewayProvider(resolved_gateway, timeout_seconds=settings.gateway_timeout_seconds)
    try:
        with session_scope(factory) as session:
            request = SearchQuery(text=query, limit=limit)
            response = RetrievalService(session, gateway).execute(request)
    finally:
        gateway.close()
    console.print(f"Hits: {len(response.hits)}")
    for hit in response.hits[:20]:
        title = hit.work.title if hit.work else "<unparsed record>"
        console.print(f"{hit.provider_rank:>3} {hit.provider:<20} {title}")


@analysis_app.command("similarity")
def analysis_similarity(problem_a: Path, problem_b: Path) -> None:
    a = _load_problem(problem_a)
    b = _load_problem(problem_b)
    evidence = baseline_problem_similarity(a, b)
    payload = evidence.model_dump(mode="json")
    payload["structural_score"] = evidence.structural_score()
    console.print_json(json.dumps(payload))


@quantum_app.command("match")
def quantum_match(problem_path: Path, algorithm_path: Path) -> None:
    problem = _load_problem(problem_path)
    algorithm_payload = json.loads(algorithm_path.read_text(encoding="utf-8"))
    algorithm = QuantumAlgorithm.model_validate(algorithm_payload)
    match = baseline_quantum_match(problem, algorithm)
    console.print_json(match.model_dump_json(indent=2))


@experiment_app.command("start")
def experiment_start(
    name: str,
    experiment_type: str = typer.Option("manual"),
    database_url: str | None = typer.Option(None, "--database"),
) -> None:
    settings = _settings(database_url)
    engine = create_database_engine(settings.database_url)
    init_db(engine)
    factory = make_session_factory(engine)
    with session_scope(factory) as session:
        run = ExperimentTracker(session).start(name, experiment_type)
    console.print(run.id)


if __name__ == "__main__":
    app()

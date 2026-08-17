from __future__ import annotations

import json
from pathlib import Path

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from discovery.core.jsonl import read_jsonl
from discovery.evaluation.benchmark import ProblemAnnotation
from discovery.problems.schema import ProblemInstance

app = typer.Typer(
    name="discovery",
    help="Scientific problem structure discovery tooling.",
    no_args_is_help=True,
)

console = Console()


@app.command("validate-problem")
def validate_problem(path: Path) -> None:
    """Validate one ProblemInstance JSON document."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        problem = ProblemInstance.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        console.print(f"[bold red]INVALID[/bold red] {path}")
        console.print(str(exc))
        raise typer.Exit(code=1) from exc

    console.print(f"[bold green]VALID[/bold green] {problem.id}")
    console.print(f"Task family: {problem.task_family}")
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
            table.add_row(
                str(line_number),
                "INVALID",
                "-",
                str(exc.errors()[0].get("loc", "")),
            )
            continue

        valid += 1
        table.add_row(
            str(line_number),
            "VALID",
            annotation.benchmark_id,
            annotation.problem.task_family.value,
        )

    console.print(table)
    console.print(f"Valid: {valid}")
    console.print(f"Invalid: {invalid}")

    if invalid:
        raise typer.Exit(code=1)


@app.command("schema")
def print_schema(
    model: str = typer.Argument(help="problem | annotation"),
) -> None:
    """Print the JSON Schema for a core research model."""
    if model == "problem":
        schema = ProblemInstance.model_json_schema()
    elif model == "annotation":
        schema = ProblemAnnotation.model_json_schema()
    else:
        raise typer.BadParameter("model must be 'problem' or 'annotation'")

    console.print_json(json.dumps(schema))


if __name__ == "__main__":
    app()

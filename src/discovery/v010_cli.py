from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from discovery.analysis.cross_domain import rank_cross_domain_candidates
from discovery.analysis.discovery_loop import discover_structure
from discovery.core.jsonl import read_jsonl
from discovery.coverage.active import ActiveRetrievalPlanner
from discovery.coverage.strata import build_coverage_report
from discovery.mathematics.schema import MathExpression
from discovery.mathematics.similarity import compare_fingerprints
from discovery.mathematics.structural import fingerprint_expression
from discovery.problems.quality import assess_problem_quality
from discovery.problems.schema import ProblemInstance
from discovery.retrieval.cascade import default_high_recall_cascade

structure_app = typer.Typer(
    help="Pre-quantum scientific structure discovery, evaluation, and coverage feedback."
)


@structure_app.command("cascade")
def cascade() -> None:
    typer.echo(default_high_recall_cascade().model_dump_json(indent=2))


@structure_app.command("problem-quality")
def problem_quality(problem_path: Path) -> None:
    problem = ProblemInstance.model_validate_json(problem_path.read_text(encoding="utf-8"))
    typer.echo(assess_problem_quality(problem).model_dump_json(indent=2))


@structure_app.command("math-compare")
def math_compare(left: Path, right: Path) -> None:
    left_expression = MathExpression.model_validate_json(left.read_text(encoding="utf-8"))
    right_expression = MathExpression.model_validate_json(right.read_text(encoding="utf-8"))
    result = compare_fingerprints(
        fingerprint_expression(left_expression), fingerprint_expression(right_expression)
    )
    typer.echo(result.model_dump_json(indent=2))


@structure_app.command("discover")
def discover(
    problems_path: Path,
    discipline_map: Annotated[Path | None, typer.Option("--discipline-map")] = None,
) -> None:
    problems = [ProblemInstance.model_validate(item) for item in read_jsonl(problems_path)]
    result = discover_structure(problems)
    payload: dict[str, object] = {"structure": result.model_dump(mode="json")}
    if discipline_map is not None:
        mapping_raw = json.loads(discipline_map.read_text(encoding="utf-8"))
        if not isinstance(mapping_raw, dict):
            raise typer.BadParameter("discipline map must be a JSON object")
        mapping = {str(key): str(value) for key, value in mapping_raw.items()}
        payload["cross_domain_candidates"] = [
            item.model_dump(mode="json")
            for item in rank_cross_domain_candidates(result.similarities, mapping)
        ]
    typer.echo(json.dumps(payload, indent=2))


@structure_app.command("coverage")
def coverage(records_path: Path) -> None:
    records = list(read_jsonl(records_path))
    typer.echo(build_coverage_report(records).model_dump_json(indent=2))


@structure_app.command("prioritize")
def prioritize(scopes_path: Path) -> None:
    scopes = list(read_jsonl(scopes_path))
    priorities = ActiveRetrievalPlanner().prioritize(scopes)
    typer.echo(json.dumps([item.model_dump(mode="json") for item in priorities], indent=2))

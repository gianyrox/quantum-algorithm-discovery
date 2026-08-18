from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from discovery.execution.schema import CorpusExportSummary
from discovery.storage.models import (
    AssetRow,
    CitationRow,
    ProblemInstanceRow,
    WorkIdentifierRow,
    WorkRow,
)


def _jsonable_work(row: WorkRow) -> dict[str, object]:
    return {
        "id": row.id,
        "title": row.title,
        "abstract": row.abstract,
        "publication_year": row.publication_year,
        "work_type": row.work_type,
        "primary_language": row.primary_language,
        "metadata": row.metadata_json,
    }


class CorpusExporter:
    """Deterministic JSONL snapshot of the canonical research corpus."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def export(self, output_path: Path) -> CorpusExportSummary:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        works = list(self.session.scalars(select(WorkRow).order_by(WorkRow.id)))
        identifiers = list(
            self.session.scalars(
                select(WorkIdentifierRow).order_by(
                    WorkIdentifierRow.work_id,
                    WorkIdentifierRow.scheme,
                    WorkIdentifierRow.value,
                )
            )
        )
        assets = list(
            self.session.scalars(select(AssetRow).order_by(AssetRow.work_id, AssetRow.id))
        )
        citations = list(
            self.session.scalars(
                select(CitationRow).order_by(
                    CitationRow.source_work_id,
                    CitationRow.target_work_id,
                    CitationRow.provider,
                )
            )
        )
        problems = list(
            self.session.scalars(select(ProblemInstanceRow).order_by(ProblemInstanceRow.id))
        )
        with output_path.open("w", encoding="utf-8") as handle:
            for work_row in works:
                handle.write(
                    json.dumps({"type": "work", "data": _jsonable_work(work_row)}) + "\n"
                )
            for identifier_row in identifiers:
                handle.write(
                    json.dumps(
                        {
                            "type": "identifier",
                            "data": {
                                "work_id": identifier_row.work_id,
                                "scheme": identifier_row.scheme,
                                "value": identifier_row.value,
                                "version": identifier_row.version,
                                "canonical_url": identifier_row.canonical_url,
                                "provider": identifier_row.provider,
                                "raw_value": identifier_row.raw_value,
                            },
                        }
                    )
                    + "\n"
                )
            for asset_row in assets:
                handle.write(
                    json.dumps(
                        {
                            "type": "asset",
                            "data": {
                                "id": asset_row.id,
                                "work_id": asset_row.work_id,
                                "provider": asset_row.provider,
                                "representation": asset_row.representation,
                                "url": asset_row.url,
                                "mime_type": asset_row.mime_type,
                                "availability": asset_row.availability,
                                "rights": asset_row.rights_json,
                                "checksum": asset_row.checksum,
                            },
                        }
                    )
                    + "\n"
                )
            for citation_row in citations:
                handle.write(
                    json.dumps(
                        {
                            "type": "citation",
                            "data": {
                                "source_work_id": citation_row.source_work_id,
                                "target_work_id": citation_row.target_work_id,
                                "provider": citation_row.provider,
                                "provider_edge_id": citation_row.provider_edge_id,
                                "metadata": citation_row.metadata_json,
                            },
                        }
                    )
                    + "\n"
                )
            for problem_row in problems:
                handle.write(
                    json.dumps({"type": "problem", "data": problem_row.payload_json}) + "\n"
                )
        return CorpusExportSummary(
            works=len(works),
            identifiers=len(identifiers),
            assets=len(assets),
            citations=len(citations),
            problems=len(problems),
            output_path=str(output_path),
        )

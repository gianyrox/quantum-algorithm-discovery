from __future__ import annotations

from collections import Counter

from pydantic import BaseModel, ConfigDict, Field


class CoverageStratum(BaseModel):
    model_config = ConfigDict(extra="forbid")

    discipline: str = "unknown"
    decade: str = "unknown"
    language: str = "unknown"
    document_type: str = "unknown"
    provider: str = "unknown"
    access: str = "unknown"

    def key(self) -> str:
        return "|".join(
            (
                self.discipline,
                self.decade,
                self.language,
                self.document_type,
                self.provider,
                self.access,
            )
        )


class StratifiedCoverageReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_works: int = Field(ge=0)
    strata: dict[str, int] = Field(default_factory=dict)
    provider_counts: dict[str, int] = Field(default_factory=dict)
    decade_counts: dict[str, int] = Field(default_factory=dict)
    missing_dimensions: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


def decade_for_year(year: int | None) -> str:
    if year is None:
        return "unknown"
    decade = (year // 10) * 10
    return f"{decade}s"


def build_coverage_report(records: list[dict[str, object]]) -> StratifiedCoverageReport:
    strata: Counter[str] = Counter()
    providers: Counter[str] = Counter()
    decades: Counter[str] = Counter()
    missing: Counter[str] = Counter()
    for record in records:
        year = record.get("year")
        numeric_year = year if isinstance(year, int) else None
        dimensions = {
            "discipline": str(record.get("discipline") or "unknown"),
            "decade": decade_for_year(numeric_year),
            "language": str(record.get("language") or "unknown"),
            "document_type": str(record.get("document_type") or "unknown"),
            "provider": str(record.get("provider") or "unknown"),
            "access": str(record.get("access") or "unknown"),
        }
        for name, value in dimensions.items():
            if value == "unknown":
                missing[name] += 1
        stratum = CoverageStratum(**dimensions)
        strata[stratum.key()] += 1
        providers[stratum.provider] += 1
        decades[stratum.decade] += 1
    warnings: list[str] = []
    if records and providers.get("unknown", 0) / len(records) > 0.10:
        warnings.append("provider metadata missing for more than 10% of records")
    if records and decades.get("unknown", 0) / len(records) > 0.20:
        warnings.append("publication year missing for more than 20% of records")
    return StratifiedCoverageReport(
        total_works=len(records),
        strata=dict(sorted(strata.items())),
        provider_counts=dict(sorted(providers.items())),
        decade_counts=dict(sorted(decades.items())),
        missing_dimensions=dict(sorted(missing.items())),
        warnings=warnings,
    )

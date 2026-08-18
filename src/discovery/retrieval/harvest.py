from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from discovery.core.ids import stable_id
from discovery.retrieval.models import QueryPlan, SearchResponse
from discovery.retrieval.planning import QueryBatch
from discovery.retrieval.provider import ResearchProvider
from discovery.retrieval.saturation import SaturationObservation, SaturationPolicy
from discovery.retrieval.service import RetrievalService
from discovery.storage.models import (
    HarvestCheckpointRow,
    RetrievalHitRow,
    RetrievalQueryRow,
    WorkIdentifierRow,
)
from discovery.storage.repositories import AssetRepository, CitationRepository


class HarvestPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expand_references: bool = False
    expand_cited_by: bool = False
    discover_assets: bool = False
    citation_seed_limit: int = Field(default=25, ge=0, le=1000)
    citation_edge_limit: int = Field(default=250, ge=0, le=10000)
    saturation: SaturationPolicy | None = None
    stop_on_error: bool = False


class HarvestResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_id: str
    started_at: datetime
    completed_at: datetime
    planned_query_count: int
    query_count: int
    hit_count: int
    unique_work_ids: list[str]
    citation_edges_seen: int = 0
    assets_seen: int = 0
    stopped_for_saturation: bool = False
    saturation_observations: list[SaturationObservation] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ResearchHarvestEngine:
    """Replayable retrieval at the query-batch boundary.

    Deep provider pagination is an upstream capability. This engine preserves each
    query as a RetrievalRun, deduplicates works through canonical identifiers, and
    can optionally collect citation edges and rights-aware asset locations.
    """

    def __init__(self, session: Session, provider: ResearchProvider) -> None:
        self.session = session
        self.provider = provider
        self.retrieval = RetrievalService(session, provider)
        self.citations = CitationRepository(session)
        self.assets = AssetRepository(session)

    def execute(
        self,
        batch: QueryBatch,
        *,
        plan: QueryPlan | None = None,
        policy: HarvestPolicy | None = None,
    ) -> HarvestResult:
        resolved_policy = policy or HarvestPolicy()
        started = datetime.now(UTC)
        responses: list[SearchResponse] = []
        errors: list[str] = []
        work_ids: set[str] = set()
        seed_identifiers: dict[str, str] = {}
        observations: list[SaturationObservation] = []
        stopped_for_saturation = False
        for query_index, query in enumerate(batch.queries):
            before_unique = len(work_ids)
            query_row_id = stable_id(
                "retrieval-query", f"{batch.id}:{query_index}:{query.text}"
            )
            query_row = self.session.get(RetrievalQueryRow, query_row_id)
            if query_row is None:
                query_row = RetrievalQueryRow(
                    id=query_row_id,
                    batch_id=batch.id,
                    plan_id=plan.id if plan is not None else batch.plan_id,
                    query_text=query.text,
                    provider_scope_json=query.providers,
                    filters_json=query.filters,
                    status="pending",
                    created_at=datetime.now(UTC),
                )
                self.session.add(query_row)
                self.session.flush()
            checkpoint = self.session.scalar(
                select(HarvestCheckpointRow).where(
                    HarvestCheckpointRow.batch_id == batch.id,
                    HarvestCheckpointRow.query_index == query_index,
                )
            )
            if checkpoint is not None and checkpoint.status == "completed":
                query_row.status = "completed"
                query_row.completed_at = query_row.completed_at or datetime.now(UTC)
                self.session.add(query_row)
                retrieved = self._recover_checkpoint(checkpoint, work_ids, seed_identifiers)
                observations.append(
                    SaturationObservation(
                        iteration=query_index + 1,
                        retrieved=retrieved,
                        new_unique_works=len(work_ids) - before_unique,
                        cumulative_unique_works=len(work_ids),
                    )
                )
                if resolved_policy.saturation is not None and resolved_policy.saturation.saturated(
                    observations
                ):
                    stopped_for_saturation = True
                    break
                continue
            if checkpoint is None:
                checkpoint = HarvestCheckpointRow(
                    batch_id=batch.id,
                    query_index=query_index,
                    query_text=query.text,
                    status="pending",
                    updated_at=datetime.now(UTC),
                )
                self.session.add(checkpoint)
                self.session.flush()
            try:
                run_id, response = self.retrieval.execute_with_run(query, plan=plan)
                responses.append(response)
                for hit in response.hits:
                    if hit.work is None:
                        continue
                    work_ids.add(hit.work.id)
                    seed = hit.work.identifiers[0].value if hit.work.identifiers else hit.work.id
                    seed_identifiers.setdefault(hit.work.id, seed)
                checkpoint.status = "completed"
                checkpoint.retrieval_run_id = run_id
                checkpoint.unique_work_count = len(
                    {hit.work.id for hit in response.hits if hit.work is not None}
                )
                checkpoint.error = None
                checkpoint.updated_at = datetime.now(UTC)
                self.session.add(checkpoint)
                query_row.status = "completed"
                query_row.completed_at = datetime.now(UTC)
                self.session.add(query_row)
                self.session.flush()
                observations.append(
                    SaturationObservation(
                        iteration=query_index + 1,
                        retrieved=len(response.hits),
                        new_unique_works=len(work_ids) - before_unique,
                        cumulative_unique_works=len(work_ids),
                    )
                )
                if resolved_policy.saturation is not None and resolved_policy.saturation.saturated(
                    observations
                ):
                    stopped_for_saturation = True
                    break
            except Exception as exc:
                checkpoint.status = "failed"
                checkpoint.error = f"{type(exc).__name__}:{exc}"
                checkpoint.updated_at = datetime.now(UTC)
                self.session.add(checkpoint)
                query_row.status = "failed"
                query_row.completed_at = datetime.now(UTC)
                self.session.add(query_row)
                self.session.flush()
                errors.append(f"search:{type(exc).__name__}:{exc}")
                if resolved_policy.stop_on_error:
                    raise

        citation_edges = 0
        assets_seen = 0
        if (
            resolved_policy.expand_references
            or resolved_policy.expand_cited_by
            or resolved_policy.discover_assets
        ):
            seeds = list(seed_identifiers.items())[: resolved_policy.citation_seed_limit]
            for work_id, identifier in seeds:
                if resolved_policy.expand_references:
                    citation_edges += self._collect_citations(
                        identifier, "references", errors, resolved_policy
                    )
                if resolved_policy.expand_cited_by:
                    citation_edges += self._collect_citations(
                        identifier, "cited_by", errors, resolved_policy
                    )
                if resolved_policy.discover_assets:
                    try:
                        asset_response = self.provider.assets(identifier)
                        for asset in asset_response.assets:
                            self.assets.upsert(work_id, asset)
                        assets_seen += len(asset_response.assets)
                    except Exception as exc:
                        errors.append(f"assets:{identifier}:{type(exc).__name__}:{exc}")
                        if resolved_policy.stop_on_error:
                            raise
                if citation_edges >= resolved_policy.citation_edge_limit:
                    break

        return HarvestResult(
            batch_id=batch.id,
            started_at=started,
            completed_at=datetime.now(UTC),
            planned_query_count=len(batch.queries),
            query_count=len(observations),
            hit_count=sum(item.retrieved for item in observations),
            unique_work_ids=sorted(work_ids),
            citation_edges_seen=citation_edges,
            assets_seen=assets_seen,
            stopped_for_saturation=stopped_for_saturation,
            saturation_observations=observations,
            errors=errors,
        )

    def _recover_checkpoint(
        self,
        checkpoint: HarvestCheckpointRow,
        work_ids: set[str],
        seed_identifiers: dict[str, str],
    ) -> int:
        if checkpoint.retrieval_run_id is None:
            return 0
        rows = list(
            self.session.scalars(
                select(RetrievalHitRow).where(
                    RetrievalHitRow.retrieval_run_id == checkpoint.retrieval_run_id
                )
            )
        )
        for row in rows:
            if row.work_id is None:
                continue
            work_ids.add(row.work_id)
            identifier = self.session.scalar(
                select(WorkIdentifierRow)
                .where(WorkIdentifierRow.work_id == row.work_id)
                .order_by(WorkIdentifierRow.id)
            )
            seed_identifiers.setdefault(
                row.work_id, identifier.value if identifier is not None else row.work_id
            )
        return len(rows)

    def _collect_citations(
        self,
        identifier: str,
        direction: str,
        errors: list[str],
        policy: HarvestPolicy,
    ) -> int:
        try:
            response = (
                self.provider.references(identifier)
                if direction == "references"
                else self.provider.cited_by(identifier)
            )
            for edge in response.edges[: policy.citation_edge_limit]:
                self.citations.upsert_edge(
                    source_work_id=edge.source_id,
                    target_work_id=edge.target_id,
                    provider=edge.provider,
                    provider_edge_id=edge.provider_edge_id,
                    metadata=edge.metadata,
                )
            return len(response.edges)
        except Exception as exc:
            errors.append(f"citation:{direction}:{identifier}:{type(exc).__name__}:{exc}")
            if policy.stop_on_error:
                raise
            return 0

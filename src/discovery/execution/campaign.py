from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from discovery.core.ids import stable_id
from discovery.corpus.integrity import IntegrityService
from discovery.corpus.resolution import IdentityGraphService
from discovery.execution.queue import ProcessingQueue
from discovery.execution.schema import (
    CampaignConfig,
    CampaignRunResult,
    CampaignScope,
    ProcessingStage,
)
from discovery.ontology.query_compiler import OntologyQueryCompiler
from discovery.retrieval.gateway_models import IdentityResolution, IntegrityReport
from discovery.retrieval.harvest import ResearchHarvestEngine
from discovery.retrieval.models import QueryClause, QueryPlan
from discovery.retrieval.planning import batch_query_plan
from discovery.retrieval.provider import ResearchProvider
from discovery.storage.models import (
    AssetRow,
    CampaignRunRow,
    ResearchCampaignRow,
    WorkIdentifierRow,
)


class GatewayEnrichmentProvider(Protocol):
    def resolve_identity(self, identifier: str) -> IdentityResolution: ...

    def integrity(self, identifier: str) -> IntegrityReport: ...


class CampaignService:
    """Durable orchestration around transparent retrieval primitives.

    Campaigns store intent; runs store outcomes. Re-running a campaign reuses
    lower-level harvest checkpoints where possible and never erases a prior run.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, config: CampaignConfig) -> ResearchCampaignRow:
        now = datetime.now(UTC)
        campaign_id = stable_id(
            "research-campaign",
            f"{config.scope_type.value}:{config.scope_id}:{config.model_dump_json()}",
        )
        row = self.session.get(ResearchCampaignRow, campaign_id)
        if row is None:
            row = ResearchCampaignRow(
                id=campaign_id,
                name=config.name or f"{config.scope_type.value}:{config.scope_id}",
                scope_type=config.scope_type.value,
                scope_id=config.scope_id,
                status="planned",
                config_json=config.model_dump(mode="json"),
                created_at=now,
                updated_at=now,
            )
            self.session.add(row)
            self.session.flush()
        return row

    def run(
        self,
        campaign_id: str,
        provider: ResearchProvider,
        *,
        gateway_enrichment: GatewayEnrichmentProvider | None = None,
    ) -> CampaignRunResult:
        campaign = self.session.get(ResearchCampaignRow, campaign_id)
        if campaign is None:
            raise KeyError(f"unknown research campaign: {campaign_id}")
        config = CampaignConfig.model_validate(campaign.config_json)
        started = datetime.now(UTC)
        run_id = str(uuid4())
        run = CampaignRunRow(
            id=run_id,
            campaign_id=campaign_id,
            status="running",
            started_at=started,
            result_json={},
        )
        campaign.status = "running"
        campaign.updated_at = started
        self.session.add_all([run, campaign])
        self.session.flush()
        errors: list[str] = []
        try:
            plan = self._compile(config)
            batch = batch_query_plan(
                plan,
                terms_per_query=config.terms_per_query,
                result_limit=config.result_limit,
                providers=config.providers,
                max_cost_usd=config.max_cost_usd,
            )
            harvest = ResearchHarvestEngine(self.session, provider).execute(
                batch,
                plan=plan,
                policy=config.harvest_policy,
            )
            errors.extend(harvest.errors)
            identity_count = 0
            integrity_count = 0
            if (config.enrich_identity or config.enrich_integrity) and gateway_enrichment is None:
                errors.append(
                    "gateway enrichment requested but no enrichment provider is configured"
                )
            if gateway_enrichment is not None:
                identity_count, integrity_count = self._enrich(
                    harvest.unique_work_ids,
                    config,
                    gateway_enrichment,
                    errors,
                )
            jobs = self._enqueue(harvest.unique_work_ids, config)
            completed = datetime.now(UTC)
            result = CampaignRunResult(
                campaign_id=campaign_id,
                run_id=run_id,
                status="completed_with_errors" if errors else "completed",
                started_at=started,
                completed_at=completed,
                query_plan_id=plan.id,
                query_batch_id=batch.id,
                unique_work_ids=harvest.unique_work_ids,
                retrieval_hits=harvest.hit_count,
                identity_assertions=identity_count,
                integrity_assertions=integrity_count,
                jobs_enqueued=jobs,
                errors=errors,
            )
            run.status = result.status
            run.completed_at = completed
            run.result_json = result.model_dump(mode="json")
            campaign.status = result.status
            campaign.updated_at = completed
            self.session.add_all([run, campaign])
            self.session.flush()
            return result
        except Exception as exc:
            completed = datetime.now(UTC)
            error = f"{type(exc).__name__}:{exc}"
            run.status = "failed"
            run.completed_at = completed
            run.error = error
            run.result_json = {"errors": [error]}
            campaign.status = "failed"
            campaign.updated_at = completed
            self.session.add_all([run, campaign])
            self.session.flush()
            raise

    def _compile(self, config: CampaignConfig) -> QueryPlan:
        compiler = OntologyQueryCompiler(self.session)
        if config.scope_type == CampaignScope.CONCEPT:
            return compiler.compile_concept(config.scope_id)
        if config.scope_type == CampaignScope.DISCIPLINE:
            return compiler.compile_discipline(config.scope_id, max_concepts=config.max_concepts)
        if config.scope_type == CampaignScope.QUERY:
            clause = QueryClause(text=config.scope_id, source="campaign.raw_query")
            return QueryPlan(
                id=stable_id("query-plan", f"campaign-query:{config.scope_id}"),
                name=f"query:{config.scope_id}",
                clauses=[clause],
                rendered_query=config.scope_id,
                notes=[
                    "User-supplied raw query; no ontology expansion was applied.",
                    "No quantum relevance filter is applied at the scientific retrieval stage.",
                ],
            )
        raise ValueError(f"unsupported campaign scope: {config.scope_type}")

    def _enrich(
        self,
        work_ids: list[str],
        config: CampaignConfig,
        gateway: GatewayEnrichmentProvider,
        errors: list[str],
    ) -> tuple[int, int]:
        identity_service = IdentityGraphService(self.session)
        integrity_service = IntegrityService(self.session)
        identity_count = 0
        integrity_count = 0
        for work_id in work_ids[: config.enrichment_limit]:
            identifier = self._seed_identifier(work_id)
            if identifier is None:
                continue
            if config.enrich_identity:
                try:
                    identity_report = gateway.resolve_identity(identifier)
                    identity_count += identity_service.ingest(
                        identity_report
                    ).assertions_persisted
                except Exception as exc:
                    errors.append(f"identity:{identifier}:{type(exc).__name__}:{exc}")
            if config.enrich_integrity:
                try:
                    integrity_report = gateway.integrity(identifier)
                    integrity_count += integrity_service.ingest(
                        integrity_report, work_id=work_id
                    )
                except Exception as exc:
                    errors.append(f"integrity:{identifier}:{type(exc).__name__}:{exc}")
        return identity_count, integrity_count

    def _enqueue(self, work_ids: list[str], config: CampaignConfig) -> int:
        if not config.enqueue_asset_processing:
            return 0
        queue = ProcessingQueue(self.session)
        count = 0
        for work_id in work_ids:
            assets = list(
                self.session.scalars(select(AssetRow).where(AssetRow.work_id == work_id))
            )
            if not assets:
                queue.enqueue(work_id=work_id, stage=ProcessingStage.ASSET_DISCOVERY)
                count += 1
                continue
            for asset in assets:
                queue.enqueue(
                    work_id=work_id,
                    asset_id=asset.id,
                    stage=ProcessingStage.ASSET_ACQUISITION,
                    payload={"representation": asset.representation},
                )
                count += 1
        return count

    def _seed_identifier(self, work_id: str) -> str | None:
        row = self.session.scalar(
            select(WorkIdentifierRow)
            .where(WorkIdentifierRow.work_id == work_id)
            .order_by(WorkIdentifierRow.id)
            .limit(1)
        )
        return row.value if row is not None else None

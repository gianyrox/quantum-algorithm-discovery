from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from discovery.corpus.service import CorpusService
from discovery.retrieval.boundary import require_gateway_boundary
from discovery.retrieval.feed402_store import Feed402EnvelopeRepository
from discovery.retrieval.gateway import GatewayProvider
from discovery.retrieval.models import QueryPlan, SearchQuery, SearchResponse
from discovery.retrieval.provider import ResearchProvider
from discovery.storage.models import RetrievalHitRow, RetrievalRunRow


def query_fingerprint(query: SearchQuery) -> str:
    payload = query.model_dump(mode="json")
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


class RetrievalService:
    def __init__(
        self,
        session: Session,
        provider: ResearchProvider,
        *,
        allow_legacy_direct: bool = False,
    ) -> None:
        if not allow_legacy_direct:
            require_gateway_boundary(provider)
        self.session = session
        self.provider = provider
        self.corpus = CorpusService(session)

    def execute(self, query: SearchQuery, *, plan: QueryPlan | None = None) -> SearchResponse:
        _, response = self.execute_with_run(query, plan=plan)
        return response

    def execute_with_run(
        self,
        query: SearchQuery,
        *,
        plan: QueryPlan | None = None,
    ) -> tuple[str, SearchResponse]:
        run = self._start_run(query, plan=plan, provider_name=self.provider.name)
        try:
            response = self.provider.search(query)
            self._persist_response(run, response)
            self._persist_feed402(run.id)
            return run.id, response
        except Exception:
            run.status = "failed"
            run.completed_at = datetime.now(UTC)
            self.session.add(run)
            self.session.flush()
            raise

    def record_response(
        self,
        query: SearchQuery,
        response: SearchResponse,
        *,
        plan: QueryPlan | None = None,
        provider_name: str | None = None,
    ) -> str:
        """Persist a response obtained through a page or replay-specific transport."""
        run = self._start_run(
            query,
            plan=plan,
            provider_name=provider_name or self.provider.name,
        )
        self._persist_response(run, response)
        self._persist_feed402(run.id)
        return run.id

    def _persist_feed402(self, retrieval_run_id: str) -> None:
        if not isinstance(self.provider, GatewayProvider):
            return
        records = self.provider.drain_feed402_envelopes()
        if not records:
            return
        manifest = self.provider.manifest()
        Feed402EnvelopeRepository(self.session).persist_retrieval_run(
            retrieval_run_id,
            records,
            spec=manifest.spec,
            merchant=self.provider.name,
        )

    def _start_run(
        self,
        query: SearchQuery,
        *,
        plan: QueryPlan | None,
        provider_name: str,
    ) -> RetrievalRunRow:
        run = RetrievalRunRow(
            id=str(uuid4()),
            provider=provider_name,
            query_text=query.text,
            query_plan_json=plan.model_dump(mode="json") if plan else {},
            query_fingerprint=query_fingerprint(query),
            started_at=datetime.now(UTC),
            status="running",
        )
        self.session.add(run)
        self.session.flush()
        return run

    def _persist_response(self, run: RetrievalRunRow, response: SearchResponse) -> None:
        for hit in response.hits:
            work_id: str | None = None
            if hit.work is not None:
                work = hit.work
                if hit.provenance is not None:
                    work = work.model_copy(
                        update={"provenance": [*work.provenance, hit.provenance]}
                    )
                row = self.corpus.works.upsert(work)
                work_id = row.id
                if work.id != work_id:
                    work = work.model_copy(update={"id": work_id})
                hit.work = work
            self.session.add(
                RetrievalHitRow(
                    retrieval_run_id=run.id,
                    work_id=work_id,
                    provider=hit.provider,
                    provider_rank=hit.provider_rank,
                    provider_score=hit.provider_score,
                    fused_rank=hit.fused_rank,
                    raw_record=hit.raw_record,
                    provenance_json=(
                        hit.provenance.model_dump(mode="json") if hit.provenance else {}
                    ),
                )
            )
        run.status = "completed"
        run.completed_at = datetime.now(UTC)
        run.provider_reports_json = [
            report.model_dump(mode="json") for report in response.provider_reports
        ]
        self.session.add(run)
        self.session.flush()

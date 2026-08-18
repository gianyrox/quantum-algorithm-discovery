from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from discovery.corpus.service import CorpusService
from discovery.retrieval.models import QueryPlan, SearchQuery, SearchResponse
from discovery.retrieval.provider import ResearchProvider
from discovery.storage.models import RetrievalHitRow, RetrievalRunRow


class RetrievalService:
    def __init__(self, session: Session, provider: ResearchProvider) -> None:
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
        run_id = str(uuid4())
        run = RetrievalRunRow(
            id=run_id,
            provider=self.provider.name,
            query_text=query.text,
            query_plan_json=plan.model_dump(mode="json") if plan else {},
            started_at=datetime.now(UTC),
            status="running",
        )
        self.session.add(run)
        self.session.flush()
        try:
            response = self.provider.search(query)
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
                        retrieval_run_id=run_id,
                        work_id=work_id,
                        provider=hit.provider,
                        provider_rank=hit.provider_rank,
                        provider_score=hit.provider_score,
                        fused_rank=hit.fused_rank,
                        raw_record=hit.raw_record,
                        provenance_json=hit.provenance.model_dump(mode="json")
                        if hit.provenance
                        else {},
                    )
                )
            run.status = "completed"
            run.completed_at = datetime.now(UTC)
            run.provider_reports_json = [
                report.model_dump(mode="json") for report in response.provider_reports
            ]
            self.session.flush()
            return run_id, response
        except Exception:
            run.status = "failed"
            run.completed_at = datetime.now(UTC)
            self.session.flush()
            raise

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from discovery.quantum.schema import QuantumAlgorithm, QuantumPrimitive
from discovery.storage.models import QuantumAlgorithmRow, QuantumPrimitiveRow


class QuantumCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    description: str
    primitives: list[QuantumPrimitive] = Field(default_factory=list)
    algorithms: list[QuantumAlgorithm] = Field(default_factory=list)
    provenance_notes: list[str] = Field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> QuantumCatalog:
        return cls.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.model_dump_json(indent=2) + "\n", encoding="utf-8")


class QuantumCatalogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def import_catalog(self, catalog: QuantumCatalog) -> tuple[int, int]:
        primitive_count = 0
        algorithm_count = 0
        for primitive in catalog.primitives:
            primitive_row = self.session.get(QuantumPrimitiveRow, primitive.id)
            if primitive_row is None:
                primitive_row = QuantumPrimitiveRow(
                    id=primitive.id,
                    name=primitive.name,
                    family=primitive.family,
                    payload_json=primitive.model_dump(mode="json"),
                )
                primitive_count += 1
            else:
                primitive_row.name = primitive.name
                primitive_row.family = primitive.family
                primitive_row.payload_json = primitive.model_dump(mode="json")
            self.session.add(primitive_row)
        for algorithm in catalog.algorithms:
            algorithm_row = self.session.get(QuantumAlgorithmRow, algorithm.id)
            if algorithm_row is None:
                algorithm_row = QuantumAlgorithmRow(
                    id=algorithm.id,
                    name=algorithm.name,
                    family=algorithm.family,
                    payload_json=algorithm.model_dump(mode="json"),
                )
                algorithm_count += 1
            else:
                algorithm_row.name = algorithm.name
                algorithm_row.family = algorithm.family
                algorithm_row.payload_json = algorithm.model_dump(mode="json")
            self.session.add(algorithm_row)
        self.session.flush()
        return primitive_count, algorithm_count

    def algorithms(self) -> list[QuantumAlgorithm]:
        from sqlalchemy import select

        rows = self.session.scalars(select(QuantumAlgorithmRow).order_by(QuantumAlgorithmRow.id))
        return [QuantumAlgorithm.model_validate(row.payload_json) for row in rows]

    def primitives(self) -> list[QuantumPrimitive]:
        from sqlalchemy import select

        rows = self.session.scalars(select(QuantumPrimitiveRow).order_by(QuantumPrimitiveRow.id))
        return [QuantumPrimitive.model_validate(row.payload_json) for row in rows]

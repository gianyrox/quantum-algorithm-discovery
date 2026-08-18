from __future__ import annotations

from sqlalchemy.orm import Session

from discovery.core.ids import stable_id
from discovery.documents.schema import ParsedDocument
from discovery.mathematics.features import extract_math_features
from discovery.mathematics.schema import MathExpression, SymbolGrounding
from discovery.storage.models import MathExpressionRow


class MathematicsService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def from_document(
        self,
        document: ParsedDocument,
        *,
        document_id: str | None = None,
    ) -> list[MathExpression]:
        expressions: list[MathExpression] = []
        for index, occurrence in enumerate(document.equations):
            features = extract_math_features(occurrence.latex, occurrence.mathml)
            expression = MathExpression(
                id=stable_id(
                    "math-expression",
                    f"{document.work_id}:{document.asset_id}:{occurrence.id}:{index}",
                ),
                work_id=document.work_id,
                equation_label=occurrence.label,
                raw_source=occurrence.latex or occurrence.mathml,
                latex=occurrence.latex,
                presentation_mathml=occurrence.mathml,
                operator_graph={"operators": features.operators, "commands": features.commands},
                symbols=[SymbolGrounding(symbol=symbol) for symbol in features.symbols],
                alpha_normalized=features.alpha_normalized,
                confidence=0.35,
            )
            self.store(expression, document_id=document_id)
            expressions.append(expression)
        return expressions

    def store(
        self,
        expression: MathExpression,
        *,
        document_id: str | None = None,
    ) -> MathExpressionRow:
        row = self.session.get(MathExpressionRow, expression.id)
        payload = expression.model_dump(mode="json")
        if row is None:
            row = MathExpressionRow(
                id=expression.id,
                work_id=expression.work_id,
                document_id=document_id,
                equation_label=expression.equation_label,
                payload_json=payload,
            )
        else:
            row.payload_json = payload
            row.document_id = document_id
            row.equation_label = expression.equation_label
        self.session.add(row)
        self.session.flush()
        return row

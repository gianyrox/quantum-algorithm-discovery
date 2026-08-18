from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from discovery.corpus.schema import Asset
from discovery.documents.access import AssetAction, decide_asset_action


class RankedAsset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset: Asset
    score: float
    reasons: list[str] = Field(default_factory=list)


_REPRESENTATION_PRIORITY = {
    "jats": 100.0,
    "xml": 90.0,
    "tei": 90.0,
    "tex": 85.0,
    "latex": 85.0,
    "source": 80.0,
    "html": 70.0,
    "text": 60.0,
    "plain_text": 60.0,
    "abstract": 50.0,
    "pdf": 10.0,
    "landing_page": 0.0,
}


def rank_assets(
    assets: list[Asset],
    *,
    require_retention: bool = True,
) -> list[RankedAsset]:
    ranked: list[RankedAsset] = []
    for asset in assets:
        reasons: list[str] = []
        tdm = decide_asset_action(asset, AssetAction.TDM)
        if not tdm.allowed:
            continue
        reasons.append(tdm.reason)
        if require_retention:
            retention = decide_asset_action(asset, AssetAction.RETENTION)
            if not retention.allowed:
                continue
            reasons.append(retention.reason)
        representation = asset.representation.casefold()
        score = _REPRESENTATION_PRIORITY.get(representation, 20.0)
        mime = (asset.mime_type or "").casefold()
        if "jats" in mime:
            score = max(score, 100.0)
        elif "tei" in mime:
            score = max(score, 90.0)
        elif "tex" in mime:
            score = max(score, 85.0)
        elif "html" in mime:
            score = max(score, 70.0)
        elif mime.startswith("text/"):
            score = max(score, 60.0)
        reasons.append(f"representation priority={score:.0f}")
        ranked.append(RankedAsset(asset=asset, score=score, reasons=reasons))
    ranked.sort(key=lambda item: (-item.score, item.asset.id))
    return ranked

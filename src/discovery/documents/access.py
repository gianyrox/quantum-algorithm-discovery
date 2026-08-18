from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from discovery.corpus.schema import Asset


class AssetAction(StrEnum):
    REDISTRIBUTION = "redistribution"
    TDM = "tdm"
    MODEL_TRAINING = "model_training"
    RETENTION = "retention"


class AssetAccessDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allowed: bool
    action: AssetAction
    reason: str
    evidence: list[str] = Field(default_factory=list)


def decide_asset_action(asset: Asset, action: AssetAction) -> AssetAccessDecision:
    if asset.availability != "retrievable":
        return AssetAccessDecision(
            allowed=False,
            action=action,
            reason=f"asset availability is {asset.availability!r}, not retrievable",
        )
    if asset.rights is None:
        return AssetAccessDecision(
            allowed=False,
            action=action,
            reason="rights are absent; unknown is not permission",
        )
    status = getattr(asset.rights, action.value)
    if status != "allowed":
        return AssetAccessDecision(
            allowed=False,
            action=action,
            reason=f"{action.value} is {status!r}; explicit allowed is required",
        )
    return AssetAccessDecision(
        allowed=True,
        action=action,
        reason=f"{action.value} is explicitly allowed",
    )

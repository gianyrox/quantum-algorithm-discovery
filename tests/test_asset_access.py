from discovery.core.provenance import RightsStatement
from discovery.corpus.schema import Asset
from discovery.documents.access import AssetAction, decide_asset_action


def test_asset_action_requires_explicit_permission() -> None:
    asset = Asset(id="a", representation="pdf", provider="p", availability="retrievable")
    assert not decide_asset_action(asset, AssetAction.TDM).allowed

    allowed = asset.model_copy(
        update={"rights": RightsStatement(tdm="allowed", retention="denied")}
    )
    assert decide_asset_action(allowed, AssetAction.TDM).allowed
    assert not decide_asset_action(allowed, AssetAction.RETENTION).allowed

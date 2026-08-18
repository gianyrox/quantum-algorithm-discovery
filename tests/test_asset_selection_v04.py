from discovery.core.provenance import RightsStatement
from discovery.corpus.schema import Asset
from discovery.documents.selection import rank_assets


def test_asset_selection_prefers_structured_explicitly_permitted_content() -> None:
    rights = RightsStatement(tdm="allowed", retention="allowed")
    assets = [
        Asset(
            id="pdf",
            provider="fixture",
            representation="pdf",
            availability="retrievable",
            rights=rights,
        ),
        Asset(
            id="jats",
            provider="fixture",
            representation="jats",
            availability="retrievable",
            rights=rights,
        ),
        Asset(
            id="unknown-rights",
            provider="fixture",
            representation="tex",
            availability="retrievable",
        ),
    ]
    ranked = rank_assets(assets)
    assert [item.asset.id for item in ranked] == ["jats", "pdf"]

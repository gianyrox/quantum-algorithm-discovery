from __future__ import annotations

import httpx

from discovery.corpus.schema import Asset
from discovery.documents.access import AssetAction, decide_asset_action


class AssetAccessDenied(RuntimeError):
    pass


class RightsAwareAssetFetcher:
    """Fetch only representations whose machine-readable rights explicitly permit TDM.

    Location discovery never becomes permission implicitly. Retention can be
    required separately for workflows that persist the raw bytes.
    """

    def __init__(
        self,
        client: httpx.Client | None = None,
        *,
        timeout_seconds: float = 60.0,
    ) -> None:
        self.client = client or httpx.Client(timeout=timeout_seconds, follow_redirects=True)
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def fetch(self, asset: Asset, *, require_retention: bool = False) -> bytes:
        tdm = decide_asset_action(asset, AssetAction.TDM)
        if not tdm.allowed:
            raise AssetAccessDenied(tdm.reason)
        if require_retention:
            retention = decide_asset_action(asset, AssetAction.RETENTION)
            if not retention.allowed:
                raise AssetAccessDenied(retention.reason)
        if asset.url is None:
            raise AssetAccessDenied("asset has no URL")
        response = self.client.get(str(asset.url))
        response.raise_for_status()
        return response.content

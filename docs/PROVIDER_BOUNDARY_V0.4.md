# Provider Boundary v0.4

## Two access modes, one corpus

Scientific Discovery intentionally supports both gateway and direct-provider execution.

### Gateway mode

Use gateway mode when the normalized capability surface is valuable: federated retrieval, provider capability discovery, identity evidence, normalized citations, rights-aware asset discovery, integrity, signed-cursor harvest, sync metadata, and provider coverage.

### Direct mode

Use direct mode for single-provider retrieval, resumable provider-native paging, local development, operational fallback, or high-volume workflows where an internal payment/proxy hop would add cost without adding scientific information.

Both modes end at the same canonical `Work`/provenance model.

## What Scientific Discovery does not duplicate

It does not try to become the universal registry of every external API. Source-specific lifecycle, provider rights, provider-specific normalization, and source capability research belong primarily in the gateway/source-registry layer.

Direct adapters are intentionally narrow research clients, not a second giant source-registry project.

## What Scientific Discovery must still own

The downstream engine owns concerns that cannot be delegated to retrieval infrastructure:

- canonical corpus identity decisions;
- experiment/retrieval lineage;
- long-running harvest checkpoints;
- rights decisions about local retention and analysis;
- document representation;
- problem/math extraction;
- cross-domain similarity and candidate generation;
- evaluation and review;
- quantum mapping and negative results.

## Provider absence is not scientific absence

A provider returning zero results, timing out, lacking a capability, or having incomplete indexing must remain distinguishable from “the literature contains nothing.” Coverage reports therefore retain provider and query strata rather than collapsing to one hit count.

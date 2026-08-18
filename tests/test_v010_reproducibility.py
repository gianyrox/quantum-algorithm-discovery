from discovery.reproducibility.manifest import ResearchManifest, SoftwareComponent


def test_manifest_fingerprint_is_stable_except_identity_time() -> None:
    left = ResearchManifest(
        id="a",
        corpus_release="corpus-1",
        extractor=SoftwareComponent(name="extractor", version="1"),
    )
    right = ResearchManifest(
        id="b",
        corpus_release="corpus-1",
        extractor=SoftwareComponent(name="extractor", version="1"),
    )
    assert left.fingerprint() == right.fingerprint()

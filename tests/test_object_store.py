from discovery.storage.object_store import LocalContentAddressedStore


def test_local_object_store_is_content_addressed(tmp_path) -> None:
    store = LocalContentAddressedStore(tmp_path / "objects")
    first = store.put(b"scientific content", media_type="text/plain")
    second = store.put(b"scientific content", media_type="text/plain")
    assert first.key == second.key
    assert store.get(first.key) == b"scientific content"

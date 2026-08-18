# v0.10 Validation

The upgrade package was applied to a fresh extraction of the committed v0.4 archive before delivery.

Validation available in the build environment:

- Python compilation of the package;
- 94 pytest tests passing, including all 74 inherited v0.4 tests;
- v0.10 pre-quantum smoke test;
- JSON-schema generation for 107 registered public models;
- Alembic migration chain `0001 -> 0002 -> 0003 -> 0004` on a fresh SQLite database;
- CLI discovery for the new `discovery structure` command group.

The build environment does not contain Ruff or mypy and cannot download packages. `scripts/post_upgrade_v010.sh` therefore runs Ruff and strict mypy in the project environment as the final static-analysis gate before commit.

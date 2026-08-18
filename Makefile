.PHONY: install test lint typecheck check smoke smoke-v03 db-init ontology-import schemas

install:
	python -m pip install -e '.[dev]'

test:
	pytest -q

lint:
	ruff check .

typecheck:
	mypy src

check: test lint typecheck

smoke:
	bash scripts/smoke_v03.sh

smoke-v03:
	bash scripts/smoke_v03.sh

db-init:
	discovery db init

ontology-import:
	discovery ontology import-seed scientific_retrieval_ontology_v0_1

schemas:
	discovery generate-schemas schemas

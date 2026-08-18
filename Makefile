.PHONY: install test lint typecheck check smoke db-init ontology-import

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
	bash scripts/smoke_test.sh

db-init:
	discovery db init

ontology-import:
	discovery ontology import-seed scientific_retrieval_ontology_v0_1

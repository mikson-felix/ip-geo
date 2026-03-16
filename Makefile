TEST=pytest
UV=uv run
SYNC=uv sync


.PHONY: install
install:
	$(SYNC) --all-groups

.PHONY: run
run:
	$(UV) granian --interface asgi --factory app.main:create_app

.PHONY: test
test:
	$(TEST)

.PHONY: cov
cov:
	$(TEST) --cov=app --cov-report=term-missing

.PHONY: check
check:
	$(UV) ruff check app tests
	$(UV) ruff format --check app tests
	$(UV) mypy app tests

.PHONY: format
format:
	$(UV) ruff check --fix app tests
	$(UV) ruff format app tests

.PHONY: precommit-install
precommit-install:
	$(UV) pre-commit install
	$(UV) pre-commit install --hook-type pre-push

.PHONY: precommit-run
precommit-run:
	$(UV) pre-commit run --all-files

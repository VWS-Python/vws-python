# Make commands for linting

SHELL := /bin/bash -euxo pipefail

.PHONY: black
black:
	black --check .

.PHONY: fix-black
fix-black:
	black .

.PHONY: mypy
mypy:
	mypy .

.PHONY: check-manifest
check-manifest:
	check-manifest .

.PHONY: doc8
doc8:
	doc8 .

.PHONY: ruff
ruff:
	ruff .

.PHONY: fix-ruff
fix-ruff:
	ruff --fix .

.PHONY: pip-extra-reqs
pip-extra-reqs:
	pdm export --pyproject | pip-extra-reqs --requirements-file=/dev/fd/0 src/

.PHONY: pip-missing-reqs
pip-missing-reqs:
	pdm export --pyproject | pip-missing-reqs --requirements-file=/dev/fd/0 src/

.PHONY: pylint
pylint:
	pylint src/ tests/ docs/

.PHONY: pyroma
pyroma:
	pyroma --min 10 .

.PHONY: vulture
vulture:
	vulture --min-confidence 100 --exclude _vendor --exclude .eggs .

.PHONY: linkcheck
linkcheck:
	$(MAKE) -C docs/ linkcheck SPHINXOPTS=$(SPHINXOPTS)

.PHONY: spelling
spelling:
	$(MAKE) -C docs/ spelling SPHINXOPTS=$(SPHINXOPTS)

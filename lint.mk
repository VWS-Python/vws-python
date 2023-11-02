# Make commands for linting

SHELL := /bin/bash -euxo pipefail

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
	ruff format --check .

.PHONY: fix-ruff
fix-ruff:
	ruff --fix .
	ruff format .

.PHONY: pip-extra-reqs
pip-extra-reqs:
	pip-extra-reqs --requirements-file=<(pdm export --pyproject) src/

.PHONY: pip-missing-reqs
pip-missing-reqs:
	pip-missing-reqs --requirements-file=<(pdm export --pyproject) src/

.PHONY: pylint
pylint:
	pylint *.py src/ tests/ docs/

.PHONY: pyroma
pyroma:
	pyroma --min 10 .

.PHONY: pyright
pyright:
	pyright .

.PHONY: vulture
vulture:
	vulture --min-confidence 100 --exclude _vendor --exclude .eggs .

.PHONY: linkcheck
linkcheck:
	$(MAKE) -C docs/ linkcheck SPHINXOPTS=$(SPHINXOPTS)

.PHONY: pyproject-fmt
 pyproject-fmt:
	pyproject-fmt --keep-full-version --check --indent=4 pyproject.toml

 .PHONY: fix-pyproject-fmt
 fix-pyproject-fmt:
	pyproject-fmt --keep-full-version --indent=4 pyproject.toml

.PHONY: spelling
spelling:
	$(MAKE) -C docs/ spelling SPHINXOPTS=$(SPHINXOPTS)

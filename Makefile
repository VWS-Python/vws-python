SHELL := /bin/bash -euxo pipefail

include lint.mk

# Treat Sphinx warnings as errors
SPHINXOPTS := -W

.PHONY: lint
lint: \
    actionlint \
    check-manifest \
    doc8 \
    linkcheck \
    mypy \
    ruff \
    pip-extra-reqs \
    pip-missing-reqs \
    pyproject-fmt \
    pyright \
    pyright-verifytypes \
    pyroma \
    spelling \
    vulture \
    pylint

.PHONY: fix-lint
fix-lint: \
    fix-pyproject-fmt \
    fix-ruff

.PHONY: docs
docs:
	make -C docs clean html SPHINXOPTS=$(SPHINXOPTS)

.PHONY: open-docs
open-docs:
	python -c 'import os, webbrowser; webbrowser.open("file://" + os.path.abspath("docs/build/html/index.html"))'

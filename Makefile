SHELL := /bin/bash -euxo pipefail

# Treat Sphinx warnings as errors
SPHINXOPTS := -W

.PHONY: lint
lint:
	check-manifest .
	doc8 .
	dodgy
	flake8 .
	isort --recursive --check-only
	mypy src/ tests/
	pip-extra-reqs src/
	pip-missing-reqs src/
	pydocstyle **
	pylint *.py src tests
	pyroma --min 10 .
	vulture . --min-confidence 100
	$(MAKE) -C docs spelling SPHINXOPTS=$(SPHINXOPTS)
	$(MAKE) -C docs linkcheck SPHINXOPTS=$(SPHINXOPTS)
	yapf \
	    --diff \
	    --recursive \
	    --exclude versioneer.py \
	    --exclude src/vws/_version.py \
	    .

.PHONY: fix-lint
fix-lint:
	# Move imports to a single line so that autoflake can handle them.
	# See https://github.com/myint/autoflake/issues/8.
	# Then later we put them back.
	isort --force-single-line --recursive --apply
	autoflake \
	    --in-place \
	    --recursive \
	    --remove-all-unused-imports \
	    --remove-unused-variables \
	    --exclude src/vws/_version.py,versioneer.py \
	    .
	yapf \
	    --in-place \
	    --recursive \
	    --exclude versioneer.py  \
	    --exclude src/vws/_version.py \
	    .
	isort --recursive --apply

.PHONY: docs
docs:
	make -C docs clean html SPHINXOPTS=$(SPHINXOPTS)

.PHONY: open-docs
open-docs:
	xdg-open docs/build/html/index.html >/dev/null 2>&1 || \
	open docs/build/html/index.html >/dev/null 2>&1 || \
	echo "Requires 'xdg-open' or 'open' but neither is available."

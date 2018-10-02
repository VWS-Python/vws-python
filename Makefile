SHELL := /bin/bash -euxo pipefail

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
	yapf \
	    --diff \
	    --recursive \
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
	    .
	yapf \
	    --in-place \
	    --recursive \
	    .
	isort --recursive --apply

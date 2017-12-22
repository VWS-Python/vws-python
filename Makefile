SHELL := /bin/bash -euxo pipefail

.PHONY: lint
lint:
	check-manifest .
	doc8 --config doc8.ini
	dodgy
	flake8 .
	isort --recursive --check-only
	mypy src/ tests/
	pip-extra-reqs src/
	pip-missing-reqs src/
	pydocstyle
	pylint *.py
	pylint src/vws
	pylint src/mock_vws
	pylint --rcfile=tests-pylintrc tests
	pyroma .
	vulture . --min-confidence 100
	yapf --diff --recursive src/ tests/

fix-lint:
	autoflake --in-place --recursive --remove-all-unused-imports --remove-unused-variables .
	yapf --in-place --recursive .
	isort --recursive --apply

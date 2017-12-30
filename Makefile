SHELL := /bin/bash -euxo pipefail

.PHONY: lint
lint:
	check-manifest .
	dodgy
	flake8 .
	isort --recursive --check-only
	mypy src/ tests/
	pip-extra-reqs src/
	pip-missing-reqs src/
	pydocstyle
	pylint *.py
	pylint src
	pylint --rcfile=tests-pylintrc --load-plugins=pylint.extensions.docparams tests/mock_vws/utils.py
	pylint --rcfile=tests-pylintrc tests
	pyroma .
	vulture . --min-confidence 100
	yapf --diff --recursive src/ tests/

fix-lint:
	autoflake --in-place --recursive --remove-all-unused-imports --remove-unused-variables .
	yapf --in-place --recursive .
	isort --recursive --apply

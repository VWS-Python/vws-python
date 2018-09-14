SHELL := /bin/bash -euxo pipefail

.PHONY: lint
lint:
	check-manifest .
	pytest -vvv -x ci/custom_linters.py
	dodgy
	flake8 .
	isort --recursive --check-only
	mypy src/ tests/ ci/
	pip-extra-reqs src/
	pip-missing-reqs src/
	pydocstyle
	pylint *.py src tests ci
	pyroma --min 10 .
	vulture . --min-confidence 100
	yapf --diff --recursive src/ tests/ ci/

.PHONY: fix-lint
fix-lint:
	# autoflake --in-place --recursive --remove-all-unused-imports --remove-unused-variables .
	yapf --in-place --recursive .
	isort --recursive --apply

.PHONY: update-secrets
update-secrets:
	tar cvf secrets.tar ci_secrets/
	travis encrypt-file secrets.tar --add --force
	git add secrets.tar.enc .travis.yml
	git commit -m 'Update secret archive [skip ci]'
	git push

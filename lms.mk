.PHONY: devdata
$(call help,make devdata,"load development data and environment variables")
devdata: build/manifest.json  python
	@tox -qe dev --run-command 'python bin/update_dev_data.py conf/development.ini'

.PHONY: db
$(call help,make db,"upgrade the DB schema to the latest version")
db: args?=upgrade head
db: python
	@tox -qqe dev --run-command 'python bin/initialize_db.py conf/development.ini'
	@tox -qe dev  --run-command 'alembic -c conf/alembic.ini $(args)'

.PHONY: sql
$(call help,make sql,"connect to the dev database with a psql shell")
sql: python
	@tox -qe dockercompose -- exec postgres psql --pset expanded=auto -U postgres

.PHONY: bddtests
sure: bddtests
bddtests: python
	@tox -qe bddtests

# Inform make that lint.txt depends on bddtests.txt
requirements/lint.txt: requirements/bddtests.txt

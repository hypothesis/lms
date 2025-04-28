.PHONY: frontend-lint
$(call help,make frontend-lint,"lint the frontend code")
frontend-lint: node_modules/.uptodate
	@yarn checkformatting
	@yarn lint
	@yarn typecheck

.PHONY: frontend-format
$(call help,make frontend-format,"format the frontend code")
frontend-format: node_modules/.uptodate
	@yarn format

.PHONY: frontend-test
$(call help,make frontend-test,"run the frontend tests")
frontend-test: node_modules/.uptodate
	@yarn test $(ARGS)

build/manifest.json: node_modules/.uptodate
	@yarn build

node_modules/.uptodate: package.json yarn.lock
	@echo installing javascript dependencies
	@yarn install
	@yarn playwright install chromium
	@touch $@

# Make some of the targets from Makefile depend on manifest.json.
dev: build/manifest.json
devdata: build/manifest.json
shell: build/manifest.json
functests: build/manifest.json
sure: build/manifest.json

# Make `make sure` lint and test the frontend code as well.
sure: frontend-lint frontend-test

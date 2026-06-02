.PHONY: docs-lint-governed docs-lint-language docs-lint-code docs-current-design docs-current-plan docs-current-build docs-current-test docs-current-deploy docs-current-operate docs-current-reference runtime-supervisor runtime-supervisor-start runtime-supervisor-stop runtime-supervisor-status runtime-supervisor-logs

docs-lint-governed:
	bash /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/lint_governed_docs.sh

docs-lint-language:
	python /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py language-lint \
	  --root /Users/billyweisberg/Repos/billyweisberg/paa-platform

docs-lint-code:
	python /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py code-lint \
	  --root /Users/billyweisberg/Repos/billyweisberg/paa-platform

docs-current-design:
	python /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py current \
	  --root /Users/billyweisberg/Repos/billyweisberg/paa-platform \
	  --stage design

docs-current-plan:
	python /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py current \
	  --root /Users/billyweisberg/Repos/billyweisberg/paa-platform \
	  --stage plan

docs-current-build:
	python /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py current \
	  --root /Users/billyweisberg/Repos/billyweisberg/paa-platform \
	  --stage build

docs-current-test:
	python /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py current \
	  --root /Users/billyweisberg/Repos/billyweisberg/paa-platform \
	  --stage test

docs-current-deploy:
	python /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py current \
	  --root /Users/billyweisberg/Repos/billyweisberg/paa-platform \
	  --stage deploy

docs-current-operate:
	python /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py current \
	  --root /Users/billyweisberg/Repos/billyweisberg/paa-platform \
	  --stage operate

docs-current-reference:
	python /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/paa_docs.py current \
	  --root /Users/billyweisberg/Repos/billyweisberg/paa-platform \
	  --stage reference

runtime-supervisor:
	/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/run_runtime_supervisor.sh

runtime-supervisor-start:
	/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/runtime_supervisor_ctl.sh start

runtime-supervisor-stop:
	/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/runtime_supervisor_ctl.sh stop || true

runtime-supervisor-status:
	/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/runtime_supervisor_ctl.sh status

runtime-supervisor-logs:
	/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/runtime_supervisor_ctl.sh logs

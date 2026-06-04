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
	PYTHONPATH=packages/paa-core/src:packages/paa-cli/src:packages/paa-consumer/src:. python -m paa_cli runtime start --repo-root /Users/billyweisberg/Repos/billyweisberg/paa-platform

runtime-supervisor-stop:
	PYTHONPATH=packages/paa-core/src:packages/paa-cli/src:packages/paa-consumer/src:. python -m paa_cli runtime stop --repo-root /Users/billyweisberg/Repos/billyweisberg/paa-platform || true

runtime-supervisor-status:
	PYTHONPATH=packages/paa-core/src:packages/paa-cli/src:packages/paa-consumer/src:. python -m paa_cli runtime status --repo-root /Users/billyweisberg/Repos/billyweisberg/paa-platform

runtime-supervisor-logs:
	PYTHONPATH=packages/paa-core/src:packages/paa-cli/src:packages/paa-consumer/src:. python -m paa_cli runtime logs --repo-root /Users/billyweisberg/Repos/billyweisberg/paa-platform

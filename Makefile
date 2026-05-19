.PHONY: docs-lint-governed docs-current-design docs-current-plan docs-current-build docs-current-test docs-current-deploy docs-current-operate docs-current-reference

docs-lint-governed:
	bash /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/lint_governed_docs.sh

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

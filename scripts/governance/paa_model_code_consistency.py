#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check governed model-to-code consistency for selected components.")
    parser.add_argument(
        "--component",
        action="append",
        dest="components",
        required=False,
        help="Component name to check. Repeat for multiple components.",
    )
    parser.add_argument("--profile", default=None, help="PAA DB profile name. Defaults to current runtime profile.")
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[2]
    core_src = repo_root / "packages" / "paa-core" / "src"
    if str(core_src) not in sys.path:
        sys.path.insert(0, str(core_src))

    from paa_core.governance.component_registry import COMPONENT_METADATA_BY_NAME
    from paa_core.governance.model_code_consistency import (
        check_model_code_consistency,
        report_as_jsonable,
    )

    component_names = args.components or [
        "WorkflowLifecycleService",
        "ExecutionPackageResolutionService",
        "ImplementationPlanRepository",
    ]
    reports = check_model_code_consistency(component_names, profile=args.profile)
    print(json.dumps([report_as_jsonable(item) for item in reports], indent=2, sort_keys=True))
    return 1 if any(item.blocking_gaps for item in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_SRC = REPO_ROOT / "packages" / "paa-core" / "src"
if str(CORE_SRC) not in sys.path:
    sys.path.insert(0, str(CORE_SRC))

from paa_core.governance.component_registry import COMPONENT_METADATA_BY_NAME
from paa_core.governance.projection_code_consistency import (
    check_projection_code_consistency,
    report_as_jsonable,
)


DEFAULT_COMPONENTS = (
    "ImplementationPlanRepository",
    "ExecutionPackageResolutionService",
    "WorkflowLifecycleService",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check project-delivery projection to governed code consistency.")
    parser.add_argument("--component", action="append", dest="components", help="Component name to check")
    parser.add_argument("--profile", default=None, help="PAA DB profile override")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    component_names = tuple(args.components or DEFAULT_COMPONENTS)
    reports = check_projection_code_consistency(
        component_names,
        profile=args.profile,
        component_registry=COMPONENT_METADATA_BY_NAME,
    )
    print(json.dumps([report_as_jsonable(report) for report in reports], indent=2, sort_keys=True))
    return 1 if any(report.blocking_gaps for report in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())

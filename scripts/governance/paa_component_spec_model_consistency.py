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

from paa_core.governance.component_spec_model_consistency import (
    check_component_spec_model_consistency,
    report_as_jsonable,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--profile", default=None)
    args = parser.parse_args()

    report = check_component_spec_model_consistency(args.spec, profile=args.profile)
    print(json.dumps(report_as_jsonable(report), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import subprocess
import sys
from typing import Sequence
from typing import Optional

from paa_core.runtime.support.runtime_paths import default_installed_artifact_path
from paa_core.runtime.support.runtime_paths import repo_root_from_cwd

from paa_core.producer.authority_parser import build_authority_parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_authority_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, 'func'):
        parser.print_help()
        sys.exit(2)
    args.func(args)


if __name__ == '__main__':
    main()

"""Producer CLI entrypoints."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from paa_core.config import load_producer_project_config
from paa_core.install import install_producer_runtime
from paa_core.readiness import main as readiness_main
from paa_core.runtime_paths import repo_root_from_cwd
from paa_producer.authority_runtime import main as authority_main
from paa_producer.commands import PRODUCER_COMMANDS
from paa_producer.derive_artifacts import derive_inventory
from paa_producer.issue_loader import load_issue_into_paa
from paa_producer.obligation_loader import materialize_verification_obligations
from paa_producer.publish import publish_from_project_config
from paa_producer.smoke_test import run_smoke_test


def main() -> int:
    parser = argparse.ArgumentParser(prog='paa-producer', allow_abbrev=False)
    parser.add_argument('command', nargs='?', default='help')
    parser.add_argument('--repo-root')
    parser.add_argument('--project-config')
    parser.add_argument('--project-pack')
    args, remainder = parser.parse_known_args()

    if args.command == 'help':
        print('paa-producer')
        print('commands:', ', '.join(PRODUCER_COMMANDS))
        return 0

    if args.command in {'install-producer-runtime', 'update-producer-runtime'}:
        if not args.repo_root:
            parser.error(f'{args.command} requires --repo-root')
        result = install_producer_runtime(
            Path(args.repo_root).resolve(),
            project_pack=args.project_pack or 'fractal-core',
        )
        print(json.dumps({
            'ok': True,
            'install_mode': result.install_mode,
            'repo_root': str(result.repo_root),
            'codex_install_root': str(result.codex_install_root),
            'runtime_data_root': str(result.runtime_data_root),
            'platform_revision': result.platform_revision,
            'project_pack': result.project_pack,
        }, indent=2))
        return 0

    if args.command == 'publish-authority-package':
        if not args.repo_root or not args.project_config:
            parser.error('publish-authority-package requires --repo-root and --project-config')
        repo_root = Path(args.repo_root).resolve()
        config = load_producer_project_config(Path(args.project_config).resolve())
        result = publish_from_project_config(repo_root=repo_root, config=config)
        print(json.dumps({
            'ok': True,
            'package_root': str(result.package_root),
            'metadata_path': str(result.metadata_path),
            'manifest_path': str(result.manifest_path),
            'authority_version': result.authority_version,
        }, indent=2))
        return 0

    if args.command == 'smoke-test':
        repo_root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from_cwd()
        print(json.dumps(run_smoke_test(repo_root), indent=2))
        return 0

    if args.command == 'authority':
        return authority_main(remainder)

    if args.command == 'derive-artifacts':
        repo_root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from_cwd()
        print(json.dumps(derive_inventory(repo_root), indent=2))
        return 0

    if args.command == 'materialize-readiness':
        return readiness_main(remainder)

    if args.command == 'materialize-verification-obligations':
        argp = argparse.ArgumentParser(
            prog='paa-producer materialize-verification-obligations',
            allow_abbrev=False,
        )
        argp.add_argument('--repo-root', default=args.repo_root, required=args.repo_root is None)
        argp.add_argument('--project-config', default=args.project_config, required=args.project_config is None)
        argp.add_argument('--issue-number', required=True, type=int)
        argp.add_argument('--package-path')
        argp.add_argument('--verification-key-prefix')
        argp.add_argument('--scope-authority-label')
        argp.add_argument('--dry-run', action='store_true')
        subargs = argp.parse_args(remainder)
        repo_root = Path(subargs.repo_root).resolve()
        config = load_producer_project_config(Path(subargs.project_config).resolve())
        result = materialize_verification_obligations(
            repo_root=repo_root,
            config=config,
            issue_number=subargs.issue_number,
            package_path=Path(subargs.package_path).resolve() if subargs.package_path else None,
            verification_key_prefix=subargs.verification_key_prefix,
            scope_authority_label=subargs.scope_authority_label,
            dry_run=subargs.dry_run,
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.command == 'load-issue-into-paa':
        argp = argparse.ArgumentParser(
            prog='paa-producer load-issue-into-paa',
            allow_abbrev=False,
        )
        argp.add_argument('--repo-root', default=args.repo_root, required=args.repo_root is None)
        argp.add_argument('--project-config', default=args.project_config, required=args.project_config is None)
        argp.add_argument('--issue-number', required=True, type=int)
        argp.add_argument('--verification-key-prefix')
        argp.add_argument('--scope-authority-label')
        argp.add_argument('--dry-run', action='store_true')
        subargs = argp.parse_args(remainder)
        repo_root = Path(subargs.repo_root).resolve()
        config = load_producer_project_config(Path(subargs.project_config).resolve())
        result = load_issue_into_paa(
            repo_root=repo_root,
            config=config,
            issue_number=subargs.issue_number,
            verification_key_prefix=subargs.verification_key_prefix,
            scope_authority_label=subargs.scope_authority_label,
            dry_run=subargs.dry_run,
        )
        print(json.dumps(result, indent=2))
        return 0

    print(f'unknown command: {args.command}')
    return 2


if __name__ == '__main__':
    raise SystemExit(main())

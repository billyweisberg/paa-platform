"""Consumer CLI entrypoints."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from paa_core.install import install_consumer_runtime
from paa_consumer.authority_install import install_authority
from paa_consumer.commands import CONSUMER_COMMANDS
from paa_consumer.inbox import run_queue_command
from paa_consumer.runtime_guardrails import validate
from paa_consumer.smoke_test import run_smoke_test
from paa_consumer.techlead import main as techlead_main


def main() -> int:
    parser = argparse.ArgumentParser(prog='paa-consumer', allow_abbrev=False)
    parser.add_argument('command', nargs='?', default='help')
    parser.add_argument('--repo-root')
    parser.add_argument('--package-root')
    parser.add_argument('--project-pack')
    parser.add_argument('--authority-install-root')
    parser.add_argument('--queue')
    parser.add_argument('--claim-id')
    args, remainder = parser.parse_known_args()

    if args.command == 'help':
        print('paa-consumer')
        print('commands:', ', '.join(CONSUMER_COMMANDS))
        return 0

    if args.command in {'install-consumer-runtime', 'update-consumer-runtime'}:
        if not args.repo_root:
            parser.error(f'{args.command} requires --repo-root')
        result = install_consumer_runtime(
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

    if args.command == 'install-authority-package':
        if not args.repo_root or not args.package_root:
            parser.error('install-authority-package requires --repo-root and --package-root')
        destination = Path(args.authority_install_root).resolve() if args.authority_install_root else None
        print(json.dumps(install_authority(Path(args.repo_root).resolve(), Path(args.package_root).resolve(), destination), indent=2))
        return 0

    if args.command == 'smoke-test':
        argp = argparse.ArgumentParser(
            prog='paa-consumer smoke-test',
            allow_abbrev=False,
        )
        argp.add_argument('--repo-root', default=args.repo_root)
        argp.add_argument('--expected-branch')
        argp.add_argument('--validate-schema', action='store_true')
        argp.add_argument('--output')
        subargs = argp.parse_args(remainder)
        repo_root = Path(subargs.repo_root or Path.cwd()).resolve()
        output_path = Path(subargs.output).resolve() if subargs.output else None
        print(json.dumps(
            run_smoke_test(
                repo_root,
                expected_branch=subargs.expected_branch,
                validate_schema_flag=subargs.validate_schema,
                output_path=output_path,
            ),
            indent=2,
        ))
        return 0

    if args.command == 'queue-check':
        if not args.repo_root or not args.queue:
            parser.error('queue-check requires --repo-root and --queue')
        return run_queue_command(Path(args.repo_root).resolve(), ['check', '--queue', args.queue, *remainder])

    if args.command == 'queue-claim-next':
        if not args.repo_root or not args.queue:
            parser.error('queue-claim-next requires --repo-root and --queue')
        return run_queue_command(Path(args.repo_root).resolve(), ['claim-next', '--queue', args.queue, *remainder])

    if args.command == 'queue-list-claims':
        if not args.repo_root:
            parser.error('queue-list-claims requires --repo-root')
        argv = ['list-claims']
        if args.queue:
            argv += ['--queue', args.queue]
        return run_queue_command(Path(args.repo_root).resolve(), argv + remainder)

    if args.command == 'queue-ack':
        if not args.repo_root or not args.claim_id:
            parser.error('queue-ack requires --repo-root and --claim-id')
        return run_queue_command(Path(args.repo_root).resolve(), ['ack', '--claim-id', args.claim_id, *remainder])

    if args.command == 'queue-requeue':
        if not args.repo_root or not args.claim_id:
            parser.error('queue-requeue requires --repo-root and --claim-id')
        return run_queue_command(Path(args.repo_root).resolve(), ['requeue', '--claim-id', args.claim_id, *remainder])

    if args.command == 'techlead-status':
        return techlead_main([*remainder])

    if args.command == 'validate-runtime':
        repo_root = Path(args.repo_root or Path.cwd()).resolve()
        print(json.dumps(validate(repo_root), indent=2))
        return 0

    print(f'unknown command: {args.command}')
    return 2


if __name__ == '__main__':
    raise SystemExit(main())

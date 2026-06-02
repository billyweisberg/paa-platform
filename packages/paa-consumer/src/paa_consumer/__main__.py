"""Consumer CLI entrypoints."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from paa_core.install import install_consumer_runtime
from paa_core import handoff_runtime
from paa_core.runtime_paths import repo_root_from_cwd
from paa_consumer.authority_install import install_authority
from paa_consumer.commands import CONSUMER_COMMANDS
from paa_consumer.hosts import build_dev_runtime_host, build_qa_runtime_host, build_techlead_runtime_host
from paa_consumer.inbox import dispatch_techlead_packet, resolve_techlead_packet_queue, run_queue_command
from paa_consumer.techlead_service_map import build_techlead_service_map
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
    parser.add_argument('--message-file')
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
        repo_root = Path(subargs.repo_root).resolve() if subargs.repo_root else repo_root_from_cwd()
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

    if args.command == 'queue-state-info':
        if not args.repo_root:
            parser.error('queue-state-info requires --repo-root')
        return run_queue_command(Path(args.repo_root).resolve(), ['state-info', *remainder])

    if args.command == 'queue-ensure-topology':
        if not args.repo_root:
            parser.error('queue-ensure-topology requires --repo-root')
        return run_queue_command(Path(args.repo_root).resolve(), ['ensure-topology', *remainder])

    if args.command == 'queue-check':
        if not args.repo_root or not args.queue:
            parser.error('queue-check requires --repo-root and --queue')
        return run_queue_command(Path(args.repo_root).resolve(), ['check', '--queue', args.queue, *remainder])

    if args.command == 'queue-validate':
        if not args.repo_root or not args.message_file:
            parser.error('queue-validate requires --repo-root and --message-file')
        return run_queue_command(Path(args.repo_root).resolve(), ['validate', '--message-file', args.message_file, *remainder])

    if args.command == 'queue-send':
        if not args.repo_root or not args.queue or not args.message_file:
            parser.error('queue-send requires --repo-root, --queue, and --message-file')
        return run_queue_command(Path(args.repo_root).resolve(), ['send', '--queue', args.queue, '--message-file', args.message_file, *remainder])

    if args.command == 'techlead-validate-packet':
        if not args.message_file:
            parser.error('techlead-validate-packet requires --message-file')
        message = handoff_runtime.load_json(Path(args.message_file).resolve())
        errors = handoff_runtime.validate_envelope(message, require_authority=True)
        if errors:
            print(json.dumps({
                'ok': False,
                'message_file': str(Path(args.message_file).resolve()),
                'resolved_queue': None,
                'errors': errors,
            }, indent=2))
            return 1
        print(json.dumps({
            'ok': True,
            'message_file': str(Path(args.message_file).resolve()),
            'message_id': message.get('message_id'),
            'schema_type': message.get('schema_type'),
            'resolved_queue': resolve_techlead_packet_queue(
                message,
                repo_root=Path(args.repo_root).resolve() if args.repo_root else repo_root_from_cwd(),
            ),
            'from_role': message.get('from_role'),
            'to_role': message.get('to_role'),
        }, indent=2))
        return 0

    if args.command == 'techlead-send-packet':
        if not args.repo_root or not args.message_file:
            parser.error('techlead-send-packet requires --repo-root and --message-file')
        result = dispatch_techlead_packet(Path(args.repo_root).resolve(), Path(args.message_file).resolve())
        print(json.dumps(result, indent=2))
        return 0 if result.get('ok') else 1

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

    if args.command == 'automation-preflight':
        argv = ['automation-preflight', '--repo-root', args.repo_root or str(repo_root_from_cwd())]
        return techlead_main(argv + remainder)

    if args.command == 'techlead-service-map':
        print(json.dumps(build_techlead_service_map(), indent=2))
        return 0

    if args.command == 'techlead-runtime':
        argp = argparse.ArgumentParser(
            prog='paa-consumer techlead-runtime',
            allow_abbrev=False,
        )
        argp.add_argument('--repo-root', type=Path, default=args.repo_root)
        argp.add_argument('--actor-name', default='TechLead Agent')
        argp.add_argument('--host-name', default='techlead-runtime-host')
        argp.add_argument('--intake-mode', choices=['preview', 'claim_next'], default='preview')
        argp.add_argument('--emit-next-assignment', action='store_true')
        argp.add_argument('--max-iterations', type=int, default=1)
        argp.add_argument('--poll-interval-seconds', type=float, default=5.0)
        subargs = argp.parse_args(remainder)
        repo_root = Path(subargs.repo_root).resolve() if subargs.repo_root else repo_root_from_cwd()
        host = build_techlead_runtime_host(
            repo_root,
            actor_name=subargs.actor_name,
            host_name=subargs.host_name,
        )
        print(json.dumps(
            host.run_loop(
                intake_mode=subargs.intake_mode,
                emit_next_assignment=subargs.emit_next_assignment,
                max_iterations=subargs.max_iterations,
                poll_interval_seconds=subargs.poll_interval_seconds,
            ),
            indent=2,
        ))
        return 0

    if args.command == 'dev-runtime':
        argp = argparse.ArgumentParser(
            prog='paa-consumer dev-runtime',
            allow_abbrev=False,
        )
        argp.add_argument('--repo-root', type=Path, default=args.repo_root)
        argp.add_argument('--actor-name', default='Dev Agent')
        argp.add_argument('--host-name', default='dev-runtime-host')
        argp.add_argument('--intake-mode', choices=['preview', 'claim_next'], default='preview')
        argp.add_argument('--emit-worker-result', action='store_true')
        argp.add_argument('--max-iterations', type=int, default=1)
        argp.add_argument('--poll-interval-seconds', type=float, default=5.0)
        subargs = argp.parse_args(remainder)
        repo_root = Path(subargs.repo_root).resolve() if subargs.repo_root else repo_root_from_cwd()
        host = build_dev_runtime_host(
            repo_root,
            actor_name=subargs.actor_name,
            host_name=subargs.host_name,
        )
        print(json.dumps(
            host.run_loop(
                intake_mode=subargs.intake_mode,
                emit_worker_result=subargs.emit_worker_result,
                max_iterations=subargs.max_iterations,
                poll_interval_seconds=subargs.poll_interval_seconds,
            ),
            indent=2,
        ))
        return 0

    if args.command == 'qa-runtime':
        argp = argparse.ArgumentParser(
            prog='paa-consumer qa-runtime',
            allow_abbrev=False,
        )
        argp.add_argument('--repo-root', type=Path, default=args.repo_root)
        argp.add_argument('--actor-name', default='QA Agent')
        argp.add_argument('--host-name', default='qa-runtime-host')
        argp.add_argument('--intake-mode', choices=['preview', 'claim_next'], default='preview')
        argp.add_argument('--emit-verification', action='store_true')
        argp.add_argument('--max-iterations', type=int, default=1)
        argp.add_argument('--poll-interval-seconds', type=float, default=5.0)
        subargs = argp.parse_args(remainder)
        repo_root = Path(subargs.repo_root).resolve() if subargs.repo_root else repo_root_from_cwd()
        host = build_qa_runtime_host(
            repo_root,
            actor_name=subargs.actor_name,
            host_name=subargs.host_name,
        )
        print(json.dumps(
            host.run_loop(
                intake_mode=subargs.intake_mode,
                emit_verification=subargs.emit_verification,
                max_iterations=subargs.max_iterations,
                poll_interval_seconds=subargs.poll_interval_seconds,
            ),
            indent=2,
        ))
        return 0

    if args.command == 'techlead-status':
        return techlead_main(['status', *remainder])

    if args.command == 'techlead-emit-next-assignment':
        argv = ['emit-next-assignment', '--repo-root', args.repo_root or str(repo_root_from_cwd())]
        return techlead_main(argv + remainder)

    if args.command == 'techlead-lineage':
        argv = ['lineage', '--repo-root', args.repo_root or str(repo_root_from_cwd())]
        return techlead_main(argv + remainder)

    if args.command == 'techlead-prepare-role-branch':
        argv = ['prepare-role-branch', '--repo-root', args.repo_root or str(repo_root_from_cwd())]
        return techlead_main(argv + remainder)

    if args.command == 'techlead-prepare-role-worktree':
        argv = ['prepare-role-worktree', '--repo-root', args.repo_root or str(repo_root_from_cwd())]
        return techlead_main(argv + remainder)

    if args.command == 'techlead-handoff-to-role-worktree':
        argv = ['handoff-to-role-worktree', '--repo-root', args.repo_root or str(repo_root_from_cwd())]
        return techlead_main(argv + remainder)

    if args.command == 'techlead-inspect-role-worktree':
        argv = ['inspect-role-worktree', '--repo-root', args.repo_root or str(repo_root_from_cwd())]
        return techlead_main(argv + remainder)

    if args.command == 'techlead-worktree-ownership':
        argv = ['worktree-ownership', '--repo-root', args.repo_root or str(repo_root_from_cwd())]
        return techlead_main(argv + remainder)

    if args.command == 'techlead-worktree-stale':
        argv = ['worktree-stale', '--repo-root', args.repo_root or str(repo_root_from_cwd())]
        return techlead_main(argv + remainder)

    if args.command == 'techlead-reset-required':
        argv = ['reset-required', '--repo-root', args.repo_root or str(repo_root_from_cwd())]
        return techlead_main(argv + remainder)

    if args.command == 'techlead-reset-cleanup':
        argv = ['reset-cleanup', '--repo-root', args.repo_root or str(repo_root_from_cwd())]
        return techlead_main(argv + remainder)

    if args.command == 'techlead-superseded-cleanup':
        argv = ['superseded-cleanup', '--repo-root', args.repo_root or str(repo_root_from_cwd())]
        return techlead_main(argv + remainder)

    if args.command == 'techlead-closed-cleanup':
        argv = ['closed-cleanup', '--repo-root', args.repo_root or str(repo_root_from_cwd())]
        return techlead_main(argv + remainder)

    if args.command == 'techlead-role-entry':
        argv = ['role-entry', '--repo-root', args.repo_root or str(repo_root_from_cwd())]
        return techlead_main(argv + remainder)

    if args.command == 'techlead-role-result-assist':
        argv = ['role-result-assist', '--repo-root', args.repo_root or str(repo_root_from_cwd())]
        return techlead_main(argv + remainder)

    if args.command == 'techlead-role-return':
        argv = ['role-return', '--repo-root', args.repo_root or str(repo_root_from_cwd())]
        return techlead_main(argv + remainder)

    if args.command == 'techlead-emit-decision':
        argv = ['emit-decision', '--repo-root', args.repo_root or str(repo_root_from_cwd())]
        return techlead_main(argv + remainder)

    if args.command == 'techlead-closeout-qa-pass':
        argv = ['closeout-qa-pass', '--repo-root', args.repo_root or str(repo_root_from_cwd())]
        return techlead_main(argv + remainder)

    if args.command == 'techlead-accept-and-merge':
        argv = ['accept-and-merge', '--repo-root', args.repo_root or str(repo_root_from_cwd())]
        return techlead_main(argv + remainder)

    if args.command == 'validate-runtime':
        repo_root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from_cwd()
        print(json.dumps(validate(repo_root), indent=2))
        return 0

    print(f'unknown command: {args.command}')
    return 2


if __name__ == '__main__':
    raise SystemExit(main())

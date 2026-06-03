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
from paa_producer.architect_packet_preparer import PacketPreparationOptions, prepare_architect_packet
from paa_producer.brief_target_author import author_brief_targets
from paa_producer.coder_brief_assembler import assemble_coder_brief
from paa_producer.brief_reviewer import review_coder_brief
from paa_core.producer.commands import PRODUCER_COMMANDS
from paa_producer.derivation_readiness import evaluate_derivation_readiness
from paa_producer.design_package_deriver import derive_design_package
from paa_producer.implementation_plan_deriver import derive_implementation_plan
from paa_core.producer.derive_artifacts import derive_inventory
from paa_core.producer.issue_loader import load_issue_into_paa
from paa_producer.component_spec_materializer import (
    DEFAULT_ANCHOR_CONSUMER_CONTEXT_KEY,
    DEFAULT_ANCHOR_DESIGN_PACKAGE_EXTERNAL,
    DEFAULT_PROJECT_SLUG,
    materialize_component_spec,
)
from paa_producer.implementation_plan_progress import (
    derive_next_activity_bundle,
    implementation_plan_progress,
    reconcile_implementation_plan_progress,
)
from paa_producer.implementation_plan_activity_state import (
    set_implementation_plan_activity_state,
)
from paa_core.producer.obligation_loader import materialize_verification_obligations
from paa_core.producer.publish import publish_from_project_config
from paa_core.producer.smoke_test import run_smoke_test


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
        result = authority_main(remainder)
        return int(result) if result is not None else 0

    if args.command == 'derive-artifacts':
        repo_root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from_cwd()
        print(json.dumps(derive_inventory(repo_root), indent=2))
        return 0

    if args.command == 'derive-design-package':
        argp = argparse.ArgumentParser(
            prog='paa-producer derive-design-package',
            allow_abbrev=False,
        )
        argp.add_argument('--repo-root', default=args.repo_root)
        argp.add_argument('--design-package', required=True)
        argp.add_argument('--schema-path')
        argp.add_argument('--project-slug')
        argp.add_argument('--project-name')
        argp.add_argument('--dry-run', action='store_true')
        subargs = argp.parse_args(remainder)
        repo_root = Path(subargs.repo_root).resolve() if subargs.repo_root else repo_root_from_cwd()
        result = derive_design_package(
            package_path=Path(subargs.design_package).resolve(),
            schema_path=Path(subargs.schema_path).resolve() if subargs.schema_path else None,
            project_slug=subargs.project_slug,
            project_name=subargs.project_name,
            repo_root=repo_root,
            dry_run=subargs.dry_run,
        )
        print(json.dumps({
            'ok': True,
            'project_slug': result.project_slug,
            'package_id': result.package_id,
            'package_path': result.package_path,
            'schema_path': result.schema_path,
            'authority_version': result.authority_version,
            'project_id': result.project_id,
            'authority_version_id': result.authority_version_id,
            'spec_fragment_id': result.spec_fragment_id,
            'implementation_target_id': result.implementation_target_id,
            'component_id': result.component_id,
            'work_item_id': result.work_item_id,
            'design_package_id': result.design_package_id,
            'dry_run': result.dry_run,
        }, indent=2))
        return 0

    if args.command == 'evaluate-derivation-readiness':
        argp = argparse.ArgumentParser(
            prog='paa-producer evaluate-derivation-readiness',
            allow_abbrev=False,
        )
        argp.add_argument('--design-package', required=True)
        argp.add_argument('--schema-path')
        argp.add_argument('--project-slug')
        subargs = argp.parse_args(remainder)
        result = evaluate_derivation_readiness(
            package_path=Path(subargs.design_package).resolve(),
            schema_path=Path(subargs.schema_path).resolve() if subargs.schema_path else None,
            project_slug=subargs.project_slug,
        )
        print(json.dumps({
            'ok': True,
            'project_slug': result.project_slug,
            'package_id': result.package_id,
            'package_path': result.package_path,
            'schema_path': result.schema_path,
            'design_package_id': result.design_package_id,
            'work_item_id': result.work_item_id,
            'authority_version_id': result.authority_version_id,
            'spec_fragment_id': result.spec_fragment_id,
            'implementation_target_id': result.implementation_target_id,
            'component_id': result.component_id,
            'primary_component_name': result.primary_component_name,
            'readiness_class': result.readiness_class,
            'ready': result.ready,
            'blockers': result.blockers,
            'warnings': result.warnings,
            'checks': result.checks,
            'recommendations': result.recommendations,
            'evaluation_mode': result.evaluation_mode,
        }, indent=2))
        return 0

    if args.command == 'derive-implementation-plan':
        argp = argparse.ArgumentParser(
            prog='paa-producer derive-implementation-plan',
            allow_abbrev=False,
        )
        argp.add_argument('--design-package', required=True)
        argp.add_argument('--package-schema-path')
        argp.add_argument('--project-slug')
        argp.add_argument('--consumer-context-key', default='python')
        argp.add_argument('--output')
        argp.add_argument('--no-persist-db', action='store_true')
        subargs = argp.parse_args(remainder)
        result = derive_implementation_plan(
            package_path=Path(subargs.design_package).resolve(),
            package_schema_path=Path(subargs.package_schema_path).resolve() if subargs.package_schema_path else None,
            project_slug=subargs.project_slug,
            consumer_context_key=subargs.consumer_context_key,
            output_path=Path(subargs.output).resolve() if subargs.output else None,
            persist_db=not subargs.no_persist_db,
        )
        print(json.dumps({
            'ok': True,
            'project_slug': result.project_slug,
            'package_id': result.package_id,
            'package_path': result.package_path,
            'design_package_id': result.design_package_id,
            'implementation_plan_id': result.implementation_plan_id,
            'plan_id_external': result.plan_id_external,
            'consumer_context_key': result.consumer_context_key,
            'activity_count': result.activity_count,
            'dependency_count': result.dependency_count,
            'verification_surface_count': result.verification_surface_count,
            'output_path': result.output_path,
            'persisted': result.persisted,
            'implementation_plan_id': result.implementation_plan_id,
        }, indent=2))
        return 0

    if args.command == 'materialize-component-spec':
        argp = argparse.ArgumentParser(
            prog='paa-producer materialize-component-spec',
            allow_abbrev=False,
        )
        argp.add_argument('--spec', required=True)
        argp.add_argument('--project-slug', default=DEFAULT_PROJECT_SLUG)
        argp.add_argument(
            '--anchor-design-package-external',
            default=DEFAULT_ANCHOR_DESIGN_PACKAGE_EXTERNAL,
        )
        argp.add_argument(
            '--anchor-consumer-context-key',
            default=DEFAULT_ANCHOR_CONSUMER_CONTEXT_KEY,
        )
        subargs = argp.parse_args(remainder)
        result = materialize_component_spec(
            spec_path=Path(subargs.spec).resolve(),
            project_slug=subargs.project_slug,
            anchor_design_package_external=subargs.anchor_design_package_external,
            anchor_consumer_context_key=subargs.anchor_consumer_context_key,
        )
        print(json.dumps({
            'source_path': result.source_path,
            'project_id': result.project_id,
            'design_package_id': result.design_package_id,
            'component_id': result.component_id,
            'implementation_plan_id': result.implementation_plan_id,
            'plan_id_external': result.plan_id_external,
            'consumer_context_key': result.consumer_context_key,
            'component_element_keys': result.component_element_keys,
            'realization_keys': result.realization_keys,
            'activity_keys': result.activity_keys,
        }, indent=2))
        return 0

    if args.command == 'implementation-plan-progress':
        argp = argparse.ArgumentParser(
            prog='paa-producer implementation-plan-progress',
            allow_abbrev=False,
        )
        argp.add_argument('--plan-id', required=True)
        subargs = argp.parse_args(remainder)
        print(json.dumps(implementation_plan_progress(plan_id=subargs.plan_id), indent=2))
        return 0

    if args.command == 'set-implementation-plan-activity-state':
        argp = argparse.ArgumentParser(
            prog='paa-producer set-implementation-plan-activity-state',
            allow_abbrev=False,
        )
        argp.add_argument('--plan-id', required=True)
        argp.add_argument('--activity-key', required=True)
        argp.add_argument('--activity-state', required=True)
        argp.add_argument('--blocking-reason')
        argp.add_argument('--started-at')
        argp.add_argument('--completed-at')
        argp.add_argument('--metadata-json')
        subargs = argp.parse_args(remainder)
        try:
            result = set_implementation_plan_activity_state(
                plan_id=subargs.plan_id,
                activity_key=subargs.activity_key,
                activity_state=subargs.activity_state,
                blocking_reason=subargs.blocking_reason,
                started_at=subargs.started_at,
                completed_at=subargs.completed_at,
                metadata_json=subargs.metadata_json,
            )
        except ValueError as exc:
            argp.error(str(exc))
        print(json.dumps(result, indent=2))
        return 0

    if args.command == 'derive-next-activity-bundle':
        argp = argparse.ArgumentParser(
            prog='paa-producer derive-next-activity-bundle',
            allow_abbrev=False,
        )
        argp.add_argument('--plan-id', required=True)
        subargs = argp.parse_args(remainder)
        print(json.dumps(derive_next_activity_bundle(plan_id=subargs.plan_id), indent=2))
        return 0

    if args.command == 'reconcile-implementation-plan-progress':
        argp = argparse.ArgumentParser(
            prog='paa-producer reconcile-implementation-plan-progress',
            allow_abbrev=False,
        )
        argp.add_argument('--plan-id', required=True)
        subargs = argp.parse_args(remainder)
        print(json.dumps(reconcile_implementation_plan_progress(plan_id=subargs.plan_id), indent=2))
        return 0

    if args.command == 'assemble-coder-brief':
        argp = argparse.ArgumentParser(
            prog='paa-producer assemble-coder-brief',
            allow_abbrev=False,
        )
        argp.add_argument('--design-package', required=True)
        argp.add_argument('--package-schema-path')
        argp.add_argument('--brief-schema-path')
        argp.add_argument('--project-slug')
        argp.add_argument('--output')
        argp.add_argument('--no-persist-db', action='store_true')
        subargs = argp.parse_args(remainder)
        result = assemble_coder_brief(
            package_path=Path(subargs.design_package).resolve(),
            package_schema_path=Path(subargs.package_schema_path).resolve() if subargs.package_schema_path else None,
            brief_schema_path=Path(subargs.brief_schema_path).resolve() if subargs.brief_schema_path else None,
            project_slug=subargs.project_slug,
            output_path=Path(subargs.output).resolve() if subargs.output else None,
            persist_db=not subargs.no_persist_db,
        )
        print(json.dumps({
            'ok': True,
            'project_slug': result.project_slug,
            'package_id': result.package_id,
            'brief_id': result.brief_id,
            'package_path': result.package_path,
            'schema_path': result.schema_path,
            'output_path': result.output_path,
            'coder_run_brief_id': result.coder_run_brief_id,
            'design_package_id': result.design_package_id,
            'work_item_id': result.work_item_id,
            'authority_state': result.authority_state,
            'readiness_class': result.readiness_class,
            'persisted': result.persisted,
            'implementation_plan_id': result.implementation_plan_id,
        }, indent=2))
        return 0

    if args.command == 'author-brief-targets':
        argp = argparse.ArgumentParser(
            prog='paa-producer author-brief-targets',
            allow_abbrev=False,
        )
        argp.add_argument('--design-package', required=True)
        argp.add_argument('--package-schema-path')
        argp.add_argument('--brief-schema-path')
        argp.add_argument('--project-slug')
        argp.add_argument('--output')
        subargs = argp.parse_args(remainder)
        result = author_brief_targets(
            package_path=Path(subargs.design_package).resolve(),
            package_schema_path=Path(subargs.package_schema_path).resolve() if subargs.package_schema_path else None,
            brief_schema_path=Path(subargs.brief_schema_path).resolve() if subargs.brief_schema_path else None,
            project_slug=subargs.project_slug,
            output_path=Path(subargs.output).resolve() if subargs.output else None,
        )
        print(json.dumps({
            'ok': True,
            'project_slug': result.project_slug,
            'package_id': result.package_id,
            'package_path': result.package_path,
            'design_package_id': result.design_package_id,
            'coder_run_brief_id': result.coder_run_brief_id,
            'brief_id': result.brief_id,
            'component_id': result.component_id,
            'work_item_id': result.work_item_id,
            'readiness_class': result.readiness_class,
            'output_path': result.output_path,
            'component_element_keys': result.component_element_keys,
            'realization_keys': result.realization_keys,
            'target_ids': result.target_ids,
            'target_count': result.target_count,
            'persisted': result.persisted,
        }, indent=2))
        return 0

    if args.command == 'review-coder-brief':
        argp = argparse.ArgumentParser(
            prog='paa-producer review-coder-brief',
            allow_abbrev=False,
        )
        argp.add_argument('--coder-run-brief-id')
        argp.add_argument('--design-package')
        argp.add_argument('--decision', required=True, choices=('approve', 'reject', 'reopen-draft'))
        argp.add_argument('--notes')
        argp.add_argument('--review-summary')
        argp.add_argument('--output')
        subargs = argp.parse_args(remainder)
        if not subargs.coder_run_brief_id and not subargs.design_package:
            argp.error('review-coder-brief requires --coder-run-brief-id or --design-package')
        result = review_coder_brief(
            coder_run_brief_id=subargs.coder_run_brief_id,
            design_package_path=Path(subargs.design_package).resolve() if subargs.design_package else None,
            decision=subargs.decision,
            notes=subargs.notes,
            review_summary=subargs.review_summary,
            output_path=Path(subargs.output).resolve() if subargs.output else None,
        )
        print(json.dumps({
            'ok': True,
            'project_slug': result.project_slug,
            'coder_run_brief_id': result.coder_run_brief_id,
            'brief_id': result.brief_id,
            'authority_state': result.authority_state,
            'status': result.status,
            'decision': result.decision,
            'transition_applied': result.transition_applied,
            'target_count': result.target_count,
            'approval_json': result.approval_json,
            'output_path': result.output_path,
            'checks': result.checks,
        }, indent=2))
        return 0

    if args.command == 'prepare-architect-packet':
        argp = argparse.ArgumentParser(
            prog='paa-producer prepare-architect-packet',
            allow_abbrev=False,
        )
        argp.add_argument('--manifest-path', required=True)
        argp.add_argument('--design-package', required=True)
        argp.add_argument('--packet-output', required=True)
        argp.add_argument('--brief-output', required=True)
        argp.add_argument('--repo', required=True)
        argp.add_argument('--branch', default='main')
        argp.add_argument('--accepted-pr-number', type=int, required=True)
        argp.add_argument('--accepted-pr-url', required=True)
        argp.add_argument('--closed-issue-number', type=int, required=True)
        argp.add_argument('--closed-issue-url', required=True)
        argp.add_argument('--next-issue-number', type=int, required=True)
        argp.add_argument('--next-issue-url', required=True)
        argp.add_argument('--baseline-file', required=True)
        argp.add_argument('--review-output')
        argp.add_argument('--schema-path')
        argp.add_argument('--project-slug')
        argp.add_argument('--packet-project')
        argp.add_argument('--remaining-gap')
        argp.add_argument('--next-move', action='append')
        argp.add_argument('--focus', action='append')
        argp.add_argument('--keep-stable', action='append')
        argp.add_argument('--governance-reminder', action='append')
        argp.add_argument('--pr-starter-branch')
        argp.add_argument('--pr-starter-title')
        argp.add_argument('--pr-starter-body-linkage')
        argp.add_argument('--message-id')
        argp.add_argument('--correlation-id')
        argp.add_argument('--created-at')
        subargs = argp.parse_args(remainder)
        result = prepare_architect_packet(
            options=PacketPreparationOptions(
                manifest_path=Path(subargs.manifest_path).resolve(),
                package_path=Path(subargs.design_package).resolve(),
                packet_output_path=Path(subargs.packet_output).resolve(),
                brief_output_path=Path(subargs.brief_output).resolve(),
                repo=subargs.repo,
                branch=subargs.branch,
                accepted_pr_number=subargs.accepted_pr_number,
                accepted_pr_url=subargs.accepted_pr_url,
                closed_issue_number=subargs.closed_issue_number,
                closed_issue_url=subargs.closed_issue_url,
                next_issue_number=subargs.next_issue_number,
                next_issue_url=subargs.next_issue_url,
                baseline_file=Path(subargs.baseline_file).resolve(),
                review_output_path=Path(subargs.review_output).resolve() if subargs.review_output else None,
                schema_path=Path(subargs.schema_path).resolve() if subargs.schema_path else None,
                project_slug=subargs.project_slug,
                packet_project=subargs.packet_project,
                remaining_gap=subargs.remaining_gap,
                next_move=tuple(subargs.next_move or ()),
                focus=tuple(subargs.focus or ()),
                keep_stable=tuple(subargs.keep_stable or ()),
                governance_reminder=tuple(subargs.governance_reminder or ()),
                pr_starter_branch=subargs.pr_starter_branch,
                pr_starter_title=subargs.pr_starter_title,
                pr_starter_body_linkage=subargs.pr_starter_body_linkage,
                message_id=subargs.message_id,
                correlation_id=subargs.correlation_id,
                created_at=subargs.created_at,
            )
        )
        print(json.dumps({
            'ok': True,
            'project_slug': result.project_slug,
            'package_id_external': result.package_id_external,
            'coder_run_brief_id': result.coder_run_brief_id,
            'brief_id_external': result.brief_id_external,
            'authority_state': result.authority_state,
            'status': result.status,
            'transition_applied': result.transition_applied,
            'packet_output_path': result.packet_output_path,
            'brief_output_path': result.brief_output_path,
            'review_output_path': result.review_output_path,
            'packet_schema_path': result.packet_schema_path,
            'brief_schema_path': result.brief_schema_path,
            'message_id': result.message_id,
            'target_count': result.target_count,
            'packet_preparation_json': result.packet_preparation_json,
            'checks': result.checks,
        }, indent=2))
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

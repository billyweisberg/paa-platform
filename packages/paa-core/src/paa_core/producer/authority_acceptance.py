from __future__ import annotations

from datetime import datetime, timezone
import json
import sys
from typing import Any

from paa_core.producer.authority_queries import bump_authority_version, publish_authority, task_or_die
from paa_core.producer.authority_resolution import find_task
from paa_core.producer.authority_support import load_manifest, run_psql, sql_literal, write_manifest


def persist_architect_acceptance(
    *,
    project_slug: str,
    completed_issue_number: int | None,
    completed_task_id: str,
    next_issue_number: int | None,
    next_task_id: str | None,
    authority_version: str,
    published_at: str,
    merge_commit_sha: str | None = None,
    pr_number: int | None = None,
) -> None:
    if next_task_id:
        notes = (
            f'Architect accepted task {completed_task_id} and advanced authority to '
            f'{next_task_id} (issue #{next_issue_number}).'
        )
    else:
        notes = f'Architect accepted terminal task {completed_task_id}; no successor task remained.'
    metadata = json.dumps({
        'source': 'project_authority.py',
        'completed_task_id': completed_task_id,
        'completed_issue_number': completed_issue_number,
        'next_task_id': next_task_id,
        'next_issue_number': next_issue_number,
        'authority_version': authority_version,
        'pr_number': pr_number,
    })
    sql = f"""
    WITH project AS (
      SELECT project_id FROM paa.projects WHERE slug = {sql_literal(project_slug)}
    ), architect_role AS (
      SELECT role_id FROM paa.roles r JOIN project p ON p.project_id = r.project_id
      WHERE r.name = 'Architect'
      LIMIT 1
    ), architect_agent AS (
      SELECT agent_id FROM paa.agents a JOIN project p ON p.project_id = a.project_id
      WHERE a.name = 'Fractal Core Architect Automation'
      LIMIT 1
    ), current_work_item AS (
      SELECT wi.work_item_id
      FROM paa.work_items wi
      JOIN project p ON p.project_id = wi.project_id
      WHERE wi.issue_number = {sql_literal(completed_issue_number)}
      LIMIT 1
    ), next_work_item AS (
      SELECT wi.work_item_id
      FROM paa.work_items wi
      JOIN project p ON p.project_id = wi.project_id
      WHERE wi.issue_number = {sql_literal(next_issue_number)}
      LIMIT 1
    ), existing_version AS (
      SELECT authority_version_id FROM paa.authority_versions av
      JOIN project p ON p.project_id = av.project_id
      WHERE av.version_label = {sql_literal(authority_version)}
      LIMIT 1
    ), upsert_version AS (
      INSERT INTO paa.authority_versions (
        project_id,
        version_label,
        published_at,
        status,
        notes
      )
      SELECT
        project.project_id,
        {sql_literal(authority_version)},
        {sql_literal(published_at)}::timestamptz,
        'published'::paa.authority_status,
        {sql_literal(f'Authority advanced after acceptance of {completed_task_id}.')}
      FROM project
      WHERE NOT EXISTS (SELECT 1 FROM existing_version)
      RETURNING authority_version_id
    ), chosen_version AS (
      SELECT authority_version_id FROM existing_version
      UNION ALL
      SELECT authority_version_id FROM upsert_version
      LIMIT 1
    ), update_current AS (
      UPDATE paa.work_items wi
      SET status = 'accepted'::paa.work_item_status,
          authority_version_id = (SELECT authority_version_id FROM chosen_version),
          updated_at = now()
      FROM current_work_item cwi
      WHERE wi.work_item_id = cwi.work_item_id
      RETURNING wi.work_item_id
    ), update_next AS (
      UPDATE paa.work_items wi
      SET status = 'in_progress'::paa.work_item_status,
          authority_version_id = (SELECT authority_version_id FROM chosen_version),
          updated_at = now()
      FROM next_work_item nwi
      WHERE wi.work_item_id = nwi.work_item_id
      RETURNING wi.work_item_id
    )
    INSERT INTO paa.acceptance_events (
      project_id,
      work_item_id,
      accepted_by_agent_id,
      accepted_by_role_id,
      decision,
      notes,
      merge_commit_sha,
      metadata_json,
      created_at
    )
    SELECT
      project.project_id,
      current_work_item.work_item_id,
      architect_agent.agent_id,
      architect_role.role_id,
      'accepted'::paa.acceptance_decision,
      {sql_literal(notes)},
      {sql_literal(merge_commit_sha)},
      {sql_literal(metadata)}::jsonb,
      {sql_literal(published_at)}::timestamptz
    FROM project
    JOIN current_work_item ON TRUE
    JOIN architect_agent ON TRUE
    JOIN architect_role ON TRUE
    LEFT JOIN linked_handoff ON TRUE
    LEFT JOIN chosen_version ON TRUE
    LEFT JOIN update_current ON TRUE
    LEFT JOIN update_next ON TRUE
    WHERE NOT EXISTS (
      SELECT 1
      FROM paa.acceptance_events ae
      WHERE ae.work_item_id = current_work_item.work_item_id
        AND ae.decision = 'accepted'::paa.acceptance_decision
    );
    """
    run_psql(sql)


def persist_architect_decision(
    *,
    project_slug: str,
    issue_number: int,
    task_id: str,
    decision: str,
    notes: str,
    decided_at: str,
    pr_number: int | None = None,
    merge_commit_sha: str | None = None,
    comment_url: str | None = None,
    qa_packet_id: str | None = None,
) -> None:
    metadata = json.dumps({
        'source': 'project_authority.py',
        'task_id': task_id,
        'issue_number': issue_number,
        'pr_number': pr_number,
        'comment_url': comment_url,
        'qa_packet_id': qa_packet_id,
    })
    sql = f"""
    WITH project AS (
      SELECT project_id FROM paa.projects WHERE slug = {sql_literal(project_slug)}
    ), architect_role AS (
      SELECT role_id FROM paa.roles r JOIN project p ON p.project_id = r.project_id
      WHERE r.name = 'Architect'
      LIMIT 1
    ), architect_agent AS (
      SELECT agent_id FROM paa.agents a JOIN project p ON p.project_id = a.project_id
      WHERE a.name = 'Fractal Core Architect Automation'
      LIMIT 1
    ), current_work_item AS (
      SELECT wi.work_item_id
      FROM paa.work_items wi
      JOIN project p ON p.project_id = wi.project_id
      WHERE wi.issue_number = {sql_literal(issue_number)}
      LIMIT 1
    ), linked_handoff AS (
      SELECT qm.handoff_id
      FROM paa.queue_messages qm
      WHERE qm.message_id_external = {sql_literal(qa_packet_id)}
      LIMIT 1
    ), updated_work_item AS (
      UPDATE paa.work_items wi
      SET status = CASE
        WHEN {sql_literal(decision)} = 'accepted' THEN 'accepted'::paa.work_item_status
        WHEN {sql_literal(decision)} = 'rejected' THEN 'rejected'::paa.work_item_status
        WHEN {sql_literal(decision)} = 'blocked' THEN 'blocked'::paa.work_item_status
        ELSE wi.status
      END,
      updated_at = now()
      FROM current_work_item cwi
      WHERE wi.work_item_id = cwi.work_item_id
      RETURNING wi.work_item_id
    )
    INSERT INTO paa.acceptance_events (
      project_id,
      work_item_id,
      handoff_id,
      accepted_by_agent_id,
      accepted_by_role_id,
      decision,
      notes,
      merge_commit_sha,
      metadata_json,
      created_at
    )
    SELECT
      project.project_id,
      current_work_item.work_item_id,
      linked_handoff.handoff_id,
      architect_agent.agent_id,
      architect_role.role_id,
      {sql_literal(decision)}::paa.acceptance_decision,
      {sql_literal(notes)},
      {sql_literal(merge_commit_sha)},
      {sql_literal(metadata)}::jsonb,
      {sql_literal(decided_at)}::timestamptz
    FROM project, current_work_item, architect_agent, architect_role
    LEFT JOIN linked_handoff ON TRUE
    WHERE NOT EXISTS (
      SELECT 1 FROM paa.acceptance_events ae
      WHERE ae.work_item_id = current_work_item.work_item_id
        AND ae.decision = {sql_literal(decision)}::paa.acceptance_decision
        AND ae.notes = {sql_literal(notes)}
    );
    """
    run_psql(sql)


def cmd_advance_after_merge(args: Any) -> None:
    manifest, data = load_manifest(args.manifest)
    current = task_or_die(data, issue_number=args.issue_number, task_id=args.task_id)
    successors = [find_task(data, task_id=t) for t in current.get('allowed_successors', [])]
    successors = [t for t in successors if t]
    if len(successors) > 1:
        print(json.dumps({
            'ok': False,
            'error': 'expected at most one allowed successor to advance',
            'task_id': current['task_id'],
            'successor_count': len(successors),
        }, indent=2))
        sys.exit(1)
    nxt = successors[0] if successors else None

    if current.get('status') != 'complete':
        current['status'] = 'complete'
    if nxt:
        nxt['status'] = 'in_dev'

    accepted_history = data.setdefault('accepted_history', [])
    if not any(entry.get('task_id') == current['task_id'] for entry in accepted_history):
        accepted_history.append({
            'issue_number': current.get('issue_number'),
            'task_id': current['task_id'],
            'phase_id': current['phase_id'],
            'title': current['title'],
        })

    data['project']['authority_version'] = bump_authority_version(data['project']['authority_version'])
    data['project']['published_at'] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    write_manifest(manifest, data)

    result = {
        'ok': True,
        'manifest_path': str(manifest),
        'completed_task_id': current['task_id'],
        'completed_issue_number': current.get('issue_number'),
        'next_task_id': nxt['task_id'] if nxt else None,
        'next_issue_number': nxt.get('issue_number') if nxt else None,
        'terminal_completion': nxt is None,
        'authority_version': data['project']['authority_version'],
        'published_at': data['project']['published_at'],
    }
    if args.publish:
        publish_authority(manifest)
        result['published'] = True
    else:
        result['published'] = False
    if args.persist_db:
        persist_architect_acceptance(
            project_slug=args.project_slug,
            completed_issue_number=current.get('issue_number'),
            completed_task_id=current['task_id'],
            next_issue_number=nxt.get('issue_number') if nxt else None,
            next_task_id=nxt['task_id'] if nxt else None,
            authority_version=data['project']['authority_version'],
            published_at=data['project']['published_at'],
            merge_commit_sha=args.merge_commit_sha,
            pr_number=args.pr_number,
        )
        result['persisted_db'] = True
    else:
        result['persisted_db'] = False
    print(json.dumps(result, indent=2))


def cmd_record_acceptance(args: Any) -> None:
    persist_architect_acceptance(
        project_slug=args.project_slug,
        completed_issue_number=args.completed_issue_number,
        completed_task_id=args.completed_task_id,
        next_issue_number=args.next_issue_number,
        next_task_id=args.next_task_id,
        authority_version=args.authority_version,
        published_at=args.published_at,
        merge_commit_sha=args.merge_commit_sha,
        pr_number=args.pr_number,
    )
    print(json.dumps({
        'ok': True,
        'project_slug': args.project_slug,
        'completed_issue_number': args.completed_issue_number,
        'completed_task_id': args.completed_task_id,
        'next_issue_number': args.next_issue_number,
        'next_task_id': args.next_task_id,
        'authority_version': args.authority_version,
        'published_at': args.published_at,
        'merge_commit_sha': args.merge_commit_sha,
        'pr_number': args.pr_number,
    }, indent=2))


def cmd_record_decision(args: Any) -> None:
    persist_architect_decision(
        project_slug=args.project_slug,
        issue_number=args.issue_number,
        task_id=args.task_id,
        decision=args.decision,
        notes=args.notes,
        decided_at=args.decided_at,
        pr_number=args.pr_number,
        merge_commit_sha=args.merge_commit_sha,
        comment_url=args.comment_url,
        qa_packet_id=args.qa_packet_id,
    )
    print(json.dumps({
        'ok': True,
        'project_slug': args.project_slug,
        'issue_number': args.issue_number,
        'task_id': args.task_id,
        'decision': args.decision,
        'notes': args.notes,
        'decided_at': args.decided_at,
        'pr_number': args.pr_number,
        'merge_commit_sha': args.merge_commit_sha,
        'comment_url': args.comment_url,
        'qa_packet_id': args.qa_packet_id,
    }, indent=2))

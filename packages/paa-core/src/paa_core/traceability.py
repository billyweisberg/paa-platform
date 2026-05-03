"""Traceability helpers backed by live PAA reporting views."""

from __future__ import annotations

from paa_core.db import query_rows, settings_from_profile, sql_literal


def full_chain_rows(project_slug: str, issue_number: int | None = None, *, db_profile: str | None = None) -> list[dict[str, str]]:
    where = f"WHERE project_slug = {sql_literal(project_slug)}"
    if issue_number is not None:
        where += f" AND issue_number = {sql_literal(issue_number)}"
    sql = f"SELECT project_slug, issue_number::text, work_item_status, package_id_external, brief_id_external, full_chain_state, coalesce(acceptance_decision,''), coalesce(dev_queue_status,''), coalesce(qa_queue_status,'') FROM paa.v_work_item_full_chain_traceability {where} ORDER BY issue_number;"
    rows = []
    for cols in query_rows(sql, settings=settings_from_profile(db_profile)):
        rows.append({
            'project_slug': cols[0],
            'issue_number': cols[1],
            'work_item_status': cols[2],
            'package_id_external': cols[3],
            'brief_id_external': cols[4],
            'full_chain_state': cols[5],
            'acceptance_decision': cols[6],
            'dev_queue_status': cols[7],
            'qa_queue_status': cols[8],
        })
    return rows

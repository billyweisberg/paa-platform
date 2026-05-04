#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path
import subprocess
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

STATUS_ORDER = {
    'undefined': 0,
    'defined': 1,
    'contract_ready': 2,
    'implementation_ready': 3,
    'verified': 4,
}

READINESS_CLASSES = {
    'not_derivation_ready',
    'derivation_ready',
    'blocked_on_dependency',
    'blocked_on_contract',
    'execution_ready',
    'parallel_ready',
    'active',
    'completed',
}

PAA_DB_CONTAINER = os.environ.get('PAA_DB_CONTAINER', 'agenthub-mm-db')
PAA_DB_NAME = os.environ.get('PAA_DB_NAME', 'paa_dev')
PAA_DB_USER = os.environ.get('PAA_DB_USER', 'mmuser')
DEFAULT_PROJECT_SLUG = os.environ.get('PAA_PROJECT_SLUG', 'fractal-core-python')


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + '\n')


def sql_literal(value: Optional[str]) -> str:
    if value is None:
        return 'NULL'
    return "'" + str(value).replace("'", "''") + "'"


def run_psql(sql: str, *, db_container: str, db_name: str, db_user: str) -> str:
    result = subprocess.run(
        ['docker', 'exec', '-i', db_container, 'psql', '-U', db_user, '-d', db_name, '-At', '-F', '\t'],
        input=sql,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or 'psql command failed')
    return result.stdout


def parse_override(values: Iterable[str], expected: Optional[Iterable[str]] = None) -> Dict[str, str]:
    overrides: Dict[str, str] = {}
    expected_set = set(expected or [])
    for value in values:
        if '=' not in value:
            raise SystemExit(f'Invalid override {value!r}. Expected key=value.')
        key, status = value.split('=', 1)
        key = key.strip()
        status = status.strip()
        if expected_set and status not in expected_set:
            allowed = ', '.join(sorted(expected_set))
            raise SystemExit(f'Invalid status {status!r} for {key!r}. Allowed: {allowed}')
        overrides[key] = status
    return overrides


def sufficiency_required(sequencing_requirement: str) -> str:
    if sequencing_requirement == 'must_follow_contract_only':
        return 'contract_ready'
    if sequencing_requirement == 'must_precede':
        return 'implementation_ready'
    return 'defined'


def status_meets(current: str, required: str) -> bool:
    return STATUS_ORDER.get(current, -1) >= STATUS_ORDER.get(required, -1)


def infer_component_id(brief: dict, graph: dict) -> str:
    target_name = brief['component_assignment']['component_name']
    for node in graph['nodes']:
        if node['component_name'] == target_name:
            return node['component_id']
    raise KeyError(f'No graph node matches brief component name {target_name!r}')


def collect_incoming_edges(component_id: str, graph: dict) -> List[dict]:
    return [edge for edge in graph['edges'] if edge['from_component_id'] == component_id]


def collect_parallel_safe_briefs(component_id: str, graph: dict, component_to_brief: Dict[str, str]) -> List[str]:
    peers: List[str] = []
    for edge in graph['edges']:
        if edge['sequencing_requirement'] != 'may_parallelize':
            continue
        if edge['from_component_id'] == component_id and edge['to_component_id'] in component_to_brief:
            peers.append(component_to_brief[edge['to_component_id']])
        elif edge['to_component_id'] == component_id and edge['from_component_id'] in component_to_brief:
            peers.append(component_to_brief[edge['from_component_id']])
    return sorted(set(peers))


def incoming_conflicts(component_id: str, graph: dict) -> List[str]:
    conflicts: List[str] = []
    for edge in collect_incoming_edges(component_id, graph):
        if edge.get('shared_surface_conflict'):
            conflicts.append(
                f"{edge['edge_id']} via shared edits in {', '.join(graph_surface_hints(edge, graph))}"
            )
    return conflicts


def graph_surface_hints(edge: dict, graph: dict) -> List[str]:
    from_node = next(node for node in graph['nodes'] if node['component_id'] == edge['from_component_id'])
    to_node = next(node for node in graph['nodes'] if node['component_id'] == edge['to_component_id'])
    return sorted(set(from_node.get('surface_set', [])) & set(to_node.get('surface_set', []))) or ['shared surface']


def dependency_readiness_rows(edges: List[dict]) -> List[dict]:
    rows = []
    for edge in edges:
        rows.append({
            'dependency_edge_id': edge['edge_id'],
            'status': edge['dependency_status'],
            'notes': edge.get('notes'),
        })
    return rows


def determine_readiness(package: dict, component_id: str, graph: dict, component_to_brief: Dict[str, str]) -> Tuple[dict, dict]:
    if package.get('status') != 'approved_for_derivation':
        return (
            {
                'prerequisite_briefs': [],
                'blocking_dependency_edges': [],
                'parallel_safe_with': [],
                'shared_surface_conflicts': [],
                'sequencing_notes': ['Stage 1 package is not approved_for_derivation.'],
            },
            {
                'readiness_class': 'not_derivation_ready',
                'dependency_readiness': [],
                'blocking_causes': ['Stage 1 design package is not approved_for_derivation.'],
                'parallel_group_id': None,
                'recommended_next_owner': 'Architect',
                'readiness_snapshot_source': f"{package.get('package_id', 'stage1_design_package')}#status",
            },
        )

    incoming = collect_incoming_edges(component_id, graph)
    prereq_briefs = [
        component_to_brief[edge['to_component_id']]
        for edge in incoming
        if edge['to_component_id'] in component_to_brief and edge['dependency_strength'] == 'hard'
    ]
    blocking_edges: List[str] = []
    blocking_causes: List[str] = []
    blocked_on_contract = False

    for edge in incoming:
        required = sufficiency_required(edge['sequencing_requirement'])
        if edge['dependency_strength'] == 'hard' and not status_meets(edge['dependency_status'], required):
            blocking_edges.append(edge['edge_id'])
            cause = edge.get('notes') or f"{edge['edge_id']} requires {required}."
            blocking_causes.append(cause)
            if edge['sequencing_requirement'] == 'must_follow_contract_only':
                blocked_on_contract = True

    shared_conflicts = incoming_conflicts(component_id, graph)
    parallel_safe_with = collect_parallel_safe_briefs(component_id, graph, component_to_brief)

    sequencing_notes = []
    for constraint in graph.get('sequencing_constraints', []):
        if constraint.get('from_component_id') == component_id or constraint.get('to_component_id') == component_id:
            sequencing_notes.append(constraint['rule'])

    if component_id == graph.get('primary_component_id') and not prereq_briefs:
        readiness_class = 'execution_ready'
        next_owner = 'Python Dev'
    elif blocking_edges:
        readiness_class = 'blocked_on_contract' if blocked_on_contract else 'blocked_on_dependency'
        next_owner = 'Python Dev'
    elif parallel_safe_with and not shared_conflicts:
        readiness_class = 'parallel_ready'
        next_owner = 'TechLead'
    else:
        readiness_class = 'execution_ready'
        next_owner = 'Python Dev'

    prerequisite_section = {
        'prerequisite_briefs': sorted(set(prereq_briefs)),
        'blocking_dependency_edges': blocking_edges,
        'parallel_safe_with': parallel_safe_with,
        'shared_surface_conflicts': shared_conflicts,
        'sequencing_notes': sequencing_notes,
    }
    readiness_section = {
        'readiness_class': readiness_class,
        'dependency_readiness': dependency_readiness_rows(incoming),
        'blocking_causes': blocking_causes,
        'parallel_group_id': f"parallel-{component_id}" if readiness_class == 'parallel_ready' else None,
        'recommended_next_owner': next_owner,
        'readiness_snapshot_source': f"{package.get('package_id', 'stage1_design_package')}#dependency_graph_slice",
    }
    return prerequisite_section, readiness_section


def discover_briefs(brief_dir: Path) -> List[Path]:
    return sorted(p for p in brief_dir.glob('coder_run_brief*.json') if p.is_file())


def load_from_db(*, package_id_external: str, project_slug: str, db_container: str, db_name: str, db_user: str) -> Tuple[dict, List[Tuple[str, dict]], dict]:
    pkg_sql = f"""
    SELECT dp.package_json::text
    FROM paa.design_packages dp
    JOIN paa.projects p ON p.project_id = dp.project_id
    WHERE p.slug = {sql_literal(project_slug)}
      AND dp.package_id_external = {sql_literal(package_id_external)}
    LIMIT 1;
    """
    pkg_out = run_psql(pkg_sql, db_container=db_container, db_name=db_name, db_user=db_user).strip()
    if not pkg_out:
        raise RuntimeError(f'No design package found for {project_slug}:{package_id_external}')
    package = json.loads(pkg_out)

    brief_sql = f"""
    SELECT cb.brief_id_external, cb.brief_json::text
    FROM paa.coder_run_briefs cb
    JOIN paa.projects p ON p.project_id = cb.project_id
    WHERE p.slug = {sql_literal(project_slug)}
      AND cb.generated_from_json->>'design_package_id_external' = {sql_literal(package_id_external)}
    ORDER BY cb.brief_id_external;
    """
    brief_rows = []
    for line in run_psql(brief_sql, db_container=db_container, db_name=db_name, db_user=db_user).splitlines():
        if not line.strip():
            continue
        brief_id, brief_json = line.split('\t', 1)
        brief_rows.append((brief_id, json.loads(brief_json)))
    if not brief_rows:
        raise RuntimeError(f'No coder briefs found for design package {package_id_external}')

    edge_sql = f"""
    SELECT e.metadata_json->>'edge_id', e.dependency_status::text, coalesce(e.notes, ''), e.shared_surface_conflict
    FROM paa.component_dependency_edges e
    JOIN paa.design_packages dp ON dp.design_package_id = e.design_package_id
    JOIN paa.projects p ON p.project_id = e.project_id
    WHERE p.slug = {sql_literal(project_slug)}
      AND dp.package_id_external = {sql_literal(package_id_external)};
    """
    edge_status_map: Dict[str, dict] = {}
    for line in run_psql(edge_sql, db_container=db_container, db_name=db_name, db_user=db_user).splitlines():
        if not line.strip():
            continue
        edge_id, status, notes, shared_surface_conflict = line.split('\t')
        edge_status_map[edge_id] = {
            'dependency_status': status,
            'notes': notes or None,
            'shared_surface_conflict': shared_surface_conflict == 't',
        }
    return package, brief_rows, edge_status_map


def persist_to_db(
    *,
    project_slug: str,
    package_id_external: str,
    updated_briefs: List[dict],
    db_container: str,
    db_name: str,
    db_user: str,
) -> None:
    statements = []
    for brief in updated_briefs:
        brief_json = json.dumps(brief, separators=(',', ':'))
        prereq_json = json.dumps(brief['execution_prerequisites'], separators=(',', ':'))
        readiness_json = json.dumps(brief['execution_readiness'], separators=(',', ':'))
        blocking_cause = '; '.join(brief['execution_readiness'].get('blocking_causes', [])) or None
        parallel_group_id = brief['execution_readiness'].get('parallel_group_id')
        statements.append(f"""
        UPDATE paa.coder_run_briefs cb
        SET brief_json = {sql_literal(brief_json)}::jsonb,
            metadata_json = coalesce(cb.metadata_json, '{{}}'::jsonb) || jsonb_build_object(
              'execution_prerequisites', {sql_literal(prereq_json)}::jsonb,
              'execution_readiness', {sql_literal(readiness_json)}::jsonb
            ),
            updated_at = now()
        FROM paa.projects p
        WHERE p.project_id = cb.project_id
          AND p.slug = {sql_literal(project_slug)}
          AND cb.brief_id_external = {sql_literal(brief['brief_id'])};

        INSERT INTO paa.coder_brief_sequence_states (
          project_id,
          design_package_id,
          coder_run_brief_id,
          primary_component_id,
          readiness_state,
          blocking_cause,
          parallel_group_id,
          metadata_json
        )
        SELECT
          p.project_id,
          dp.design_package_id,
          cb.coder_run_brief_id,
          cb.primary_component_id,
          {sql_literal(brief['execution_readiness']['readiness_class'])}::paa.readiness_state,
          {sql_literal(blocking_cause)},
          {sql_literal(parallel_group_id)},
          jsonb_build_object(
            'source', 'materialize_coder_brief_readiness.py',
            'design_package_id_external', {sql_literal(package_id_external)},
            'brief_id_external', {sql_literal(brief['brief_id'])},
            'dependency_readiness', {sql_literal(readiness_json)}::jsonb
          )
        FROM paa.projects p
        JOIN paa.design_packages dp ON dp.project_id = p.project_id
        JOIN paa.coder_run_briefs cb ON cb.project_id = p.project_id
        WHERE p.slug = {sql_literal(project_slug)}
          AND dp.package_id_external = {sql_literal(package_id_external)}
          AND cb.brief_id_external = {sql_literal(brief['brief_id'])};
        """)
    sql = 'BEGIN;\n' + '\n'.join(statements) + '\nCOMMIT;\n'
    run_psql(sql, db_container=db_container, db_name=db_name, db_user=db_user)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description='Materialize execution prerequisites and readiness into coder_run_brief artifacts.')
    parser.add_argument('--design-package', help='Path to the Stage 1 design package JSON artifact.')
    parser.add_argument('--dependency-graph', help='Optional path to dependency_graph_slice JSON. Defaults to embedded package graph.')
    parser.add_argument('--brief-dir', help='Directory containing coder_run_brief*.json artifacts to update.')
    parser.add_argument('--db-package-id-external', help='Load the design package and coder briefs from PAA by external package id.')
    parser.add_argument('--db-project-slug', default=DEFAULT_PROJECT_SLUG, help='Project slug for PAA-backed mode.')
    parser.add_argument('--db-container', default=PAA_DB_CONTAINER, help='Docker container name for PAA Postgres.')
    parser.add_argument('--db-name', default=PAA_DB_NAME, help='Database name for PAA Postgres.')
    parser.add_argument('--db-user', default=PAA_DB_USER, help='Database user for PAA Postgres.')
    parser.add_argument('--set-edge-status', action='append', default=[], help='Override dependency edge status as edge_id=status.')
    parser.add_argument('--set-brief-readiness', action='append', default=[], help='Force a brief readiness class as brief_id=readiness_class.')
    parser.add_argument('--write', action='store_true', help='Persist updated briefs back to disk.')
    parser.add_argument('--db-write', action='store_true', help='Persist updated coder brief JSON and sequence state into PAA.')
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not args.design_package and not args.db_package_id_external:
        raise SystemExit('Pass either --design-package or --db-package-id-external.')
    if not args.brief_dir and not args.db_package_id_external:
        raise SystemExit('Pass either --brief-dir or --db-package-id-external.')

    updated_briefs: List[dict] = []

    if args.db_package_id_external:
        package, brief_rows, edge_status_map = load_from_db(
            package_id_external=args.db_package_id_external,
            project_slug=args.db_project_slug,
            db_container=args.db_container,
            db_name=args.db_name,
            db_user=args.db_user,
        )
        graph = load_json(Path(args.dependency_graph).resolve()) if args.dependency_graph else package['dependency_graph_slice']
        for edge in graph['edges']:
            db_edge = edge_status_map.get(edge['edge_id'])
            if db_edge:
                edge['dependency_status'] = db_edge['dependency_status']
                edge['notes'] = db_edge['notes'] or edge.get('notes')
                edge['shared_surface_conflict'] = db_edge['shared_surface_conflict']
        briefs = [(Path(f"{brief_id}.json"), brief) for brief_id, brief in brief_rows]
    else:
        package_path = Path(args.design_package).resolve()
        brief_dir = Path(args.brief_dir).resolve()
        package = load_json(package_path)
        graph = load_json(Path(args.dependency_graph).resolve()) if args.dependency_graph else package['dependency_graph_slice']
        brief_paths = discover_briefs(brief_dir)
        briefs = [(path, load_json(path)) for path in brief_paths]

    edge_overrides = parse_override(args.set_edge_status, STATUS_ORDER.keys())
    brief_readiness_overrides = parse_override(args.set_brief_readiness, READINESS_CLASSES)

    for edge in graph['edges']:
        if edge['edge_id'] in edge_overrides:
            edge['dependency_status'] = edge_overrides[edge['edge_id']]

    component_to_brief: Dict[str, str] = {}
    path_to_component: Dict[Path, str] = {}
    for path, brief in briefs:
        component_id = infer_component_id(brief, graph)
        path_to_component[path] = component_id
        component_to_brief[component_id] = brief['brief_id']

    summary = []
    for path, brief in briefs:
        component_id = path_to_component[path]
        prereq, readiness = determine_readiness(package, component_id, graph, component_to_brief)
        if brief['brief_id'] in brief_readiness_overrides:
            readiness['readiness_class'] = brief_readiness_overrides[brief['brief_id']]
        brief['execution_prerequisites'] = prereq
        brief['execution_readiness'] = readiness
        if args.write and args.brief_dir:
            save_json(path, brief)
        updated_briefs.append(brief)
        summary.append({
            'brief_id': brief['brief_id'],
            'component_name': brief['component_assignment']['component_name'],
            'readiness_class': readiness['readiness_class'],
            'blocking_dependency_edges': prereq['blocking_dependency_edges'],
            'parallel_safe_with': prereq['parallel_safe_with'],
        })

    if args.db_write and args.db_package_id_external:
        persist_to_db(
            project_slug=args.db_project_slug,
            package_id_external=args.db_package_id_external,
            updated_briefs=updated_briefs,
            db_container=args.db_container,
            db_name=args.db_name,
            db_user=args.db_user,
        )

    print(json.dumps({'updated_briefs': summary}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

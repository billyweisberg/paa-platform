from __future__ import annotations

import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.repositories.source_authority import (
    AuthorityVersionUpsertSpec,
    ImplementationTargetUpsertSpec,
    PostgresSourceAuthorityRepository,
    ProjectUpsertSpec,
    SpecFragmentUpsertSpec,
    WorkItemUpsertSpec,
)


class SourceAuthorityRepositoryTests(unittest.TestCase):
    def test_get_project_by_slug_parses_row(self) -> None:
        repo = PostgresSourceAuthorityRepository()
        output = [{'project_id': 'proj-1', 'slug': 'paa-platform', 'name': 'PAA Platform', 'repo_url': 'https://example.test/repo', 'execution_surface': 'github', 'status': 'active', 'created_at': '2026-06-04T12:00:00+00:00', 'updated_at': '2026-06-04T12:05:00+00:00'}]
        with patch('paa_core.repositories.source_authority.postgres.query_json_rows', return_value=output):
            row = repo.get_project_by_slug('paa-platform')

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.slug, 'paa-platform')
        self.assertEqual(row.repo_url, 'https://example.test/repo')

    def test_upsert_project_is_idempotent_by_slug(self) -> None:
        repo = PostgresSourceAuthorityRepository()
        spec = ProjectUpsertSpec(
            slug='paa-platform',
            name='PAA Platform',
            repo_url='https://example.test/repo',
        )
        output = [{'project_id': 'proj-1', 'slug': 'paa-platform', 'name': 'PAA Platform', 'repo_url': 'https://example.test/repo', 'execution_surface': 'github', 'status': 'active', 'created_at': '2026-06-04T12:00:00+00:00', 'updated_at': '2026-06-04T12:05:00+00:00'}]
        with patch('paa_core.repositories.source_authority.postgres.execute_sql') as mock_exec, patch(
            'paa_core.repositories.source_authority.postgres.query_json_rows',
            return_value=output,
        ):
            row = repo.upsert_project(spec)

        self.assertEqual(row.project_id, 'proj-1')
        self.assertEqual(mock_exec.call_count, 1)

    def test_upsert_authority_version_is_idempotent_by_project_and_label(self) -> None:
        repo = PostgresSourceAuthorityRepository()
        spec = AuthorityVersionUpsertSpec(
            project_slug='paa-platform',
            version_label='2026.06.04',
            manifest_path='/tmp/manifest.json',
        )
        with patch.object(
            repo,
            'get_project_by_slug',
            return_value=type('Project', (), {'project_id': 'proj-1'})(),
        ), patch('paa_core.repositories.source_authority.postgres.execute_sql') as mock_exec, patch(
            'paa_core.repositories.source_authority.postgres.query_json_rows',
            return_value=[
                {
                    'authority_version_id': 'auth-1',
                    'project_id': 'proj-1',
                    'version_label': '2026.06.04',
                    'source_commit': None,
                    'published_from_ref': None,
                    'manifest_path': '/tmp/manifest.json',
                    'published_at': None,
                    'status': 'published',
                    'notes': None,
                    'created_at': '2026-06-04T12:00:00+00:00',
                    'updated_at': '2026-06-04T12:05:00+00:00',
                }
            ],
        ):
            row = repo.upsert_authority_version(spec)

        self.assertEqual(row.authority_version_id, 'auth-1')
        self.assertEqual(mock_exec.call_count, 1)

    def test_upsert_spec_fragment_resolves_by_stable_identity(self) -> None:
        repo = PostgresSourceAuthorityRepository()
        spec = SpecFragmentUpsertSpec(
            project_slug='paa-platform',
            title='Design package derivation',
            canonical_statement='Derive a package from source authority.',
            fragment_kind='artifact_contract',
            delta_family='producer_design_package',
            external_fragment_id='frag-ext-1',
            out_of_scope_delta_families=('ui',),
            expected_touch_surfaces=('producer/design_package_deriver.py',),
        )
        with patch.object(
            repo,
            'get_project_by_slug',
            return_value=type('Project', (), {'project_id': 'proj-1'})(),
        ), patch('paa_core.repositories.source_authority.postgres.execute_sql'), patch(
            'paa_core.repositories.source_authority.postgres.query_json_rows',
            return_value=[
                {
                    'spec_fragment_id': 'frag-1',
                    'project_id': 'proj-1',
                    'title': 'Design package derivation',
                    'canonical_statement': 'Derive a package from source authority.',
                    'fragment_kind': 'artifact_contract',
                    'delta_family': 'producer_design_package',
                    'authorized_delta_family': None,
                    'out_of_scope_delta_families': ['ui'],
                    'expected_touch_surfaces': ['producer/design_package_deriver.py'],
                    'status': 'approved',
                    'metadata': {'spec_fragment_id_external': 'frag-ext-1'},
                    'created_at': '2026-06-04T12:00:00+00:00',
                    'updated_at': '2026-06-04T12:05:00+00:00',
                }
            ],
        ):
            row = repo.upsert_spec_fragment(spec)

        self.assertEqual(row.spec_fragment_id, 'frag-1')
        self.assertEqual(row.out_of_scope_delta_families, ('ui',))

    def test_upsert_implementation_target_resolves_by_target_identity_within_fragment(self) -> None:
        repo = PostgresSourceAuthorityRepository()
        spec = ImplementationTargetUpsertSpec(
            spec_fragment_id='frag-1',
            title='Design package derivation target',
            external_target_id='target-ext-1',
            current_gap=('raw sql in producer',),
            desired_state=('repo-owned persistence',),
            protected_baseline=('s03 methodology path',),
            pre_handoff_scope_checks=('authoring-check',),
        )
        with patch.object(repo, '_require_spec_fragment'), patch(
            'paa_core.repositories.source_authority.postgres.execute_sql'
        ), patch(
            'paa_core.repositories.source_authority.postgres.query_json_rows',
            return_value=[
                {
                    'implementation_target_id': 'target-1',
                    'spec_fragment_id': 'frag-1',
                    'title': 'Design package derivation target',
                    'current_gap': ['raw sql in producer'],
                    'desired_state': ['repo-owned persistence'],
                    'protected_baseline': ['s03 methodology path'],
                    'out_of_scope': [],
                    'pre_handoff_scope_checks': ['authoring-check'],
                    'risk_level': 'medium',
                    'status': 'approved',
                    'metadata': {'implementation_target_id_external': 'target-ext-1'},
                    'created_at': '2026-06-04T12:00:00+00:00',
                    'updated_at': '2026-06-04T12:05:00+00:00',
                }
            ],
        ):
            row = repo.upsert_implementation_target(spec)

        self.assertEqual(row.implementation_target_id, 'target-1')
        self.assertEqual(row.current_gap, ('raw sql in producer',))

    def test_upsert_work_item_resolves_by_issue_or_fragment_anchor(self) -> None:
        repo = PostgresSourceAuthorityRepository()
        spec = WorkItemUpsertSpec(
            project_slug='paa-platform',
            authority_version_id='auth-1',
            title='Implement S04 data layer',
            issue_number=204,
            spec_fragment_ref='frag-ext-1',
            implementation_target_ref='target-ext-1',
            domain_ref={'task_id': 'S04'},
            spec_fragment_id='frag-1',
            implementation_target_id='target-1',
        )
        with patch.object(
            repo,
            'get_project_by_slug',
            return_value=type('Project', (), {'project_id': 'proj-1'})(),
        ), patch.object(repo, '_require_authority_version'), patch.object(
            repo, '_require_spec_fragment'
        ), patch.object(repo, '_require_implementation_target'), patch(
            'paa_core.repositories.source_authority.postgres.execute_sql'
        ), patch(
            'paa_core.repositories.source_authority.postgres.query_json_rows',
            return_value=[
                {
                    'work_item_id': 'work-1',
                    'project_id': 'proj-1',
                    'authority_version_id': 'auth-1',
                    'title': 'Implement S04 data layer',
                    'status': 'authorized',
                    'merge_policy': 'architect_review_required',
                    'requires_qa': False,
                    'issue_number': 204,
                    'implementation_target_ref': 'target-ext-1',
                    'spec_fragment_ref': 'frag-ext-1',
                    'domain_ref': {'task_id': 'S04'},
                    'spec_fragment_id': 'frag-1',
                    'implementation_target_id': 'target-1',
                    'created_at': '2026-06-04T12:00:00+00:00',
                    'updated_at': '2026-06-04T12:05:00+00:00',
                }
            ],
        ):
            row = repo.upsert_work_item(spec)

        self.assertEqual(row.work_item_id, 'work-1')
        self.assertEqual(row.issue_number, 204)
        self.assertEqual(row.domain_ref, {'task_id': 'S04'})

    def test_find_work_item_by_project_and_authority_anchor_returns_none_when_missing(self) -> None:
        repo = PostgresSourceAuthorityRepository()
        with patch('paa_core.repositories.source_authority.postgres.query_json_rows', return_value=[]):
            row = repo.find_work_item_by_project_and_authority_anchor(
                'paa-platform',
                issue_number=204,
            )

        self.assertIsNone(row)

    def test_find_work_item_requires_issue_or_fragment_anchor(self) -> None:
        repo = PostgresSourceAuthorityRepository()
        with self.assertRaises(ValueError):
            repo.find_work_item_by_project_and_authority_anchor('paa-platform')

    def test_dependent_upserts_fail_closed_for_missing_upstream_anchors(self) -> None:
        repo = PostgresSourceAuthorityRepository()
        with patch('paa_core.repositories.source_authority.postgres.query_scalar', return_value=None):
            with self.assertRaises(LookupError):
                repo._require_authority_version('missing-auth')
            with self.assertRaises(LookupError):
                repo._require_spec_fragment('missing-frag')
            with self.assertRaises(LookupError):
                repo._require_implementation_target('missing-target')


if __name__ == '__main__':
    unittest.main()

from __future__ import annotations

import os
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.db import DBSettings, run_psql, settings_from_profile


class DBSettingsTests(unittest.TestCase):
    def test_default_profile_targets_paa_local_db(self) -> None:
        settings = settings_from_profile('paa_dev')
        self.assertEqual(settings.mode, 'docker_exec')
        self.assertEqual(settings.container, 'paa-postgres-db')
        self.assertEqual(settings.port, 55433)
        self.assertEqual(settings.user, 'paa')

    def test_host_profile_uses_tcp(self) -> None:
        settings = settings_from_profile('paa_dev_host')
        self.assertEqual(settings.mode, 'tcp')
        self.assertEqual(settings.host, '127.0.0.1')
        self.assertEqual(settings.port, 55433)

    def test_env_overrides_profile_settings(self) -> None:
        with patch.dict(
            os.environ,
            {
                'PAA_DB_PROFILE': 'agenthub_paa_dev_legacy',
                'PAA_DB_MODE': 'tcp',
                'PAA_DB_HOST': 'db.local',
                'PAA_DB_PORT': '6000',
                'PAA_DB_NAME': 'custom_db',
                'PAA_DB_USER': 'custom_user',
                'PAA_DB_PASSWORD': 'secret',
            },
            clear=False,
        ):
            settings = settings_from_profile(None)
        self.assertEqual(
            settings,
            DBSettings(
                mode='tcp',
                container='agenthub-mm-db',
                host='db.local',
                port=6000,
                name='custom_db',
                user='custom_user',
                password='secret',
            ),
        )


class RunPsqlTests(unittest.TestCase):
    def test_run_psql_uses_docker_exec_for_container_mode(self) -> None:
        settings = DBSettings(
            mode='docker_exec',
            container='paa-postgres-db',
            host='127.0.0.1',
            port=55433,
            name='paa_dev',
            user='paa',
        )
        with patch('paa_core.db.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = 'ok\n'
            out = run_psql('select 1;', settings=settings)
        self.assertEqual(out, 'ok\n')
        cmd = mock_run.call_args.kwargs['args'] if 'args' in mock_run.call_args.kwargs else mock_run.call_args.args[0]
        self.assertEqual(cmd[:4], ['docker', 'exec', '-i', 'paa-postgres-db'])

    def test_run_psql_uses_host_psql_for_tcp_mode(self) -> None:
        settings = DBSettings(
            mode='tcp',
            container='paa-postgres-db',
            host='127.0.0.1',
            port=55433,
            name='paa_dev',
            user='paa',
            password='secret',
        )
        with patch('paa_core.db.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = 'ok\n'
            out = run_psql('select 1;', settings=settings)
        self.assertEqual(out, 'ok\n')
        cmd = mock_run.call_args.kwargs['args'] if 'args' in mock_run.call_args.kwargs else mock_run.call_args.args[0]
        env = mock_run.call_args.kwargs['env']
        self.assertEqual(cmd[:2], ['psql', '-h'])
        self.assertEqual(cmd[2], '127.0.0.1')
        self.assertEqual(cmd[4], '55433')
        self.assertEqual(env['PGPASSWORD'], 'secret')


if __name__ == '__main__':
    unittest.main()

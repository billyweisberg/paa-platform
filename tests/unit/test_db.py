from __future__ import annotations

import os
import sys
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

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
    def test_run_psql_uses_psycopg_connection_for_container_mode(self) -> None:
        settings = DBSettings(
            mode='docker_exec',
            container='paa-postgres-db',
            host='127.0.0.1',
            port=55433,
            name='paa_dev',
            user='paa',
        )
        fake_cursor = MagicMock()
        fake_cursor.description = (object(),)
        fake_cursor.fetchall.return_value = [('ok',)]
        fake_conn = MagicMock()
        fake_conn.__enter__.return_value = fake_conn
        fake_conn.cursor.return_value.__enter__.return_value = fake_cursor
        with patch('paa_core.db.psycopg.connect', return_value=fake_conn) as mock_connect:
            out = run_psql('select 1;', settings=settings)
        self.assertEqual(out, 'ok')
        mock_connect.assert_called_once_with(
            host='127.0.0.1',
            port=55433,
            dbname='paa_dev',
            user='paa',
            password=None,
            autocommit=True,
        )
        fake_cursor.execute.assert_called_once_with('select 1;')

    def test_run_psql_uses_psycopg_connection_for_tcp_mode(self) -> None:
        settings = DBSettings(
            mode='tcp',
            container='paa-postgres-db',
            host='127.0.0.1',
            port=55433,
            name='paa_dev',
            user='paa',
            password='secret',
        )
        fake_cursor = MagicMock()
        fake_cursor.description = (object(),)
        fake_cursor.fetchall.return_value = [('ok',)]
        fake_conn = MagicMock()
        fake_conn.__enter__.return_value = fake_conn
        fake_conn.cursor.return_value.__enter__.return_value = fake_cursor
        with patch('paa_core.db.psycopg.connect', return_value=fake_conn) as mock_connect:
            out = run_psql('select 1;', settings=settings)
        self.assertEqual(out, 'ok')
        mock_connect.assert_called_once_with(
            host='127.0.0.1',
            port=55433,
            dbname='paa_dev',
            user='paa',
            password='secret',
            autocommit=True,
        )
        fake_cursor.execute.assert_called_once_with('select 1;')


if __name__ == '__main__':
    unittest.main()

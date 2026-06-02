"""Deprecated consumer CLI entrypoint."""

from __future__ import annotations

import json


def main() -> int:
    print(json.dumps(
        {
            'ok': False,
            'reason': 'paa_consumer_cli_removed',
            'details': 'Use the unified `paa` CLI instead of `paa_consumer`.',
            'suggested_commands': [
                'paa runtime start',
                'paa runtime status',
                'paa runtime stop',
                'paa queue ensure-topology',
                'paa queue check',
                'paa queue purge',
                'paa queue send-packet',
            ],
        },
        indent=2,
    ))
    return 2


if __name__ == '__main__':
    raise SystemExit(main())

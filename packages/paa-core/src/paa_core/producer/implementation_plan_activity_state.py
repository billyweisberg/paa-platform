"""Producer-side entrypoint for implementation-plan activity state mutation."""

from __future__ import annotations

import json

from paa_core.repositories.implementation_plan import (
    ImplementationPlanActivityStateUpdateSpec,
    PostgresImplementationPlanRepository,
)


def set_implementation_plan_activity_state(
    *,
    plan_id: str,
    activity_key: str,
    activity_state: str,
    blocking_reason: str | None = None,
    started_at: str | None = None,
    completed_at: str | None = None,
    metadata_json: str | None = None,
) -> dict[str, object]:
    metadata = _parse_metadata_json(metadata_json)
    repository = PostgresImplementationPlanRepository()
    repository.set_implementation_plan_activity_state(
        ImplementationPlanActivityStateUpdateSpec(
            implementation_plan_id=plan_id,
            activity_key=activity_key,
            activity_state=activity_state,
            blocking_reason=blocking_reason,
            started_at=started_at,
            completed_at=completed_at,
            metadata=metadata,
        )
    )
    return {
        'ok': True,
        'implementation_plan_id': plan_id,
        'activity_key': activity_key,
        'requested_state': activity_state,
        'blocking_reason': blocking_reason,
        'started_at': started_at,
        'completed_at': completed_at,
        'metadata': metadata,
    }


def _parse_metadata_json(metadata_json: str | None) -> dict[str, object] | None:
    if metadata_json is None:
        return None
    payload = json.loads(metadata_json)
    if not isinstance(payload, dict):
        raise ValueError('metadata_json must decode to a JSON object')
    return payload


__all__ = ['set_implementation_plan_activity_state']

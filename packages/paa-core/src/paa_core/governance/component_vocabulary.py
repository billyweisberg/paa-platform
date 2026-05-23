"""Canonical governed component vocabulary and validation."""

from __future__ import annotations

from dataclasses import dataclass

_CANONICAL_SYSTEM_LAYERS = frozenset(
    {
        'domain-core',
        'domain-services',
        'application-services',
        'infrastructure-ports',
        'infrastructure-adapters',
        'host-surfaces',
    }
)

_CANONICAL_TIERS = frozenset({'runtime', 'integration', 'test', 'docs'})

_CANONICAL_STATUSES = frozenset({'draft', 'active', 'superseded', 'retired'})


class ComponentVocabularyError(RuntimeError):
    """Raised when governed component vocabulary is non-canonical."""


@dataclass(frozen=True)
class CanonicalComponentVocabulary:
    system_layers: frozenset[str]
    tiers: frozenset[str]
    statuses: frozenset[str]


CANONICAL_COMPONENT_VOCABULARY = CanonicalComponentVocabulary(
    system_layers=_CANONICAL_SYSTEM_LAYERS,
    tiers=_CANONICAL_TIERS,
    statuses=_CANONICAL_STATUSES,
)


def validate_component_identity_vocabulary(*, system_layer: str, tier: str, status: str) -> None:
    if system_layer not in _CANONICAL_SYSTEM_LAYERS:
        raise ComponentVocabularyError(
            f"Non-canonical system_layer {system_layer!r}. Allowed: {sorted(_CANONICAL_SYSTEM_LAYERS)!r}"
        )
    if tier not in _CANONICAL_TIERS:
        raise ComponentVocabularyError(
            f"Non-canonical tier {tier!r}. Allowed: {sorted(_CANONICAL_TIERS)!r}"
        )
    if status not in _CANONICAL_STATUSES:
        raise ComponentVocabularyError(
            f"Non-canonical status {status!r}. Allowed: {sorted(_CANONICAL_STATUSES)!r}"
        )


__all__ = [
    'CANONICAL_COMPONENT_VOCABULARY',
    'CanonicalComponentVocabulary',
    'ComponentVocabularyError',
    'validate_component_identity_vocabulary',
]

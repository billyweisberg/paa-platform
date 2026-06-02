"""Compatibility wrapper for the unified TechLead runtime host."""

import time

from paa_core.techlead_runtime_host import (
    TechLeadRuntimeHost,
    TechLeadRuntimeLoopResult,
    _TechLeadAssignmentPublisher,
    build_techlead_runtime_host,
)

__all__ = [
    'TechLeadRuntimeHost',
    'TechLeadRuntimeLoopResult',
    '_TechLeadAssignmentPublisher',
    'build_techlead_runtime_host',
]

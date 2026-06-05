from __future__ import annotations

from typing import Protocol

from paa_core.application.dto.methodology_execution import (
    ApplyMethodologyExecutionTransitionRequest,
    EvaluateMethodologyExecutionPreflightRequest,
    ExplainMethodologyExecutionRequest,
    GetMethodologyExecutionNextActionRequest,
    GetMethodologyExecutionStatusRequest,
    MethodologyExecutionOperationResult,
)


class MethodologyExecutionService(Protocol):
    def get_status(
        self, request: GetMethodologyExecutionStatusRequest
    ) -> MethodologyExecutionOperationResult: ...

    def get_next_action(
        self, request: GetMethodologyExecutionNextActionRequest
    ) -> MethodologyExecutionOperationResult: ...

    def explain(
        self, request: ExplainMethodologyExecutionRequest
    ) -> MethodologyExecutionOperationResult: ...

    def apply_transition(
        self, request: ApplyMethodologyExecutionTransitionRequest
    ) -> MethodologyExecutionOperationResult: ...

    def evaluate_preflight(
        self, request: EvaluateMethodologyExecutionPreflightRequest
    ) -> MethodologyExecutionOperationResult: ...

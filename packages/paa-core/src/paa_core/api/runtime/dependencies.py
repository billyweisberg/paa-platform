from __future__ import annotations

from paa_core.application.services import (
    DefaultAutomationPreflightApplicationService,
    DefaultQueueAdminApplicationService,
    DefaultRuntimeAdminApplicationService,
    DefaultRuntimeDispatchApplicationService,
    DefaultRuntimeReportApplicationService,
    DefaultRuntimeValidationApplicationService,
)


def get_queue_admin_service() -> DefaultQueueAdminApplicationService:
    return DefaultQueueAdminApplicationService()


def get_runtime_admin_service() -> DefaultRuntimeAdminApplicationService:
    return DefaultRuntimeAdminApplicationService()


def get_runtime_dispatch_service() -> DefaultRuntimeDispatchApplicationService:
    return DefaultRuntimeDispatchApplicationService()


def get_runtime_report_service() -> DefaultRuntimeReportApplicationService:
    return DefaultRuntimeReportApplicationService()


def get_runtime_validation_service() -> DefaultRuntimeValidationApplicationService:
    return DefaultRuntimeValidationApplicationService()


def get_automation_preflight_service() -> DefaultAutomationPreflightApplicationService:
    return DefaultAutomationPreflightApplicationService()

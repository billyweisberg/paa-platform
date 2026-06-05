from __future__ import annotations

from paa_core.application.services import (
    DefaultAutomationPreflightApplicationService,
    DefaultAuthorityInstallApplicationService,
    DefaultComponentTaxonomyApplicationService,
    DefaultOperatorCommandApplicationService,
    DefaultProducerCommandApplicationService,
    DefaultQueueAdminApplicationService,
    DefaultRuntimeAdminApplicationService,
    DefaultRuntimeDispatchApplicationService,
    DefaultRuntimeInstallApplicationService,
    DefaultRuntimeReportApplicationService,
    DefaultRuntimeValidationApplicationService,
    build_default_operator_command_service,
)


class _NullStructuredLogger:
    def info(self, event: str, **fields: object) -> None:
        del event, fields

    def warning(self, event: str, **fields: object) -> None:
        del event, fields


def get_operator_command_service() -> DefaultOperatorCommandApplicationService:
    return build_default_operator_command_service(logger=_NullStructuredLogger())


def get_authority_install_service() -> DefaultAuthorityInstallApplicationService:
    return DefaultAuthorityInstallApplicationService()


def get_component_taxonomy_service() -> DefaultComponentTaxonomyApplicationService:
    return DefaultComponentTaxonomyApplicationService()


def get_producer_command_service() -> DefaultProducerCommandApplicationService:
    return DefaultProducerCommandApplicationService()


def get_queue_admin_service() -> DefaultQueueAdminApplicationService:
    return DefaultQueueAdminApplicationService()


def get_runtime_admin_service() -> DefaultRuntimeAdminApplicationService:
    return DefaultRuntimeAdminApplicationService()


def get_runtime_dispatch_service() -> DefaultRuntimeDispatchApplicationService:
    return DefaultRuntimeDispatchApplicationService()


def get_runtime_install_service() -> DefaultRuntimeInstallApplicationService:
    return DefaultRuntimeInstallApplicationService()


def get_runtime_report_service() -> DefaultRuntimeReportApplicationService:
    return DefaultRuntimeReportApplicationService()


def get_runtime_validation_service() -> DefaultRuntimeValidationApplicationService:
    return DefaultRuntimeValidationApplicationService()


def get_automation_preflight_service() -> DefaultAutomationPreflightApplicationService:
    return DefaultAutomationPreflightApplicationService()

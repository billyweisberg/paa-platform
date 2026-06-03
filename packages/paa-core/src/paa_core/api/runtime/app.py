# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false
from __future__ import annotations

try:
    from fastapi import FastAPI
except ImportError as exc:  # pragma: no cover
    FastAPI = None
    _FASTAPI_IMPORT_ERROR = exc
else:
    _FASTAPI_IMPORT_ERROR = None

from paa_core.api.runtime.routers.authority import router as authority_router
from paa_core.api.runtime.routers.hosts import router as host_router
from paa_core.api.runtime.routers.ops import router as ops_router
from paa_core.api.runtime.routers.operators import router as operator_router
from paa_core.api.runtime.routers.packets import router as packet_router
from paa_core.api.runtime.routers.producer import router as producer_router
from paa_core.api.runtime.routers.queues import router as queue_router
from paa_core.api.runtime.routers.reports import router as report_router
from paa_core.api.runtime.routers.status import router as status_router
from paa_core.api.runtime.routers.supervisor import router as supervisor_router
from paa_core.api.runtime.routers.workflow import router as workflow_router


def build_runtime_api_app():
    if FastAPI is None:  # pragma: no cover
        raise RuntimeError(
            'FastAPI is required to build the PAA runtime API. Install the `paa-core` package dependencies first.'
        ) from _FASTAPI_IMPORT_ERROR

    app = FastAPI(
        title='PAA Runtime API',
        version='0.1.0',
        summary='HTTP gateway over PAA runtime application services.',
    )

    @app.get('/healthz')
    def healthz() -> dict[str, object]:
        return {'ok': True, 'service': 'paa-runtime-api'}

    app.include_router(supervisor_router)
    app.include_router(authority_router)
    app.include_router(host_router)
    app.include_router(ops_router)
    app.include_router(operator_router)
    app.include_router(packet_router)
    app.include_router(producer_router)
    app.include_router(queue_router)
    app.include_router(status_router)
    app.include_router(report_router)
    app.include_router(workflow_router)
    return app


__all__ = ['build_runtime_api_app']

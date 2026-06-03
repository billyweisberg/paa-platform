# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from paa_core.api.runtime.dependencies import get_runtime_dispatch_service
from paa_core.application.dto.runtime import RuntimeDispatchRequest
from paa_core.application.services import DefaultRuntimeDispatchApplicationService

router = APIRouter(prefix='/runtime/packets', tags=['runtime-packets'])


class PacketDispatchModel(BaseModel):
    repo_root: str
    message_file: str


def _build_dispatch_request(request: PacketDispatchModel) -> RuntimeDispatchRequest:
    return RuntimeDispatchRequest(
        repo_root=Path(request.repo_root).resolve(),
        message_file=Path(request.message_file).resolve(),
    )


@router.post('/dispatch')
def dispatch_runtime_packet(
    request: PacketDispatchModel,
    service: DefaultRuntimeDispatchApplicationService = Depends(get_runtime_dispatch_service),
) -> dict[str, object]:
    return service.dispatch_packet(_build_dispatch_request(request)).payload


@router.post('/dispatch-techlead')
def dispatch_techlead_runtime_packet(
    request: PacketDispatchModel,
    service: DefaultRuntimeDispatchApplicationService = Depends(get_runtime_dispatch_service),
) -> dict[str, object]:
    return service.dispatch_techlead_packet(_build_dispatch_request(request)).payload

# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from paa_core.api.runtime.dependencies import get_authority_install_service
from paa_core.application.dto.authority import AuthorityInstallRequest
from paa_core.application.services import DefaultAuthorityInstallApplicationService

router = APIRouter(prefix='/runtime/authority', tags=['runtime-authority'])


class AuthorityInstallModel(BaseModel):
    repo_root: str
    package_root: str
    authority_install_root: str | None = None


@router.post('/install-package')
def install_package(
    request: AuthorityInstallModel,
    service: DefaultAuthorityInstallApplicationService = Depends(get_authority_install_service),
) -> dict[str, object]:
    return service.install_package(
        AuthorityInstallRequest(
            repo_root=Path(request.repo_root).resolve(),
            package_root=Path(request.package_root).resolve(),
            authority_install_root=Path(request.authority_install_root).resolve() if request.authority_install_root else None,
        )
    ).payload


__all__ = ['router']

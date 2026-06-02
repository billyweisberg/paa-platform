from __future__ import annotations

from typing import Protocol

from paa_core.application.dto.authority import AuthorityInstallRequest, AuthorityInstallResultView


class AuthorityInstallService(Protocol):
    def install_package(self, request: AuthorityInstallRequest) -> AuthorityInstallResultView: ...

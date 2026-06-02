"""Runtime supervisor for starting the three default PAA runtime hosts together."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import threading
from typing import Any

from .dev_runtime import build_dev_runtime_host
from .qa_runtime import build_qa_runtime_host
from .techlead_runtime import build_techlead_runtime_host


@dataclass(frozen=True)
class RuntimeSupervisorHostSpec:
    host_key: str
    actor_name: str
    host_name: str
    intake_mode: str
    emit_flag_name: str
    emit_flag_value: bool


class RuntimeSupervisor:
    def __init__(
        self,
        *,
        techlead_host: object,
        dev_host: object,
        qa_host: object,
    ) -> None:
        self._hosts = {
            'techlead': techlead_host,
            'dev': dev_host,
            'qa': qa_host,
        }

    def run(
        self,
        *,
        intake_mode: str = 'claim_next',
        emit_next_assignment: bool = True,
        emit_worker_result: bool = True,
        emit_verification: bool = True,
        max_iterations: int = 0,
        poll_interval_seconds: float = 5.0,
    ) -> dict[str, Any]:
        host_specs = (
            RuntimeSupervisorHostSpec(
                host_key='techlead',
                actor_name='TechLead Agent',
                host_name='techlead-runtime-host',
                intake_mode=intake_mode,
                emit_flag_name='emit_next_assignment',
                emit_flag_value=emit_next_assignment,
            ),
            RuntimeSupervisorHostSpec(
                host_key='dev',
                actor_name='Dev Agent',
                host_name='dev-runtime-host',
                intake_mode=intake_mode,
                emit_flag_name='emit_worker_result',
                emit_flag_value=emit_worker_result,
            ),
            RuntimeSupervisorHostSpec(
                host_key='qa',
                actor_name='QA Agent',
                host_name='qa-runtime-host',
                intake_mode=intake_mode,
                emit_flag_name='emit_verification',
                emit_flag_value=emit_verification,
            ),
        )
        results: dict[str, Any] = {}
        errors: dict[str, str] = {}
        threads: list[threading.Thread] = []

        def _run_host(spec: RuntimeSupervisorHostSpec) -> None:
            try:
                host = self._hosts[spec.host_key]
                kwargs = {
                    'intake_mode': spec.intake_mode,
                    spec.emit_flag_name: spec.emit_flag_value,
                    'max_iterations': max_iterations,
                    'poll_interval_seconds': poll_interval_seconds,
                }
                results[spec.host_key] = host.run_loop(**kwargs)
            except Exception as exc:
                errors[spec.host_key] = str(exc)

        for spec in host_specs:
            thread = threading.Thread(
                target=_run_host,
                name=f'paa-{spec.host_key}-runtime',
                args=(spec,),
                daemon=False,
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        ok = not errors and len(results) == len(host_specs)
        return {
            'ok': ok,
            'host_count': len(host_specs),
            'intake_mode': intake_mode,
            'max_iterations': max_iterations,
            'poll_interval_seconds': poll_interval_seconds,
            'results': results,
            'errors': errors,
        }


def build_runtime_supervisor(
    repo_root: Path,
    *,
    techlead_actor_name: str = 'TechLead Agent',
    dev_actor_name: str = 'Dev Agent',
    qa_actor_name: str = 'QA Agent',
    techlead_host_name: str = 'techlead-runtime-host',
    dev_host_name: str = 'dev-runtime-host',
    qa_host_name: str = 'qa-runtime-host',
    logger: object | None = None,
) -> RuntimeSupervisor:
    resolved_repo_root = repo_root.expanduser().resolve()
    return RuntimeSupervisor(
        techlead_host=build_techlead_runtime_host(
            resolved_repo_root,
            actor_name=techlead_actor_name,
            host_name=techlead_host_name,
            logger=logger,
        ),
        dev_host=build_dev_runtime_host(
            resolved_repo_root,
            actor_name=dev_actor_name,
            host_name=dev_host_name,
            logger=logger,
        ),
        qa_host=build_qa_runtime_host(
            resolved_repo_root,
            actor_name=qa_actor_name,
            host_name=qa_host_name,
            logger=logger,
        ),
    )


__all__ = ['RuntimeSupervisor', 'RuntimeSupervisorHostSpec', 'build_runtime_supervisor']

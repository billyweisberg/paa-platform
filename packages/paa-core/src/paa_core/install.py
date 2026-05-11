"""Repo-local install/update helpers for PAA runtime payloads."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, UTC
import json
import shutil
import subprocess
import sys
from pathlib import Path

from paa_core.paths import CODEX_INSTALL_ROOT, PROJECT_DATA_ROOT, ensure_directory

PLATFORM_VERSION = "0.1.0"
SCHEMA_BUNDLE_VERSION = "0.1.0"
DEFAULT_PROJECT_PACK = "fractal-core"


@dataclass(frozen=True)
class InstallResult:
    """Summary of a repo-local install/update run."""

    repo_root: Path
    install_mode: str
    codex_install_root: Path
    runtime_data_root: Path
    platform_revision: str
    project_pack: str


@dataclass(frozen=True)
class AuthorityInstallResult:
    """Summary of an authority-package install into a consumer repo."""

    repo_root: Path
    package_root: Path
    authority_install_root: Path


def platform_repo_root() -> Path:
    """Resolve the platform repo root from the source tree layout."""
    metadata_path = Path(__file__).resolve().parents[2] / "install-metadata.json"
    if metadata_path.exists():
        try:
            metadata = json.loads(metadata_path.read_text())
        except Exception:
            metadata = {}
        configured_root = metadata.get("source_platform_repo_root")
        if configured_root:
            candidate = Path(str(configured_root)).expanduser().resolve()
            if candidate.exists():
                return candidate
    return Path(__file__).resolve().parents[4]


def platform_revision() -> str:
    """Resolve the current platform git revision."""

    root = platform_repo_root()
    return (
        subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        .stdout.strip()
    )


def project_pack_root(project_pack: str) -> Path:
    """Resolve a named project pack inside the platform repo."""

    root = platform_repo_root() / "project-packs" / project_pack
    if not root.exists():
        raise FileNotFoundError(
            f"Project pack '{project_pack}' not found under {platform_repo_root() / 'project-packs'}"
        )
    return root


def project_pack_manifest(project_pack: str) -> dict[str, object]:
    """Load a named project pack manifest."""

    manifest_path = project_pack_root(project_pack) / "pack.json"
    return json.loads(manifest_path.read_text())


def _copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)



def _copy_optional_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _install_selected_files(src_root: Path, dst_root: Path, names: list[str]) -> None:
    dst_root.mkdir(parents=True, exist_ok=True)
    for name in names:
        src = src_root / name
        if not src.exists():
            raise FileNotFoundError(f"Required runtime helper not found: {src}")
        _copy_file(src, dst_root / name)
        if src.suffix == ".sh" or src.suffix == ".py":
            (dst_root / name).chmod(0o755)


def _render_text_template(src: Path, dst: Path, replacements: dict[str, str]) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    text = src.read_text()
    for key, value in replacements.items():
        text = text.replace(key, value)
    dst.write_text(text)


def _install_rendered_tree(src: Path, dst: Path, replacements: dict[str, str]) -> None:
    if not src.exists():
        return
    if dst.exists():
        shutil.rmtree(dst)
    for path in src.rglob("*"):
        rel = path.relative_to(src)
        target = dst / rel
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        _render_text_template(path, target, replacements)


def _prune_installed_dirs(root: Path, allowed_dirs: set[str]) -> None:
    if not root.exists():
        return
    for child in root.iterdir():
        if child.is_file():
            continue
        if child.name not in allowed_dirs:
            shutil.rmtree(child)

def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")


def _manifest_names(manifest: dict[str, object], role: str, key: str) -> set[str]:
    return set(
        str(name)
        for name in ((manifest.get(role) or {}).get(key, []))  # type: ignore[union-attr]
    )


def _install_selected_rendered_dirs(
    src_root: Path,
    dst_root: Path,
    replacements: dict[str, str],
    allowed_dirs: set[str],
) -> None:
    dst_root.mkdir(parents=True, exist_ok=True)
    for child in src_root.iterdir():
        if child.is_file():
            _render_text_template(child, dst_root / child.name, replacements)
            continue
        if child.name in allowed_dirs:
            _install_rendered_tree(child, dst_root / child.name, replacements)
    _prune_installed_dirs(dst_root, allowed_dirs)


def _install_vendor_packages(codex_root: Path, package_specs: list[str]) -> None:
    if not package_specs:
        return
    vendor_root = codex_root / 'vendor'
    if vendor_root.exists():
        shutil.rmtree(vendor_root)
    vendor_root.mkdir(parents=True, exist_ok=True)
    if shutil.which("uv"):
        vendor_python = "3.12"
        subprocess.run(
            [
                "uv",
                "pip",
                "install",
                "--quiet",
                "--python",
                vendor_python,
                "--target",
                str(vendor_root),
                *package_specs,
            ],
            check=True,
        )
        lock_path = vendor_root / ".lock"
        if lock_path.exists():
            lock_path.unlink()
        return
    vendor_python = shutil.which("python3.12")
    if vendor_python is None:
        if sys.version_info >= (3, 12):
            vendor_python = sys.executable
        else:
            raise RuntimeError("PAA vendor install requires python3.12 or newer when uv is unavailable.")
    subprocess.run(
        [
            vendor_python,
            '-m',
            'pip',
            'install',
            '--quiet',
            '--disable-pip-version-check',
            '--no-compile',
            '--target',
            str(vendor_root),
            *package_specs,
        ],
        check=True,
    )


def _write_wrapper(script_path: Path, module_name: str) -> None:
    script_path.write_text(
        "#!/bin/sh\n"
        "set -eu\n\n"
        "SCRIPT_PATH=\"$0\"\n"
        "while [ -L \"$SCRIPT_PATH\" ]; do\n"
        "  SCRIPT_PATH=\"$(readlink \"$SCRIPT_PATH\")\"\n"
        "done\n"
        "SCRIPT_DIR=\"$(CDPATH= cd -- \"$(dirname -- \"$SCRIPT_PATH\")\" && pwd)\"\n"
        "REPO_ROOT=\"$(CDPATH= cd -- \"$SCRIPT_DIR/../../..\" && pwd)\"\n"
        "RUNTIME_ROOT=\"$REPO_ROOT/.codex/paa\"\n"
        "VENDOR_ROOT=\"$REPO_ROOT/.codex/paa/vendor\"\n"
        "LIB_ROOT=\"$REPO_ROOT/.codex/paa/lib\"\n"
        "export PYTHONPATH=\"$VENDOR_ROOT:$LIB_ROOT${PYTHONPATH:+:$PYTHONPATH}\"\n\n"
        "if [ -x \"$REPO_ROOT/.venv/bin/python\" ]; then\n"
        f"  exec \"$REPO_ROOT/.venv/bin/python\" -m {module_name} \"$@\"\n"
        "fi\n\n"
        "if command -v uv >/dev/null 2>&1; then\n"
        "  if [ -f \"$REPO_ROOT/pyproject.toml\" ]; then\n"
        f"    exec uv run --directory \"$RUNTIME_ROOT\" --python 3.12 --no-project python -m {module_name} \"$@\"\n"
        "  fi\n"
        f"  exec uv run --python 3.12 --isolated python -m {module_name} \"$@\"\n"
        "fi\n\n"
        "if [ -x \"/opt/homebrew/opt/python@3.13/bin/python3\" ]; then\n"
        f"  exec /opt/homebrew/opt/python@3.13/bin/python3 -m {module_name} \"$@\"\n"
        "fi\n\n"
        "if command -v python3.12 >/dev/null 2>&1; then\n"
        f"  exec python3.12 -m {module_name} \"$@\"\n"
        "fi\n\n"
        "if command -v python3 >/dev/null 2>&1; then\n"
        "  PYTHON_OK=\"$(python3 -c 'import sys; print(int(sys.version_info >= (3, 12)))')\"\n"
        "  if [ \"$PYTHON_OK\" = \"1\" ]; then\n"
        f"    exec python3 -m {module_name} \"$@\"\n"
        "  fi\n"
        "fi\n\n"
        "echo 'PAA wrapper requires uv with Python 3.12 support, or python3 >= 3.12 on PATH.' >&2\n"
        "exit 1\n"
    )
    script_path.chmod(0o755)


def _install_common_layout(
    repo_root: Path,
    *,
    mode: str,
    package_names: list[str],
    example_config_name: str,
    project_pack: str,
    vendor_packages: list[str] | None = None,
) -> InstallResult:
    root = platform_repo_root()
    codex_root = ensure_directory(repo_root / CODEX_INSTALL_ROOT)
    runtime_root = ensure_directory(repo_root / PROJECT_DATA_ROOT)

    ensure_directory(codex_root / "bin")
    ensure_directory(codex_root / "lib")
    ensure_directory(codex_root / "scripts" / "runtime")
    ensure_directory(codex_root / 'schemas' / 'authority-package')
    ensure_directory(codex_root / 'schemas' / 'handoff-packets')
    ensure_directory(codex_root / 'schemas' / 'runtime-records')
    ensure_directory(codex_root / 'templates' / 'configs')
    ensure_directory(codex_root / 'vendor')

    for package_name in package_names:
        src = root / "packages" / package_name / "src"
        pkg_dirs = [p for p in src.iterdir() if p.is_dir()]
        for pkg_dir in pkg_dirs:
            _copy_tree(pkg_dir, codex_root / "lib" / pkg_dir.name)

    for schema_group in ['authority-package', 'handoff-packets', 'runtime-records']:
        schema_root = root / 'schemas' / schema_group
        if schema_root.exists():
            for schema_path in schema_root.glob('*.json'):
                _copy_file(schema_path, codex_root / 'schemas' / schema_group / schema_path.name)

    templates_root = root / "templates" / "configs"
    for template_path in templates_root.glob("*.json"):
        _copy_file(template_path, codex_root / "templates" / "configs" / template_path.name)

    _copy_file(templates_root / example_config_name, codex_root / "project-config.example.json")

    _install_vendor_packages(codex_root, vendor_packages or [])

    _write_json(
        codex_root / "install-metadata.json",
        {
            "platform_version": PLATFORM_VERSION,
            "install_mode": mode,
            "project_pack": project_pack,
            "installed_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "source_platform_repo": "https://github.com/billyweisberg/paa-platform",
            "source_platform_repo_root": str(root),
            "source_platform_revision": platform_revision(),
            "schema_bundle_version": SCHEMA_BUNDLE_VERSION,
        },
    )

    return InstallResult(
        repo_root=repo_root,
        install_mode=mode,
        codex_install_root=codex_root,
        runtime_data_root=runtime_root,
        platform_revision=platform_revision(),
        project_pack=project_pack,
    )


def install_producer_runtime(repo_root: Path, project_pack: str = DEFAULT_PROJECT_PACK) -> InstallResult:
    """Install or update the producer-mode repo-local PAA payload."""

    root = platform_repo_root()
    result = _install_common_layout(
        repo_root,
        mode="producer",
        package_names=["paa-core", "paa-producer"],
        example_config_name="project-config.producer.example.json",
        project_pack=project_pack,
        vendor_packages=[],
    )
    pack_root = project_pack_root(project_pack)
    manifest = project_pack_manifest(project_pack)
    replacements = {"{{REPO_ROOT}}": str(repo_root.resolve())}
    ensure_directory(result.runtime_data_root / "publish")
    ensure_directory(result.runtime_data_root / "cache")
    _write_wrapper(result.codex_install_root / 'bin' / 'paa-producer', 'paa_producer')
    _install_selected_files(
        root / "scripts" / "runtime",
        result.codex_install_root / "scripts" / "runtime",
        [
            "bootstrap_automation_logging.sh",
            "install_pilot_authority_overlay.py",
            "log_automation_event.py",
            "run_automation_preflight_with_logging.sh",
        ],
    )
    _install_selected_rendered_dirs(
        pack_root / 'skills',
        repo_root / '.codex' / 'skills',
        replacements,
        _manifest_names(manifest, 'producer', 'skills'),
    )
    _install_selected_rendered_dirs(
        pack_root / 'automations',
        repo_root / '.codex' / 'automations',
        replacements,
        _manifest_names(manifest, 'producer', 'automations'),
    )
    config_root = pack_root / 'config'
    if config_root.exists():
        for config_path in config_root.glob('*.json'):
            _copy_file(config_path, result.codex_install_root / config_path.name)
    (result.codex_install_root / 'README.md').write_text(
        "# Repo-local PAA install\n\n"
        f"This repo carries the producer-mode PAA payload under `.codex/paa/`.\n"
        f"Selected project pack: `{project_pack}`.\n"
    )
    return result


def install_consumer_runtime(repo_root: Path, project_pack: str = DEFAULT_PROJECT_PACK) -> InstallResult:
    """Install or update the consumer-mode repo-local PAA payload."""

    root = platform_repo_root()
    result = _install_common_layout(
        repo_root,
        mode="consumer",
        package_names=["paa-core", "paa-consumer", "paa-producer"],
        example_config_name="project-config.consumer.example.json",
        project_pack=project_pack,
        vendor_packages=['jsonschema>=4,<5'],
    )
    pack_root = project_pack_root(project_pack)
    manifest = project_pack_manifest(project_pack)
    replacements = {"{{REPO_ROOT}}": str(repo_root.resolve())}
    for name in ["authority/current", "claims", "queue-state", "artifacts", "evidence", "cache", "reports"]:
        ensure_directory(result.runtime_data_root / name)
    _write_wrapper(result.codex_install_root / 'bin' / 'paa-consumer', 'paa_consumer')
    _write_wrapper(result.codex_install_root / 'bin' / 'paa-producer', 'paa_producer')
    _install_selected_files(
        root / "scripts" / "runtime",
        result.codex_install_root / "scripts" / "runtime",
        [
            "bootstrap_automation_logging.sh",
            "install_pilot_authority_overlay.py",
            "log_automation_event.py",
            "run_automation_preflight_with_logging.sh",
        ],
    )
    _install_selected_rendered_dirs(
        pack_root / 'skills',
        repo_root / '.codex' / 'skills',
        replacements,
        _manifest_names(manifest, 'consumer', 'skills'),
    )
    _install_selected_rendered_dirs(
        pack_root / 'automations',
        repo_root / '.codex' / 'automations',
        replacements,
        _manifest_names(manifest, 'consumer', 'automations'),
    )
    config_root = pack_root / 'config'
    if config_root.exists():
        for config_path in config_root.glob('*.json'):
            _copy_file(config_path, result.codex_install_root / config_path.name)
    (result.codex_install_root / 'README.md').write_text(
        "# Repo-local PAA install\n\n"
        f"This repo carries the consumer-mode PAA payload under `.codex/paa/`.\n"
        f"Selected project pack: `{project_pack}`.\n"
    )
    return result


def install_authority_package(repo_root: Path, package_root: Path, authority_install_root: Path | None = None) -> AuthorityInstallResult:
    """Install a published authority package into a consumer repo runtime root."""

    destination = authority_install_root or (repo_root / PROJECT_DATA_ROOT / "authority" / "current")
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for child in package_root.iterdir():
        target = destination / child.name
        if child.is_dir():
            shutil.copytree(child, target)
        else:
            shutil.copy2(child, target)
    return AuthorityInstallResult(
        repo_root=repo_root,
        package_root=package_root,
        authority_install_root=destination,
    )

"""Component-spec table extraction and narrow materialization seed models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
from typing import Any

from .component_vocabulary import validate_component_identity_vocabulary


_REQUIRED_SECTIONS = (
    "Component Identity Table",
    "Component Elements Table",
    "Realizations Table",
    "Plan Seed Table",
    "Activity Seed Table",
    "Activity Dependency Table",
    "Verification Surface Table",
)


class ComponentSpecExtractionError(RuntimeError):
    """Raised when a governed component-spec doc cannot be extracted safely."""


@dataclass(frozen=True)
class ComponentIdentitySeed:
    component_name: str
    component_kind: str
    alignment_state: str
    system_layer: str
    tier: str
    status: str


@dataclass(frozen=True)
class ComponentElementSeed:
    element_name: str
    element_kind: str
    description: str
    owned_by_component: str


@dataclass(frozen=True)
class ComponentRealizationSeed:
    element_name: str
    realization_kind: str
    artifact_kind: str
    artifact_target: str
    verification_role: str
    realization_key: str


@dataclass(frozen=True)
class ImplementationPlanSeed:
    plan_name: str
    consumer_context_key: str
    primary_component_name: str
    implementation_target_kind: str
    plan_status: str


@dataclass(frozen=True)
class ActivitySeed:
    activity_key: str
    activity_name: str
    sequence: int
    activity_kind: str
    element_name: str
    realization_kind: str
    done_definition: str


@dataclass(frozen=True)
class ActivityDependencySeed:
    activity_key: str
    depends_on_activity_key: str
    dependency_kind: str


@dataclass(frozen=True)
class VerificationSurfaceSeed:
    verification_surface: str
    verification_kind: str
    artifact_target: str
    required_for_acceptance: bool


@dataclass(frozen=True)
class ComponentSpecMaterializationSeed:
    source_path: str
    component_identity: ComponentIdentitySeed
    component_elements: tuple[ComponentElementSeed, ...]
    realizations: tuple[ComponentRealizationSeed, ...]
    plan_seed: ImplementationPlanSeed
    activity_seeds: tuple[ActivitySeed, ...]
    activity_dependencies: tuple[ActivityDependencySeed, ...]
    verification_surfaces: tuple[VerificationSurfaceSeed, ...]


_SECTION_RE = re.compile(r"^##\s+(?P<title>.+?)\s*$")


def _slug_component_name(component_name: str) -> str:
    pieces = re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?=[A-Z]|$)", component_name)
    normalized = [piece.lower() for piece in pieces if piece]
    if normalized:
        return "_".join(normalized)
    return component_name.replace("-", "_").replace(" ", "_").lower()


def _parse_markdown_table(lines: list[str], start_index: int) -> tuple[list[str], list[dict[str, str]], int]:
    if start_index >= len(lines) or not lines[start_index].lstrip().startswith("|"):
        raise ComponentSpecExtractionError("Expected Markdown table directly under section heading.")
    raw_table_lines: list[str] = []
    index = start_index
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            break
        if not line.lstrip().startswith("|"):
            break
        raw_table_lines.append(line.rstrip("\n"))
        index += 1
    if len(raw_table_lines) < 2:
        raise ComponentSpecExtractionError("Markdown table must include header and delimiter rows.")
    header_cells = _split_table_row(raw_table_lines[0])
    delimiter_cells = _split_table_row(raw_table_lines[1])
    if len(header_cells) != len(delimiter_cells):
        raise ComponentSpecExtractionError("Markdown table delimiter does not match header width.")
    rows: list[dict[str, str]] = []
    for row_line in raw_table_lines[2:]:
        cells = _split_table_row(row_line)
        if len(cells) != len(header_cells):
            raise ComponentSpecExtractionError("Markdown table row width does not match header width.")
        rows.append({header_cells[i]: cells[i] for i in range(len(header_cells))})
    return header_cells, rows, index


def _split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        raise ComponentSpecExtractionError("Malformed Markdown table row.")
    cells = stripped[1:-1].split("|")
    return [cell.strip().strip("`") for cell in cells]


def _require_columns(section_name: str, row_headers: list[str], required_columns: tuple[str, ...]) -> None:
    missing = [column for column in required_columns if column not in row_headers]
    if missing:
        joined = ", ".join(missing)
        raise ComponentSpecExtractionError(f"Section '{section_name}' is missing required columns: {joined}")


def _require_single_row(section_name: str, rows: list[dict[str, str]]) -> dict[str, str]:
    if len(rows) != 1:
        raise ComponentSpecExtractionError(
            f"Section '{section_name}' must contain exactly one data row; found {len(rows)}."
        )
    return rows[0]


def extract_component_spec_materialization_seed(path: str | Path) -> ComponentSpecMaterializationSeed:
    source_path = Path(path)
    lines = source_path.read_text().splitlines()
    section_tables: dict[str, tuple[list[str], list[dict[str, str]]]] = {}
    index = 0
    while index < len(lines):
        match = _SECTION_RE.match(lines[index])
        if not match:
            index += 1
            continue
        section_name = match.group("title")
        next_index = index + 1
        while next_index < len(lines) and not lines[next_index].strip():
            next_index += 1
        if next_index < len(lines) and lines[next_index].lstrip().startswith("|"):
            headers, rows, after_index = _parse_markdown_table(lines, next_index)
            section_tables[section_name] = (headers, rows)
            index = after_index
            continue
        index = next_index

    for required_section in _REQUIRED_SECTIONS:
        if required_section not in section_tables:
            raise ComponentSpecExtractionError(f"Missing required section table: {required_section}")

    identity_headers, identity_rows = section_tables["Component Identity Table"]
    _require_columns(
        "Component Identity Table",
        identity_headers,
        ("component_name", "component_kind", "alignment_state", "system_layer", "tier", "status"),
    )
    identity_row = _require_single_row("Component Identity Table", identity_rows)
    component_identity = ComponentIdentitySeed(
        component_name=identity_row["component_name"],
        component_kind=identity_row["component_kind"],
        alignment_state=identity_row["alignment_state"],
        system_layer=identity_row["system_layer"],
        tier=identity_row["tier"],
        status=identity_row["status"],
    )
    validate_component_identity_vocabulary(
        system_layer=component_identity.system_layer,
        tier=component_identity.tier,
        status=component_identity.status,
    )

    element_headers, element_rows = section_tables["Component Elements Table"]
    _require_columns(
        "Component Elements Table",
        element_headers,
        ("element_name", "element_kind", "description", "owned_by_component"),
    )
    component_elements = tuple(
        ComponentElementSeed(
            element_name=row["element_name"],
            element_kind=row["element_kind"],
            description=row["description"],
            owned_by_component=row["owned_by_component"],
        )
        for row in element_rows
    )

    known_element_names = {element.element_name for element in component_elements}
    component_slug = _slug_component_name(component_identity.component_name)

    realization_headers, realization_rows = section_tables["Realizations Table"]
    _require_columns(
        "Realizations Table",
        realization_headers,
        ("element_name", "realization_kind", "artifact_kind", "artifact_target", "verification_role"),
    )
    realizations_list: list[ComponentRealizationSeed] = []
    for row in realization_rows:
        element_name = row["element_name"]
        if element_name not in known_element_names:
            raise ComponentSpecExtractionError(
                f"Realization references unknown element_name '{element_name}'."
            )
        realization_kind = row["realization_kind"]
        realizations_list.append(
            ComponentRealizationSeed(
                element_name=element_name,
                realization_kind=realization_kind,
                artifact_kind=row["artifact_kind"],
                artifact_target=row["artifact_target"],
                verification_role=row["verification_role"],
                realization_key=f"{component_slug}__{element_name}__{realization_kind}",
            )
        )
    realizations = tuple(realizations_list)

    plan_headers, plan_rows = section_tables["Plan Seed Table"]
    _require_columns(
        "Plan Seed Table",
        plan_headers,
        ("plan_name", "consumer_context_key", "primary_component_name", "implementation_target_kind", "plan_status"),
    )
    plan_row = _require_single_row("Plan Seed Table", plan_rows)
    plan_seed = ImplementationPlanSeed(
        plan_name=plan_row["plan_name"],
        consumer_context_key=plan_row["consumer_context_key"],
        primary_component_name=plan_row["primary_component_name"],
        implementation_target_kind=plan_row["implementation_target_kind"],
        plan_status=plan_row["plan_status"],
    )

    activity_headers, activity_rows = section_tables["Activity Seed Table"]
    _require_columns(
        "Activity Seed Table",
        activity_headers,
        (
            "activity_key",
            "activity_name",
            "sequence",
            "activity_kind",
            "element_name",
            "realization_kind",
            "done_definition",
        ),
    )
    activity_seeds_list: list[ActivitySeed] = []
    known_activity_keys: set[str] = set()
    for row in activity_rows:
        element_name = row["element_name"]
        if element_name not in known_element_names:
            raise ComponentSpecExtractionError(
                f"Activity references unknown element_name '{element_name}'."
            )
        activity_key = row["activity_key"]
        known_activity_keys.add(activity_key)
        activity_seeds_list.append(
            ActivitySeed(
                activity_key=activity_key,
                activity_name=row["activity_name"],
                sequence=int(row["sequence"]),
                activity_kind=row["activity_kind"],
                element_name=element_name,
                realization_kind=row["realization_kind"],
                done_definition=row["done_definition"],
            )
        )
    activity_seeds = tuple(activity_seeds_list)

    dependency_headers, dependency_rows = section_tables["Activity Dependency Table"]
    _require_columns(
        "Activity Dependency Table",
        dependency_headers,
        ("activity_key", "depends_on_activity_key", "dependency_kind"),
    )
    dependency_list: list[ActivityDependencySeed] = []
    for row in dependency_rows:
        activity_key = row["activity_key"]
        depends_on = row["depends_on_activity_key"]
        if activity_key not in known_activity_keys:
            raise ComponentSpecExtractionError(
                f"Dependency references unknown activity_key '{activity_key}'."
            )
        if depends_on not in known_activity_keys:
            raise ComponentSpecExtractionError(
                f"Dependency references unknown depends_on_activity_key '{depends_on}'."
            )
        dependency_list.append(
            ActivityDependencySeed(
                activity_key=activity_key,
                depends_on_activity_key=depends_on,
                dependency_kind=row["dependency_kind"],
            )
        )
    activity_dependencies = tuple(dependency_list)

    verification_headers, verification_rows = section_tables["Verification Surface Table"]
    _require_columns(
        "Verification Surface Table",
        verification_headers,
        ("verification_surface", "verification_kind", "artifact_target", "required_for_acceptance"),
    )
    verification_list: list[VerificationSurfaceSeed] = []
    for row in verification_rows:
        required_raw = row["required_for_acceptance"]
        if required_raw not in {"true", "false"}:
            raise ComponentSpecExtractionError(
                "Verification Surface Table requires 'required_for_acceptance' to be 'true' or 'false'."
            )
        verification_list.append(
            VerificationSurfaceSeed(
                verification_surface=row["verification_surface"],
                verification_kind=row["verification_kind"],
                artifact_target=row["artifact_target"],
                required_for_acceptance=required_raw == "true",
            )
        )
    verification_surfaces = tuple(verification_list)

    return ComponentSpecMaterializationSeed(
        source_path=str(source_path),
        component_identity=component_identity,
        component_elements=component_elements,
        realizations=realizations,
        plan_seed=plan_seed,
        activity_seeds=activity_seeds,
        activity_dependencies=activity_dependencies,
        verification_surfaces=verification_surfaces,
    )


def seed_as_jsonable(seed: ComponentSpecMaterializationSeed) -> dict[str, Any]:
    return asdict(seed)


__all__ = [
    "ActivityDependencySeed",
    "ActivitySeed",
    "ComponentElementSeed",
    "ComponentIdentitySeed",
    "ComponentRealizationSeed",
    "ComponentSpecExtractionError",
    "ComponentSpecMaterializationSeed",
    "ImplementationPlanSeed",
    "VerificationSurfaceSeed",
    "extract_component_spec_materialization_seed",
    "seed_as_jsonable",
]

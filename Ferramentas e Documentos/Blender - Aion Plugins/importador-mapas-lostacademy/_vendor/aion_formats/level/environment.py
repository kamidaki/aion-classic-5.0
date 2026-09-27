from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
import math
from xml.etree import ElementTree


TEXTURE_FIELDS = tuple(f"skybox_texture{index}" for index in range(4)) + ("cloud_texture",)


@dataclass(frozen=True)
class EnvironmentLighting:
    ray_direction: tuple[float, float, float] | None
    sun_color: tuple[float, float, float] | None
    ambient_color: tuple[float, float, float]
    sun_status: str
    source: str = "Environment/Lighting_000 (static reference, not TimeEnv sun)"
    direction_mapping: str = "CryEngine1_reference_ray=(SunVector.y,SunVector.x,SunVector.z)"
    color_source: str = "Environment/EnvState/SunColor"
    units: str = "preview_rgb_div_255; Blender strength is user-controlled, not game units"


def lighting_preview_settings(environment):
    profile = environment.selected_time_option
    if profile is None:
        raise ValueError("missing_explicit_time_profile")
    ambient = tuple(float(value) for value in profile.get("env_color", "").split(","))
    if len(ambient) != 3 or any(not math.isfinite(value) or not 0 <= value <= 255 for value in ambient):
        raise ValueError("invalid_profile_env_color")
    ambient = tuple(value / 255 for value in ambient)
    if profile.get("sky_sun_check") != "1":
        return EnvironmentLighting(None, None, ambient, "sun_disabled_or_unspecified_in_profile")
    lighting = environment.sections.get("Lighting_000", {})
    if lighting.get("Lighting") != "1":
        return EnvironmentLighting(None, None, ambient, "static_lighting_disabled_or_absent")
    sun_color_raw = environment.sections.get("EnvState", {}).get("SunColor")
    if not lighting.get("SunVector") or not sun_color_raw:
        return EnvironmentLighting(None, None, ambient, "missing_static_sun_data")
    direction = tuple(float(value) for value in lighting["SunVector"].split(","))
    if len(direction) != 3 or any(not math.isfinite(value) for value in direction):
        raise ValueError("invalid_static_sun_vector")
    length = math.hypot(*direction)
    if length < 1e-8:
        raise ValueError("zero_static_sun_vector")
    sun_color = tuple(float(value) for value in sun_color_raw.split(","))
    if len(sun_color) != 3 or any(not math.isfinite(value) or not 0 <= value <= 255 for value in sun_color):
        raise ValueError("invalid_static_sun_color")
    return EnvironmentLighting(
        (direction[1] / length, direction[0] / length, direction[2] / length),
        tuple(value / 255 for value in sun_color),
        ambient, "static_reference_only",
    )


@dataclass(frozen=True)
class EnvironmentTexture:
    field: str
    reference: str
    resolved_path: str | None
    status: str


@dataclass(frozen=True)
class LevelEnvironment:
    source_file: str
    mission_time: str | None
    sections: dict[str, dict[str, str]]
    skybox_reference: str
    library_file: str | None
    profile_name: str
    profile_parameters: dict[str, str]
    textures: tuple[EnvironmentTexture, ...]
    status: str
    warnings: tuple[str, ...]
    time_options: tuple[dict[str, str], ...]
    selected_time_option: dict[str, str] | None
    render_ready: bool = False


def _client_file(client_root: Path, reference: str) -> tuple[Path | None, str]:
    normalized = reference.replace("\\", "/")
    if not normalized:
        return None, "not_specified"
    if PureWindowsPath(reference).drive or normalized.startswith("/"):
        return None, "unsafe_path"
    parts = normalized.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return None, "unsafe_path"
    current = client_root.resolve()
    for part in parts:
        if not current.is_dir():
            return None, "missing"
        matches = [entry for entry in current.iterdir() if entry.name.casefold() == part.casefold()]
        if not matches:
            return None, "missing"
        if len(matches) != 1:
            return None, "ambiguous_path"
        current = matches[0].resolve()
        if not current.is_relative_to(client_root.resolve()):
            return None, "unsafe_path"
    return (current, "resolved") if current.is_file() else (None, "missing")


def resolve_level_environment(
    mission_path: str | Path, client_root: str | Path, *, time_option: str | None = None,
) -> LevelEnvironment:
    source = Path(mission_path)
    root_path = Path(client_root)
    mission_time = None
    sections = {}
    skybox = ""
    library_file = None
    profile_name = ""
    parameters = {}
    textures = ()
    time_options = ()
    selected_time_option = None
    warnings = ["skybox_projection_not_verified", "lighting_units_and_basis_not_verified"]

    def result(status):
        return LevelEnvironment(
            str(source), mission_time, sections, skybox, library_file, profile_name,
            parameters, textures, status, tuple(warnings), time_options, selected_time_option,
        )

    if not source.is_file():
        return result("missing_mission")
    mission = ElementTree.parse(source).getroot()
    mission_time = mission.get("Time")
    environment = mission.find("Environment")
    if environment is None:
        return result("missing_environment")
    for section in environment:
        if section.tag in sections:
            raise ValueError(f"Duplicate environment section: {section.tag}")
        sections[section.tag] = dict(section.attrib)
    if mission.find("EnvSetManager") is not None:
        warnings.append("environment_sets_not_evaluated")
    time_options = tuple(dict(option.attrib) for option in mission.findall("TimeEnvSystem/TimeEnvOption"))
    if mission.find("TimeofDayEnvSystem") is not None:
        warnings.append("time_of_day_curves_not_evaluated")
    skybox = sections.get("Shaders", {}).get("SkyBox", "")
    if time_option is not None:
        matches = [option for option in time_options if option.get("name") == time_option]
        if len(matches) != 1:
            return result("missing_time_option" if not matches else "ambiguous_time_option")
        selected_time_option = matches[0]
        skybox = selected_time_option.get("sky_box_name", "")
    if not skybox:
        return result("missing_skybox_reference")
    library_name, separator, profile_name = skybox.partition(".")
    if not separator:
        return result("legacy_shader_unresolved")
    if not profile_name or any(char in library_name for char in "/\\:"):
        return result("invalid_skybox_reference")
    library_path, path_status = _client_file(root_path, f"data/skybox/xml/{library_name}.xml")
    if library_path is None:
        warnings.append(f"library_path:{path_status}")
        return result("missing_skybox_library")
    library_file = str(library_path)
    library = ElementTree.parse(library_path).getroot()
    if library.tag != "SkyboxLibrary" or library.get("Name", "").casefold() != library_name.casefold():
        return result("library_identity_mismatch")
    profiles = [entry for entry in library.findall("Skybox") if entry.get("Name", "").casefold() == profile_name.casefold()]
    if len(profiles) != 1:
        return result("missing_skybox_profile" if not profiles else "ambiguous_skybox_profile")
    params = profiles[0].find("Params")
    if params is None:
        return result("missing_profile_parameters")
    parameters = dict(params.attrib)
    resolved = []
    for field in TEXTURE_FIELDS:
        reference = parameters.get(field, "")
        path, status = _client_file(root_path, reference)
        resolved.append(EnvironmentTexture(field, reference, str(path) if path else None, status))
        if reference and status != "resolved":
            warnings.append(f"{field}:{status}")
    textures = tuple(resolved)
    return result("resolved")

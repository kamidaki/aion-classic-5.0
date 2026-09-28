"""
Data model for Aion NPC metadata (AionNPCMetadata).
Canonical data definition supporting bidirectional sync between Blender,
the Aion Client (data/npcs/npcs.pak -> client_npcs.xml and data/Strings/Strings.pak -> client_strings_npc.xml),
and the Game Server Emulator (npc_templates.xml).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class AionNPCMetadata:
    """Authoritative representation of an Aion NPC template.

    Covers all canonical fields specified in PLUGIN-MODEL3D_IMPROVEMENT.MD Items 5.1 and 7.2.
    """

    # Identification
    npc_id: int = 900001
    name: str = "Novo_NPC"
    desc: str = "STR_NPC_NOVO_NPC"
    string_id: int = 799999
    string_body: str = "Novo NPC"

    # Mesh & Visual Representation
    dir: str = "NPC/ShugoMale"
    mesh: str = "ShugoMale"
    material: str = "mat_mob_reptile"
    foot_mat: str = "foot_etc"
    show_dmg_decal: int = 0
    ui_type: str = "general"
    cursor_type: str = "talk"
    erect: int = 1

    # Bounding Radius & Scale
    bound_front: float = 0.5
    bound_side: float = 0.5
    bound_upper: float = 2.0
    scale: float = 100.0
    weapon_scale: float = 100.0
    altitude: float = 0.0

    # Vision & Perception
    stare_angle: float = 75.0
    stare_distance: float = 20.0
    sensory_range: float = 15.0
    sangle: int = 240

    # Movement Speeds (m/s)
    move_speed_normal_walk: float = 1.5
    move_speed_normal_run: float = 6.0

    # Combat & Stats
    ammo_bone: str = "Bip01 Head"
    ammo_speed: int = 50
    hpgauge_level: int = 3
    level: int = 1
    max_hp: int = 10000
    attack_speed: int = 2000

    # AI & Factions
    ai_name: str = "General"
    tribe: str = "GENERAL"
    npc_type: str = "GENERAL"
    rank: str = "NOVICE"
    rating: str = "NORMAL"
    race: str = ""

    # Extra arbitrary attributes
    extra_attrs: Dict[str, Any] = field(default_factory=dict)

    def to_client_npc_xml(self) -> str:
        """Generates canonical <npc_client> XML block for data/npcs/npcs.pak -> client_npcs.xml."""
        return (
            f"  <npc_client>\n"
            f"    <id>{self.npc_id}</id>\n"
            f"    <name>{self.name}</name>\n"
            f"    <desc>{self.desc}</desc>\n"
            f"    <dir>{self.dir}</dir>\n"
            f"    <mesh>{self.mesh}</mesh>\n"
            f"    <material>{self.material}</material>\n"
            f"    <foot_mat>{self.foot_mat}</foot_mat>\n"
            f"    <show_dmg_decal>{self.show_dmg_decal}</show_dmg_decal>\n"
            f"    <ui_type>{self.ui_type}</ui_type>\n"
            f"    <cursor_type>{self.cursor_type}</cursor_type>\n"
            f"    <erect>{self.erect}</erect>\n"
            f"    <bound_radius front=\"{self.bound_front:.6f}\" side=\"{self.bound_side:.6f}\" upper=\"{self.bound_upper:.6f}\" />\n"
            f"    <scale>{int(self.scale)}</scale>\n"
            f"    <weapon_scale>{int(self.weapon_scale)}</weapon_scale>\n"
            f"    <altitude>{self.altitude:.6f}</altitude>\n"
            f"    <stare_angle>{self.stare_angle:.1f}</stare_angle>\n"
            f"    <stare_distance>{self.stare_distance:.1f}</stare_distance>\n"
            f"    <move_speed_normal_walk>{self.move_speed_normal_walk:.6f}</move_speed_normal_walk>\n"
            f"    <move_speed_normal_run>{self.move_speed_normal_run:.6f}</move_speed_normal_run>\n"
            f"    <ammo_bone>{self.ammo_bone}</ammo_bone>\n"
            f"    <ammo_speed>{self.ammo_speed}</ammo_speed>\n"
            f"    <hpgauge_level>{self.hpgauge_level}</hpgauge_level>\n"
            f"    <ai_name>{self.ai_name}</ai_name>\n"
            f"    <tribe>{self.tribe}</tribe>\n"
            f"    <sensory_range>{self.sensory_range:.1f}</sensory_range>\n"
            f"  </npc_client>"
        )

    def to_client_string_xml(self) -> str:
        """Generates canonical <string> XML block for data/Strings/Strings.pak -> client_strings_npc.xml."""
        body_text = self.string_body if self.string_body else self.name
        return (
            f"  <string>\n"
            f"    <name>{self.desc}</name>\n"
            f"    <id>{self.string_id}</id>\n"
            f"    <body>{body_text}</body>\n"
            f"  </string>"
        )

    def to_emulator_dict(self) -> Dict[str, Any]:
        """Returns keyword arguments suitable for EmulatorExporter.export_npc()."""
        return {
            "npc_id": self.npc_id,
            "name": self.string_body if self.string_body else self.name,
            "name_id": self.string_id,
            "level": self.level,
            "height": self.scale / 100.0,
            "max_hp": self.max_hp,
            "race": self.race,
            "tribe": self.tribe,
            "npc_type": self.npc_type,
            "ai": self.ai_name,
            "srange": int(self.sensory_range),
            "sangle": self.sangle,
            "attack_speed": self.attack_speed,
            "hpgauge": self.hpgauge_level,
            "rank": self.rank,
            "rating": self.rating,
            "walk_speed": self.move_speed_normal_walk,
            "run_speed": self.move_speed_normal_run,
            "bound_front": self.bound_front,
            "bound_side": self.bound_side,
            "bound_upper": self.bound_upper,
            "extra_attrs": self.extra_attrs if self.extra_attrs else None,
        }

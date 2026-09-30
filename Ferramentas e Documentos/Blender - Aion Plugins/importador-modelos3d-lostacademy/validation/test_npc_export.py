"""
Automated verification suite for NPC creation, Client/Emulator export, and Multi-model lineup.
Validates Phase 3 (Stage Layout & Lineup) and Phase 4 (NPC Metadata & Round-trip Export)
of PLUGIN-MODEL3D_IMPROVEMENT.MD.
"""
from __future__ import annotations

import io
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

# Add plugin to sys.path
_PLUGIN_DIR = Path(__file__).resolve().parents[1]
_ADDONS_ROOT = _PLUGIN_DIR.parent
if str(_ADDONS_ROOT) not in sys.path:
    sys.path.insert(0, str(_ADDONS_ROOT))
if str(_PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_DIR))

import bpy
import addon_utils

ADDON_NAME = "importador-modelos3d-lostacademy"
addon_utils.enable(ADDON_NAME, default_set=True)

import importlib
mod = importlib.import_module(ADDON_NAME)
AionNPCMetadata = mod.exporters.AionNPCMetadata
ClientNPCExporter = mod.exporters.ClientNPCExporter
EmulatorExporter = mod.exporters.EmulatorExporter
ViewerStage = mod.viewers.ViewerStage
apply_lineup_offset = mod.viewers.apply_lineup_offset
calculate_next_model_x_offset = mod.viewers.calculate_next_model_x_offset


def test_npc_metadata():
    print("\n[Step 1] Testing AionNPCMetadata data class & XML generation...")
    meta = AionNPCMetadata(
        npc_id=290001,
        name="Novo_NPC_Custom",
        desc="STR_NPC_NOVO_NPC_CUSTOM",
        string_id=799999,
        string_body="Novo Guarda de Sanctum",
        dir="Monster/NovoMonstro",
        mesh="NovoMonstro",
        material="mat_mob_reptile",
        foot_mat="foot_etc",
        bound_front=1.2,
        bound_side=1.2,
        bound_upper=2.5,
        scale=100.0,
        level=50,
        max_hp=45000,
        ai_name="General",
        tribe="GUARD",
    )

    client_xml = meta.to_client_npc_xml()
    assert "<npc_client>" in client_xml
    assert "<id>290001</id>" in client_xml
    assert "<name>Novo_NPC_Custom</name>" in client_xml
    assert "<desc>STR_NPC_NOVO_NPC_CUSTOM</desc>" in client_xml
    assert '<bound_radius front="1.200000" side="1.200000" upper="2.500000" />' in client_xml
    assert "<max_hp>" not in client_xml  # max_hp is in emulator template, not client_npcs
    print("  -> Client NPC XML snippet validated.")

    str_xml = meta.to_client_string_xml()
    assert "<string>" in str_xml
    assert "<id>799999</id>" in str_xml
    assert "<name>STR_NPC_NOVO_NPC_CUSTOM</name>" in str_xml
    assert "<body>Novo Guarda de Sanctum</body>" in str_xml
    print("  -> Client string XML snippet validated.")

    emu_dict = meta.to_emulator_dict()
    assert emu_dict["npc_id"] == 290001
    assert emu_dict["name_id"] == 799999
    assert emu_dict["max_hp"] == 45000
    assert emu_dict["level"] == 50
    print("  -> Emulator dict arguments validated.")


def test_client_exporter():
    print("\n[Step 2] Testing ClientNPCExporter transactional export & safety...")
    mock_client = Path(tempfile.mkdtemp(prefix="aion_mock_client_exp_"))
    try:
        # Create mock client folder structure
        npcs_dir = mock_client / "data" / "npcs"
        npcs_dir.mkdir(parents=True, exist_ok=True)
        strings_dir = mock_client / "data" / "Strings"
        strings_dir.mkdir(parents=True, exist_ok=True)

        # Create initial client_npcs.xml (UTF-16LE with BOM)
        initial_npcs_xml = (
            '<?xml version="1.0" encoding="utf-16" ?>\n'
            '<npc_clients generated_time="2026/01/01 12:00:00">\n'
            '  <npc_client>\n'
            '    <id>200000</id>\n'
            '    <name>ExistingNpc</name>\n'
            '    <desc>STR_NPC_EXISTING</desc>\n'
            '  </npc_client>\n'
            '</npc_clients>\n'
        )
        npcs_file = npcs_dir / "client_npcs.xml"
        npcs_file.write_bytes(b"\xff\xfe" + initial_npcs_xml.encode("utf-16le"))

        # Create initial client_strings_npc.xml (UTF-8)
        initial_strings_xml = (
            '<?xml version="1.0" encoding="utf-8" ?>\n'
            '<strings>\n'
            '  <string>\n'
            '    <id>350000</id>\n'
            '    <name>STR_NPC_EXISTING</name>\n'
            '    <body>NPC Existente</body>\n'
            '  </string>\n'
            '</strings>\n'
        )
        strings_file = strings_dir / "client_strings_npc.xml"
        strings_file.write_text(initial_strings_xml, encoding="utf-8")

        # Test pre-flight checks
        assert ClientNPCExporter.npc_id_exists(mock_client, 200000) is True
        assert ClientNPCExporter.npc_id_exists(mock_client, 999999) is False
        assert ClientNPCExporter.string_name_exists(mock_client, "STR_NPC_EXISTING") is True
        assert ClientNPCExporter.string_name_exists(mock_client, "STR_NPC_UNKNOWN") is False
        print("  -> Pre-flight existence checks verified.")

        meta = AionNPCMetadata(
            npc_id=290001,
            name="Test_Guard",
            desc="STR_NPC_TEST_GUARD",
            string_id=799999,
            string_body="Test Guard Display Name",
        )

        # 1. Test Read-Only Safe Mode (allow_client_write=False)
        safe_export_dir = Path(tempfile.mkdtemp(prefix="aion_safe_exp_"))
        try:
            res_safe = ClientNPCExporter.export_npc_to_client(
                client_root=mock_client,
                metadata=meta,
                allow_client_write=False,
                fallback_dir=safe_export_dir,
            )
            assert res_safe.success is True
            assert len(res_safe.written_files) == 2
            # Client files must remain untouched
            assert "290001" not in npcs_file.read_bytes().decode("utf-16le", errors="replace")
            print("  -> Safe mode verified: client files untouched, changes routed to export dir.")
        finally:
            shutil.rmtree(safe_export_dir, ignore_errors=True)

        # 2. Test Live Client Write Mode (allow_client_write=True)
        res_live = ClientNPCExporter.export_npc_to_client(
            client_root=mock_client,
            metadata=meta,
            allow_client_write=True,
        )
        assert res_live.success is True, f"Live export failed: {res_live.message}"
        assert len(res_live.backups) > 0, "No backups created during live write"

        # Verify client_npcs.xml was updated with preservation of BOM and existing NPC
        updated_npcs_bytes = npcs_file.read_bytes()
        assert updated_npcs_bytes.startswith(b"\xff\xfe"), "UTF-16LE BOM lost!"
        updated_npcs_text = updated_npcs_bytes[2:].decode("utf-16le")
        assert "<id>200000</id>" in updated_npcs_text, "Original NPC 200000 was lost!"
        assert "<id>290001</id>" in updated_npcs_text, "New NPC 290001 was not injected!"
        assert "</npc_clients>" in updated_npcs_text

        # Verify client_strings_npc.xml was updated
        updated_str_text = strings_file.read_text(encoding="utf-8")
        assert "STR_NPC_EXISTING" in updated_str_text, "Original string was lost!"
        assert "STR_NPC_TEST_GUARD" in updated_str_text, "New string was not injected!"
        assert "Test Guard Display Name" in updated_str_text
        print("  -> Live transactional write verified: both XML files updated cleanly with backups.")

    finally:
        shutil.rmtree(mock_client, ignore_errors=True)


def test_client_pak_exporter():
    print("\n[Step 2b] Testing ClientNPCExporter live PAK archive injection & .pak.bak creation...")
    import zipfile
    mock_client = Path(tempfile.mkdtemp(prefix="aion_mock_pak_client_"))
    try:
        npcs_dir = mock_client / "data" / "npcs"
        npcs_dir.mkdir(parents=True, exist_ok=True)
        npcs_pak_path = npcs_dir / "npcs.pak"

        initial_npcs_xml = (
            '<?xml version="1.0" encoding="utf-8" ?>\n'
            '<npc_clients generated_time="2026/01/01 12:00:00">\n'
            '  <npc_client>\n'
            '    <id>200000</id>\n'
            '    <name>ExistingPakNpc</name>\n'
            '    <desc>STR_NPC_EXISTING_PAK</desc>\n'
            '  </npc_client>\n'
            '</npc_clients>\n'
        )

        # Build initial npcs.pak
        with zipfile.ZipFile(str(npcs_pak_path), "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("client_npcs.xml", initial_npcs_xml.encode("utf-8"))

        assert npcs_pak_path.is_file()
        assert ClientNPCExporter.npc_id_exists(mock_client, 200000) is True
        assert ClientNPCExporter.npc_id_exists(mock_client, 290002) is False

        meta = AionNPCMetadata(
            npc_id=290002,
            name="Pak_Guard",
            desc="STR_NPC_PAK_GUARD",
            string_id=799998,
            string_body="Pak Guard Display Name",
        )

        res_pak = ClientNPCExporter.export_npc_to_client(
            client_root=mock_client,
            metadata=meta,
            allow_client_write=True,
        )
        assert res_pak.success is True, f"PAK export failed: {res_pak.message}"

        # Verify .pak.bak backup exists
        pak_bak = npcs_pak_path.with_suffix(".pak.bak")
        assert pak_bak.is_file(), f"Expected backup {pak_bak} was not created!"

        # Read updated npcs.pak via AionPakArchive
        arc = mod.core.pak_engine.AionPakArchive(npcs_pak_path)
        updated_data = arc.read_file("client_npcs.xml")
        assert updated_data is not None, "client_npcs.xml missing from updated npcs.pak!"
        updated_text = updated_data.decode("utf-8", errors="replace")
        assert "<id>200000</id>" in updated_text, "Original NPC lost from PAK!"
        assert "<id>290002</id>" in updated_text, "New NPC not injected into PAK!"
        print("  -> Live PAK archive update verified: npcs.pak updated, .pak.bak created, entries intact.")

    finally:
        shutil.rmtree(mock_client, ignore_errors=True)



def test_emulator_exporter():
    print("\n[Step 3] Testing EmulatorExporter XML generation & schema validation...")
    temp_emu_dir = Path(tempfile.mkdtemp(prefix="aion_mock_emu_"))
    try:
        emu_xml_path = temp_emu_dir / "npc_templates.xml"
        initial_emu_xml = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<npc_templates xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n'
            '    <npc_template npc_id="200000" level="1" name="Existing Dummy" name_id="350000" height="1.0" rank="NOVICE" rating="NORMAL" tribe="GENERAL" type="GENERAL" ai="general" srange="10" sangle="240" attack_speed="2000" hpgauge="3">\n'
            '        <stats maxHp="1000">\n'
            '            <speeds walk="1.5" group_walk="1.5" run="6.0" run_fight="6.0" group_run_fight="6.0"/>\n'
            '        </stats>\n'
            '        <bound_radius front="0.5" side="0.5" upper="2.0"/>\n'
            '    </npc_template>\n'
            '</npc_templates>\n'
        )
        emu_xml_path.write_text(initial_emu_xml, encoding="utf-8")

        exp = EmulatorExporter(emulator_npc_templates_path=emu_xml_path)
        assert exp.npc_id_exists(200000) is True
        assert exp.npc_id_exists(290001) is False
        assert exp.get_max_npc_id(emu_xml_path) == 200000

        # Export new NPC
        ok = exp.export_npc(
            npc_id=290001,
            name="Sanctum Elite Guard",
            name_id=799999,
            level=55,
            height=1.0,
            max_hp=50000,
            race="PC_LIGHT",
            tribe="GUARD",
            npc_type="GUARD",
            ai="general",
            srange=15,
            walk_speed=1.5,
            run_speed=6.0,
            bound_front=0.6,
            bound_side=0.6,
            bound_upper=2.2,
        )
        assert ok is True
        assert exp.npc_id_exists(290001) is True
        assert exp.get_max_npc_id(emu_xml_path) == 290001

        # Check backup created
        bak_file = emu_xml_path.with_suffix(".xml.bak")
        assert bak_file.is_file(), "npc_templates.xml.bak was not created!"

        # Parse written XML
        tree = ET.parse(str(emu_xml_path))
        root = tree.getroot()
        templates = root.findall("npc_template")
        assert len(templates) == 2, f"Expected 2 templates, found {len(templates)}"

        new_t = [t for t in templates if int(t.get("npc_id", 0)) == 290001][0]
        assert new_t.get("name") == "Sanctum Elite Guard"
        assert new_t.get("level") == "55"
        assert new_t.get("tribe") == "GUARD"
        assert new_t.get("race") == "PC_LIGHT"

        stats = new_t.find("stats")
        assert stats is not None
        assert stats.get("maxHp") == "50000"

        speeds = stats.find("speeds")
        assert speeds is not None
        assert speeds.get("run") == "6.0"

        bound = new_t.find("bound_radius")
        assert bound is not None
        assert bound.get("upper") == "2.2"

        print("  -> EmulatorExporter verified: valid XML, sub-elements (stats, speeds, bound_radius) and backup.")

    finally:
        shutil.rmtree(temp_emu_dir, ignore_errors=True)


def test_lineup_and_stage():
    print("\n[Step 4] Testing Multi-model Lineup placement & Remove Model operator...")
    stage_col = ViewerStage.get_or_create_stage_collection()
    ViewerStage.clear_stage_objects()

    # Create model 1
    arm1 = bpy.data.armatures.new("Rig1_Data")
    obj1 = bpy.data.objects.new("Rig1", arm1)
    stage_col.objects.link(obj1)
    apply_lineup_offset(obj1, mode="LINEUP")

    assert obj1.location.x == 0.0, f"Expected first model at X=0.0, got {obj1.location.x}"
    print(f"  -> Model 1 placed at X={obj1.location.x:.3f}m (exact world origin).")

    # Create model 2
    arm2 = bpy.data.armatures.new("Rig2_Data")
    obj2 = bpy.data.objects.new("Rig2", arm2)
    stage_col.objects.link(obj2)
    apply_lineup_offset(obj2, mode="LINEUP")

    assert obj2.location.x > obj1.location.x, f"Expected Model 2 to the right of Model 1, got {obj2.location.x}"
    print(f"  -> Model 2 placed at X={obj2.location.x:.3f}m (> 0.0 with safe margin).")

    # Test removing active model operator
    bpy.context.view_layer.objects.active = obj2
    bpy.ops.aion_model.remove_active_model()
    remaining = [o for o in stage_col.objects if o.type == "ARMATURE"]
    assert len(remaining) == 1, f"Expected 1 remaining armature, got {len(remaining)}"
    assert remaining[0] == obj1, "Wrong model was removed"
    print("  -> aion_model.remove_active_model successfully removed selected model from lineup.")

    # Cleanup
    ViewerStage.clear_stage_objects()


if __name__ == "__main__":
    print("=" * 80)
    print("AUTOMATED VERIFICATION: NPC CREATOR, CLIENT EXPORT & LINEUP")
    print("=" * 80)
    test_npc_metadata()
    test_client_exporter()
    test_client_pak_exporter()
    test_emulator_exporter()
    test_lineup_and_stage()
    print("\n" + "=" * 80)
    print("ALL NPC CREATOR & EXPORT TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)

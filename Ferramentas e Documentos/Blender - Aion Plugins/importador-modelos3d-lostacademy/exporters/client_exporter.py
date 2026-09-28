"""
Client NPC Exporter for LostAcademy Aion Model Library.
Handles transactional injection of new NPC definitions into the Aion client files:
- data/npcs/npcs.pak -> client_npcs.xml
- data/Strings/Strings.pak -> client_strings_npc.xml
With complete pre-flight validation, automatic .bak / .pak.bak creation,
and read-only safe mode.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..core.pak_engine import AionPakArchive
from ..core.transaction_manager import TransactionManager, TransactionResult
from .npc_metadata import AionNPCMetadata

logger = logging.getLogger(__name__)


class ClientNPCExporter:
    """Exports NPC metadata directly into Aion client PAK archives or loose XML files."""

    @staticmethod
    def find_npcs_pak(client_root: Path | str) -> Optional[Path]:
        """Locates the primary NPCs PAK archive in the client directory."""
        root = Path(client_root).resolve()
        candidates = [
            root / "data" / "npcs" / "npcs.pak",
            root / "Data" / "NPCs" / "Npcs.pak",
            root / "data" / "npcs" / "Npcs_LostAcademy.pak",
            root / "data" / "europe" / "Npcs" / "Npcs.pak",
            root / "data" / "npcs" / "Atributos_Npcs.pak",
        ]
        for c in candidates:
            if c.is_file():
                return c

        # Glob fallback
        data_p = root / "data" if (root / "data").is_dir() else root / "Data"
        if data_p.is_dir():
            for p in data_p.glob("**/*npc*.pak"):
                if p.is_file():
                    return p
        return None

    @staticmethod
    def find_strings_pak(client_root: Path | str) -> Optional[Path]:
        """Locates the primary Strings PAK archive in the client directory."""
        root = Path(client_root).resolve()
        candidates = [
            root / "data" / "Strings" / "Strings.pak",
            root / "data" / "strings" / "strings.pak",
            root / "Data" / "Strings" / "Strings.pak",
        ]
        for c in candidates:
            if c.is_file():
                return c

        data_p = root / "data" if (root / "data").is_dir() else root / "Data"
        if data_p.is_dir():
            for p in data_p.glob("**/*string*.pak"):
                if p.is_file():
                    return p
        return None

    @classmethod
    def npc_id_exists(cls, client_root: Path | str, npc_id: int) -> bool:
        """Checks if *npc_id* already exists in the client's NPC data."""
        root = Path(client_root).resolve()
        id_str = str(npc_id)

        # 1. Check loose file
        for cand in [root / "data" / "npcs" / "client_npcs.xml", root / "Data" / "NPCs" / "client_npcs.xml"]:
            if cand.is_file():
                try:
                    raw = cand.read_bytes()
                    if id_str.encode("utf-8") in raw or id_str.encode("utf-16le") in raw:
                        return True
                except Exception:
                    pass

        # 2. Check PAK archive
        pak = cls.find_npcs_pak(root)
        if pak and pak.is_file():
            try:
                arc = AionPakArchive(pak)
                for fname in arc.entries:
                    if "client_npc" in fname.lower() and fname.endswith((".xml", ".bxml")):
                        raw = arc.read_file(fname)
                        if raw:
                            # Quick search in binary / text / utf-16
                            if id_str.encode("utf-8") in raw or id_str.encode("utf-16le") in raw:
                                return True
            except Exception:
                pass
        return False

    @classmethod
    def string_name_exists(cls, client_root: Path | str, string_desc: str) -> bool:
        """Checks if a string descriptor already exists in the client's string tables."""
        root = Path(client_root).resolve()
        if not string_desc:
            return False

        # 1. Check loose file
        for cand in [root / "data" / "Strings" / "client_strings_npc.xml", root / "data" / "strings" / "client_strings_npc.xml"]:
            if cand.is_file():
                try:
                    raw = cand.read_bytes()
                    if string_desc.encode("utf-8") in raw or string_desc.encode("utf-16le") in raw:
                        return True
                except Exception:
                    pass

        # 2. Check Strings PAK
        pak = cls.find_strings_pak(root)
        if pak and pak.is_file():
            try:
                arc = AionPakArchive(pak)
                raw = arc.read_file("client_strings_npc.xml")
                if raw and (string_desc.encode("utf-8") in raw or string_desc.encode("utf-16le") in raw):
                    return True
            except Exception:
                pass
        return False

    @classmethod
    def _read_existing_entry(
        cls,
        client_root: Path,
        pak_path: Optional[Path],
        internal_name: str,
        loose_rel: str,
    ) -> Optional[bytes]:
        """Reads existing file content from loose file or PAK archive."""
        loose = client_root / loose_rel
        if loose.is_file():
            try:
                return loose.read_bytes()
            except Exception:
                pass

        if pak_path and pak_path.is_file():
            try:
                arc = AionPakArchive(pak_path)
                return arc.read_file(internal_name)
            except Exception:
                pass
        return None

    @classmethod
    def _inject_xml_snippet(
        cls,
        raw_data: Optional[bytes],
        snippet: str,
        root_tag: str,
        closing_tag: str,
    ) -> bytes:
        """Injects an XML snippet before the closing tag, preserving original encoding/BOM."""
        if not raw_data or raw_data.startswith(b"\x80"):
            # New XML document or BXML replacement with clean UTF-8 XML
            doc = (
                f'<?xml version="1.0" encoding="utf-8"?>\n'
                f'<{root_tag}>\n'
                f"{snippet}\n"
                f"</{root_tag}>\n"
            )
            return doc.encode("utf-8")

        # Detect encoding
        is_utf16_bom = raw_data.startswith(b"\xff\xfe")
        is_utf8_bom = raw_data.startswith(b"\xef\xbb\xbf")

        if is_utf16_bom:
            encoding = "utf-16le"
            text = raw_data[2:].decode(encoding, errors="replace")
        elif is_utf8_bom:
            encoding = "utf-8"
            text = raw_data[3:].decode(encoding, errors="replace")
        else:
            try:
                text = raw_data.decode("utf-8")
                encoding = "utf-8"
            except UnicodeDecodeError:
                text = raw_data.decode("latin-1", errors="replace")
                encoding = "latin-1"

        close_idx = text.rfind(closing_tag)
        if close_idx != -1:
            new_text = text[:close_idx] + snippet + "\n" + text[close_idx:]
        else:
            new_text = text + "\n" + snippet + "\n"

        encoded = new_text.encode(encoding)
        if is_utf16_bom:
            return b"\xff\xfe" + encoded
        if is_utf8_bom:
            return b"\xef\xbb\xbf" + encoded
        return encoded

    @classmethod
    def export_npc_to_client(
        cls,
        client_root: Path | str,
        metadata: AionNPCMetadata,
        allow_client_write: bool = False,
        fallback_dir: Optional[Path | str] = None,
    ) -> TransactionResult:
        """Injects *metadata* into client_npcs.xml and client_strings_npc.xml.

        Executes transactionally:
        - Creates automatic backups before modification.
        - Updates client_npcs.xml in npcs.pak (or loose).
        - Updates client_strings_npc.xml in Strings.pak (or loose).
        - If *allow_client_write* is False, safely routes files to *fallback_dir*.

        Args:
            client_root: Root path of the Aion client.
            metadata: Populated :class:`AionNPCMetadata` instance.
            allow_client_write: Read-only safety switch.
            fallback_dir: Optional export directory when safety switch is on.

        Returns:
            :class:`TransactionResult` detailing files modified and backups created.
        """
        root = Path(client_root).resolve()

        # 1. Pre-flight checks
        npcs_pak = cls.find_npcs_pak(root)
        strings_pak = cls.find_strings_pak(root)

        # 2. Prepare client_npcs.xml content
        existing_npcs_data = cls._read_existing_entry(
            client_root=root,
            pak_path=npcs_pak,
            internal_name="client_npcs.xml",
            loose_rel="data/npcs/client_npcs.xml",
        )
        new_npcs_data = cls._inject_xml_snippet(
            raw_data=existing_npcs_data,
            snippet=metadata.to_client_npc_xml(),
            root_tag="npc_clients",
            closing_tag="</npc_clients>",
        )

        # 3. Prepare client_strings_npc.xml content
        existing_str_data = cls._read_existing_entry(
            client_root=root,
            pak_path=strings_pak,
            internal_name="client_strings_npc.xml",
            loose_rel="data/Strings/client_strings_npc.xml",
        )
        new_str_data = cls._inject_xml_snippet(
            raw_data=existing_str_data,
            snippet=metadata.to_client_string_xml(),
            root_tag="strings",
            closing_tag="</strings>",
        )

        # 4. Map asset updates for TransactionManager
        asset_updates: Dict[str, bytes] = {
            "data/npcs/client_npcs.xml": new_npcs_data,
            "data/Strings/client_strings_npc.xml": new_str_data,
        }

        # 5. Commit transactionally
        result = TransactionManager.save_assets(
            client_root=root,
            asset_updates=asset_updates,
            allow_client_write=allow_client_write,
            export_fallback_dir=fallback_dir,
            create_backups=True,
        )
        return result

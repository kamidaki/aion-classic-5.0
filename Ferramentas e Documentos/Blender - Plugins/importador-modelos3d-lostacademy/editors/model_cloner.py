"""
Model Cloner & Asset Duplicator for LostAcademy Aion Model Library.
Duplicates existing models, skeletons, and animation sets to create new standalone client assets.
"""

from __future__ import annotations
import copy
import time
from pathlib import Path
from typing import Optional, Tuple

from ..core.client_provider import AionClientProvider
from ..core.transaction_manager import TransactionManager, TransactionResult
from ..indexer.asset_entry import AssetEntry
from ..indexer.asset_database import AssetDatabase


class ModelCloner:
    """Clones existing Aion assets into new independently editable assets."""

    @staticmethod
    def clone_asset(
        source_entry: AssetEntry,
        new_name: str,
        client_provider: AionClientProvider,
        target_relative_path: Optional[str] = None,
        allow_client_write: bool = False,
    ) -> Tuple[Optional[AssetEntry], TransactionResult]:
        """
        Duplicates source_entry and its model data, creating a new standalone AssetEntry.
        """
        if not source_entry:
            return None, TransactionResult(False, "No source asset specified to clone.")

        # Read original CGF
        cgf_bytes = client_provider.resolve_cgf_bytes(source_entry.model_path)
        if not cgf_bytes:
            return None, TransactionResult(False, f"Could not read source model bytes for {source_entry.model_path}")

        clean_name = new_name.strip() or f"{source_entry.name}_Copy"
        clean_slug = clean_name.lower().replace(" ", "_")

        if not target_relative_path:
            orig_parent = Path(source_entry.model_path).parent.as_posix()
            target_relative_path = f"{orig_parent}/{clean_slug}.cgf"

        updates = {
            target_relative_path: cgf_bytes,
        }

        # Clone matching CAL if present
        cal_bytes = None
        new_cal_rel = None
        if source_entry.cal_path:
            cal_data = client_provider.catalog.extract_file(source_entry.cal_path)
            if cal_data:
                orig_cal_p = Path(source_entry.cal_path)
                new_cal_rel = f"{orig_cal_p.parent.as_posix()}/{clean_slug}.cal"
                updates[new_cal_rel] = cal_data

        # Execute transaction
        tx_res = TransactionManager.save_assets(
            client_root=client_provider.root,
            asset_updates=updates,
            allow_client_write=allow_client_write,
        )

        # Create cloned AssetEntry
        new_id = f"clone_{int(time.time())}"
        cloned_entry = copy.deepcopy(source_entry)
        cloned_entry.asset_id = new_id
        cloned_entry.name = clean_name
        cloned_entry.model_path = target_relative_path
        cloned_entry.cal_path = new_cal_rel
        cloned_entry.is_loose = True

        AssetDatabase.get().add_entry(cloned_entry)

        return cloned_entry, tx_res

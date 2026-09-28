"""
Direct Saver for Aion Models.
Handles the transactional write process from the 3D scene back to the active Aion client.
"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import bpy
from ..core.transaction_manager import TransactionManager, TransactionResult
from ..providers.export_provider import ExportProvider
from ..providers.model_provider import ModelProvider

logger = logging.getLogger(__name__)


class DirectSaver:
    """Orchestrates saving the currently edited model back to client files or PAKs."""

    @staticmethod
    def save_model(
        root_obj: bpy.types.Object,
        entry: Any,
        model_provider: ModelProvider,
        client_root: Path,
        allow_client_write: bool = False,
        fallback_dir: Optional[Path] = None,
    ) -> TransactionResult:
        """
        Executes a transactional save for the given model object.
        """
        if not root_obj:
            return TransactionResult(
                success=False,
                error_message="No active model object to save.",
            )

        export_prov = ExportProvider(model_provider=model_provider, client_root=client_root)
        result = export_prov.save_current_asset(
            root_obj=root_obj,
            entry=entry,
            allow_client_write=allow_client_write,
            export_fallback_dir=fallback_dir,
        )
        return result

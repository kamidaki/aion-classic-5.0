"""
Core engine package for LostAcademy Aion Model Library.
"""

from .pak_engine import (
    AionPakArchive,
    AionCatalogIndex,
    AionPakEntry,
    deobfuscate_stream,
    update_pak_archive,
    get_pak_resolver,
)
from .client_detector import (
    ClientInfo,
    discover_available_clients,
    inspect_client,
    detect_client_flavor,
)
from .client_provider import AionClientProvider, ClientFlavor
from .change_tracker import ChangeTracker, TrackedAsset
from .transaction_manager import TransactionManager, TransactionResult

__all__ = [
    "AionPakArchive",
    "AionCatalogIndex",
    "AionPakEntry",
    "deobfuscate_stream",
    "update_pak_archive",
    "get_pak_resolver",
    "ClientInfo",
    "discover_available_clients",
    "inspect_client",
    "detect_client_flavor",
    "AionClientProvider",
    "ClientFlavor",
    "ChangeTracker",
    "TrackedAsset",
    "TransactionManager",
    "TransactionResult",
]

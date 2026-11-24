import ctypes
from ctypes import wintypes
import os
import sys

dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Release64", "Game.dll")

if not os.path.exists(dll_path):
    print(f"[ERRO] Binario nao encontrado: {dll_path}")
    sys.exit(1)

print(f"=======================================================")
print(f"[INFO] Testando Carregamento Dinamico do Game.dll Classic 5.0")
print(f"[INFO] Caminho: {dll_path}")
print(f"=======================================================")

try:
    game_dll = ctypes.WinDLL(dll_path)
    print(f"[SUCESSO] DLL carregada na memoria via WinDLL.")
except Exception as e:
    print(f"[FALHA] Erro ao carregar DLL: {e}")
    sys.exit(1)

# Estrutura CryModuleMemoryInfo
class CryModuleMemoryInfo(ctypes.Structure):
    _fields_ = [
        ("AllocatedMemory", ctypes.c_uint64),
        ("StringAllocation", ctypes.c_uint64),
        ("CryStringAllocation", ctypes.c_uint64)
    ]

# 1. Testar CryModuleGetMemoryInfo (Ordinal 2)
try:
    CryModuleGetMemoryInfo = getattr(game_dll, "CryModuleGetMemoryInfo")
    CryModuleGetMemoryInfo.argtypes = [ctypes.POINTER(CryModuleMemoryInfo)]
    CryModuleGetMemoryInfo.restype = None

    mem_info = CryModuleMemoryInfo()
    CryModuleGetMemoryInfo(ctypes.byref(mem_info))
    print(f"[SUCESSO] CryModuleGetMemoryInfo executado com sucesso:")
    print(f"  - AllocatedMemory: {mem_info.AllocatedMemory} bytes")
    print(f"  - StringAllocation: {mem_info.StringAllocation} bytes")
    print(f"  - CryStringAllocation: {mem_info.CryStringAllocation} bytes")
except Exception as e:
    print(f"[FALHA] Erro ao chamar CryModuleGetMemoryInfo: {e}")
    sys.exit(1)

# 2. Testar CreateGameInstance (Ordinal 1)
try:
    CreateGameInstance = getattr(game_dll, "CreateGameInstance")
    CreateGameInstance.argtypes = [ctypes.c_void_p]
    CreateGameInstance.restype = ctypes.c_void_p

    pGame = CreateGameInstance(None)
    print(f"[SUCESSO] CreateGameInstance executado com sucesso:")
    print(f"  - Ponteiro IGame retornado: 0x{pGame:016X}" if pGame else "  - Ponteiro nulo retornado")
    if not pGame:
        print(f"[FALHA] Ponteiro retornado de CreateGameInstance eh nulo!")
        sys.exit(1)
except Exception as e:
    print(f"[FALHA] Erro ao chamar CreateGameInstance: {e}")
    sys.exit(1)

print(f"=======================================================")
print(f"[CONCLUSAO] Todos os testes de carregamento dinamico e exportacoes passaram com 100% de exito!")
print(f"=======================================================")
sys.exit(0)

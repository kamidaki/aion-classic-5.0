import ctypes
from ctypes import wintypes
import struct

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010

kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi

pid = 11076
hProcess = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)

class MODULEINFO(ctypes.Structure):
    _fields_ = [
        ("lpBaseOfDll", ctypes.c_void_p),
        ("SizeOfImage", wintypes.DWORD),
        ("EntryPoint", ctypes.c_void_p),
    ]

psapi.EnumProcessModules.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_void_p), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
psapi.EnumProcessModules.restype = wintypes.BOOL

psapi.GetModuleBaseNameW.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.LPWSTR, wintypes.DWORD]
psapi.GetModuleBaseNameW.restype = wintypes.DWORD

psapi.GetModuleInformation.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.POINTER(MODULEINFO), wintypes.DWORD]
psapi.GetModuleInformation.restype = wintypes.BOOL

hMods = (ctypes.c_void_p * 1024)()
cbNeeded = wintypes.DWORD()

if psapi.EnumProcessModules(hProcess, hMods, ctypes.sizeof(hMods), ctypes.byref(cbNeeded)):
    count = cbNeeded.value // ctypes.sizeof(ctypes.c_void_p)
    print(f"Total modules loaded: {count}")
    for i in range(count):
        hMod = hMods[i]
        modName = ctypes.create_unicode_buffer(512)
        psapi.GetModuleBaseNameW(hProcess, hMod, modName, 512)
        mi = MODULEINFO()
        psapi.GetModuleInformation(hProcess, hMod, ctypes.byref(mi), ctypes.sizeof(mi))
        name = modName.value
        if any(k in name.lower() for k in ["game", "cry", "aion", "system", "client"]):
            print(f"  {name:30s} Base: 0x{mi.lpBaseOfDll:016X} Size: 0x{mi.SizeOfImage:08X}")

kernel32.CloseHandle(hProcess)

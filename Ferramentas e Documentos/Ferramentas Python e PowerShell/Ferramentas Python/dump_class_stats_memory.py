import ctypes
from ctypes import wintypes
import struct
import re

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
kernel32 = ctypes.windll.kernel32

pid = 11076
hProcess = kernel32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)

buffer_size = 1024 * 1024
read_buf = ctypes.create_string_buffer(buffer_size)
bytes_read = ctypes.c_size_t()

def read_mem(addr, size):
    buf = ctypes.create_string_buffer(size)
    n = ctypes.c_size_t()
    if kernel32.ReadProcessMemory(hProcess, ctypes.c_void_p(addr), buf, size, ctypes.byref(n)):
        return buf.raw[:n.value]
    return None

# Let's search for occurrences of class names in memory
classes = [b"warrior", b"gladiator", b"templar", b"scout", b"assassin", b"ranger", b"mage", b"sorcerer", b"elementallist", b"priest", b"cleric", b"chanter", b"monk", b"thunderer", b"brawler", b"luminess", b"phoenix", b"reaper", b"soul_reaper"]

# Scan memory for class structs
class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD),
        ("PartitionId", wintypes.WORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
    ]

mbi = MEMORY_BASIC_INFORMATION()
addr = 0
found_tables = []

while kernel32.VirtualQueryEx(hProcess, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
    if mbi.State == 0x1000 and (mbi.Protect & 0xFF) in (0x04, 0x02, 0x20, 0x40):
        curr = mbi.BaseAddress
        end = curr + mbi.RegionSize
        while curr < end:
            chunk = min(buffer_size, end - curr)
            if kernel32.ReadProcessMemory(hProcess, ctypes.c_void_p(curr), read_buf, chunk, ctypes.byref(bytes_read)):
                data = read_buf.raw[:bytes_read.value]
                # Look for "reaper" or "soul_reaper" in wide char (UTF-16LE) or ASCII
                for c in [b"r\x00e\x00a\x00p\x00e\x00r\x00", b"s\x00o\x00u\x00l\x00_\x00r\x00e\x00a\x00p\x00e\x00r\x00"]:
                    if c in data:
                        idx = data.find(c)
                        found_tables.append((curr + idx, data[max(0, idx-64):min(len(data), idx+256)]))
            curr += chunk
    addr += mbi.RegionSize
    if addr >= 0x7FFFFFFF0000:
        break

print(f"Found {len(found_tables)} reaper hits in memory:")
for hit_addr, raw in found_tables[:10]:
    print(f"\nHit at 0x{hit_addr:X}:")
    print("Hex:", raw.hex())
    # Try decoding utf-16
    try:
        print("UTF-16:", raw.decode('utf-16le', errors='ignore'))
    except:
        pass

kernel32.CloseHandle(hProcess)

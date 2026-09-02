import ctypes
from ctypes import wintypes
import struct
import re

PROCESS_VM_READ = 0x0010
kernel32 = ctypes.windll.kernel32

pid = 11076
hProcess = kernel32.OpenProcess(PROCESS_VM_READ, False, pid)

buffer_size = 2 * 1024 * 1024
read_buf = ctypes.create_string_buffer(buffer_size)
bytes_read = ctypes.c_size_t()

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
found_maps = []

target_maps = [110030000, 110040000, 210070000, 220070000, 210010000, 220010000, 110010000, 120010000]

print("Scanning for map IDs in memory...")

while kernel32.VirtualQueryEx(hProcess, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
    if mbi.State == 0x1000 and (mbi.Protect & 0xFF) in (0x04, 0x02, 0x20, 0x40):
        curr = mbi.BaseAddress
        end = curr + mbi.RegionSize
        while curr < end:
            chunk = min(buffer_size, end - curr)
            if kernel32.ReadProcessMemory(hProcess, ctypes.c_void_p(curr), read_buf, chunk, ctypes.byref(bytes_read)):
                data = read_buf.raw[:bytes_read.value]
                for mid in target_maps:
                    mid_b = struct.pack("<I", mid)
                    if mid_b in data:
                        idx = data.find(mid_b)
                        hit_addr = curr + idx
                        # extract surrounding text / strings
                        ctx = data[max(0, idx-64) : min(len(data), idx+256)]
                        found_maps.append((mid, hit_addr, ctx))
            curr += chunk
    addr += mbi.RegionSize
    if addr >= 0x7FFFFFFF0000:
        break

print(f"Total map matches: {len(found_maps)}")
for mid, hit_addr, ctx in found_maps[:15]:
    print(f"\n--- Map ID {mid} at 0x{hit_addr:X} ---")
    print("Hex:", ctx[:64].hex())
    # print strings
    ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in ctx[:128])
    print("ASCII:", ascii_str)

kernel32.CloseHandle(hProcess)

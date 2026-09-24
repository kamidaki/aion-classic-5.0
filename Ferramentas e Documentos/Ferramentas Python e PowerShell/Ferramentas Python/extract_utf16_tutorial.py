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
found = []

terms = [
    b"i\x00d\x00t\x00u\x00t\x00o\x00r\x00i\x00a\x00l\x00",
    b"J\x00u\x00c\x00l\x00e\x00a\x00s\x00",
    b"M\x00o\x00m\x00e\x00n\x00t\x00 \x00o\x00f\x00",
    b"j\x00u\x00c\x00l\x00e\x00a\x00s\x00",
    b"1\x001\x000\x000\x003\x000\x000\x000\x000\x00",
    b"1\x001\x000\x000\x004\x000\x000\x000\x000\x00",
    b"2\x002\x000\x000\x007\x000\x000\x000\x000\x00"
]

print("Scanning memory for UTF-16 terms...")

while kernel32.VirtualQueryEx(hProcess, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
    if mbi.State == 0x1000 and (mbi.Protect & 0xFF) in (0x04, 0x02, 0x20, 0x40):
        curr = mbi.BaseAddress
        end = curr + mbi.RegionSize
        while curr < end:
            chunk = min(buffer_size, end - curr)
            if kernel32.ReadProcessMemory(hProcess, ctypes.c_void_p(curr), read_buf, chunk, ctypes.byref(bytes_read)):
                data = read_buf.raw[:bytes_read.value]
                for t in terms:
                    if t in data:
                        idx = data.find(t)
                        hit_addr = curr + idx
                        ctx = data[max(0, idx-100) : min(len(data), idx+1500)]
                        found.append((t, hit_addr, ctx))
            curr += chunk
    addr += mbi.RegionSize
    if addr >= 0x7FFFFFFF0000:
        break

print(f"Total hits found: {len(found)}")
for t, hit_addr, ctx in found[:10]:
    print(f"\n================ Hit at 0x{hit_addr:X} ================")
    try:
        print(ctx.decode('utf-16le', errors='replace')[:500])
    except:
        print(ctx[:200].hex())

kernel32.CloseHandle(hProcess)

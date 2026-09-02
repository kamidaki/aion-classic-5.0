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

terms = [b"idtutorialq", b"IDTutorialQ", b"IDTUTORIALQ", b"WorldId", b"Moment of Light and shadow", b"Q1000", b"q1000", b"Jucleas"]

print("Scanning for tutorial XML and quest data in memory...")

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
for t, hit_addr, ctx in found:
    print(f"\n================ Hit for {t} at 0x{hit_addr:X} ================")
    try:
        print(ctx.decode('utf-8', errors='replace'))
    except:
        print(ctx[:200].hex())

kernel32.CloseHandle(hProcess)

import ctypes
from ctypes import wintypes
import struct

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
kernel32 = ctypes.windll.kernel32

pid = 11076
hProcess = kernel32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)

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
found_tables = []

print("Scanning for experience table in memory...")

# We know level 1 exp = 0, level 2 exp in Aion Classic is around 400 ~ 650
# Let's search for sequences of 64-bit uints or 32-bit uints starting with 0, >0, etc.

while kernel32.VirtualQueryEx(hProcess, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
    if mbi.State == 0x1000 and (mbi.Protect & 0xFF) in (0x04, 0x02, 0x20, 0x40):
        curr = mbi.BaseAddress
        end = curr + mbi.RegionSize
        while curr < end:
            chunk = min(buffer_size, end - curr)
            if kernel32.ReadProcessMemory(hProcess, ctypes.c_void_p(curr), read_buf, chunk, ctypes.byref(bytes_read)):
                data = read_buf.raw[:bytes_read.value]
                
                # Check for "pcexp" XML content or table
                if b"<exp>" in data or b"<pcexps>" in data or b"pcexp_table" in data:
                    idx = data.find(b"pcexp_table")
                    if idx != -1:
                        found_tables.append((curr + idx, data[max(0, idx-100) : min(len(data), idx+1000)]))
            curr += chunk
    addr += mbi.RegionSize
    if addr >= 0x7FFFFFFF0000:
        break

print(f"Found {len(found_tables)} hits for pcexp_table:")
for hit_addr, d in found_tables:
    print(f"\n0x{hit_addr:X}:")
    try:
        print(d.decode('utf-8', errors='replace')[:300])
    except:
        print(d[:100].hex())

kernel32.CloseHandle(hProcess)

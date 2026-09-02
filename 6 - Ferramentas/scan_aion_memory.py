import ctypes
from ctypes import wintypes
import struct
import re

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400

kernel32 = ctypes.windll.kernel32

pid = 11076
hProcess = kernel32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
if not hProcess:
    print(f"Failed to open process {pid}: error {ctypes.GetLastError()}")
    exit(1)

print(f"Successfully opened Aion.bin PID {pid}!")

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
MEM_COMMIT = 0x1000
PAGE_READWRITE = 0x04
PAGE_READONLY = 0x02
PAGE_EXECUTE_READ = 0x20
PAGE_EXECUTE_READWRITE = 0x40

valid_protects = (PAGE_READWRITE, PAGE_READONLY, PAGE_EXECUTE_READ, PAGE_EXECUTE_READWRITE)

addr = 0
found_xmls = []
target_terms = [b"pcexp_table", b"client_stat_info", b"client_character_class_info", b"player_initial_data", b"<pcexp_table", b"<stat_info", b"Moment of Light and shadow"]

print("Scanning memory regions...")
buffer_size = 1024 * 1024
read_buf = ctypes.create_string_buffer(buffer_size)
bytes_read = ctypes.c_size_t()

matching_regions = []

while kernel32.VirtualQueryEx(hProcess, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
    if mbi.State == MEM_COMMIT and (mbi.Protect & 0xFF) in valid_protects:
        region_addr = mbi.BaseAddress
        region_size = mbi.RegionSize
        # read in chunks
        curr = region_addr
        end = region_addr + region_size
        while curr < end:
            chunk = min(buffer_size, end - curr)
            if kernel32.ReadProcessMemory(hProcess, ctypes.c_void_p(curr), read_buf, chunk, ctypes.byref(bytes_read)):
                data = read_buf.raw[:bytes_read.value]
                for term in target_terms:
                    if term in data:
                        idx = data.find(term)
                        hit_addr = curr + idx
                        print(f"[FOUND] '{term.decode()}' at 0x{hit_addr:X} in region 0x{region_addr:X} (size {region_size})")
                        matching_regions.append((hit_addr, term, data[max(0, idx-100) : min(len(data), idx+1500)]))
            curr += chunk
    addr += mbi.RegionSize
    if addr >= 0x7FFFFFFF0000: # user mode limit
        break

print(f"\nTotal hits found: {len(matching_regions)}")
for hit_addr, term, snippet in matching_regions:
    print(f"\n--- Hit for {term} at 0x{hit_addr:X} ---")
    try:
        print(snippet.decode('utf-8', errors='replace')[:500])
    except Exception as e:
        print(snippet[:200].hex())

kernel32.CloseHandle(hProcess)

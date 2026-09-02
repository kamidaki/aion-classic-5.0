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
found_hits = []

# Pattern: 334 (0x014E) followed soon by 375 (0x0177)
# Could be uint32 (4e 01 00 00 ... 77 01 00 00) or uint16 (4e 01 ... 77 01)
p_u32 = b"\x4e\x01\x00\x00"
p_u16 = b"\x4e\x01"

print("Searching for HP=334 and MP=375 in memory...")

while kernel32.VirtualQueryEx(hProcess, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
    if mbi.State == 0x1000 and (mbi.Protect & 0xFF) in (0x04, 0x02, 0x20, 0x40):
        curr = mbi.BaseAddress
        end = curr + mbi.RegionSize
        while curr < end:
            chunk = min(buffer_size, end - curr)
            if kernel32.ReadProcessMemory(hProcess, ctypes.c_void_p(curr), read_buf, chunk, ctypes.byref(bytes_read)):
                data = read_buf.raw[:bytes_read.value]
                
                # find all occurrences of p_u32
                pos = 0
                while True:
                    idx = data.find(p_u32, pos)
                    if idx == -1:
                        break
                    # check if 375 is within 128 bytes
                    sub = data[idx : idx + 128]
                    if b"\x77\x01\x00\x00" in sub:
                        hit_addr = curr + idx
                        found_hits.append((hit_addr, data[max(0, idx-64) : min(len(data), idx+256)]))
                    pos = idx + 4
            curr += chunk
    addr += mbi.RegionSize
    if addr >= 0x7FFFFFFF0000:
        break

print(f"Total HP=334 & MP=375 matches: {len(found_hits)}")
for hit_addr, win in found_hits[:15]:
    print(f"\n--- Hit at 0x{hit_addr:X} ---")
    # print as array of 32-bit ints
    ints = [struct.unpack_from("<I", win, o)[0] for o in range(0, len(win)-3, 4)]
    print("Ints:", ints[:30])

kernel32.CloseHandle(hProcess)

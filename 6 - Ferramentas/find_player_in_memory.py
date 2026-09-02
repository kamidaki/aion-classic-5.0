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
found_player = []

# Pattern: Name "card" in UTF-16LE = b"c\x00a\x00r\x00d\x00\x00\x00"
name_utf16 = b"c\x00a\x00r\x00d\x00\x00\x00"
name_ascii = b"card\x00"

print("Searching for character 'card' and stats in memory...")

while kernel32.VirtualQueryEx(hProcess, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
    if mbi.State == 0x1000 and (mbi.Protect & 0xFF) in (0x04, 0x02, 0x20, 0x40):
        curr = mbi.BaseAddress
        end = curr + mbi.RegionSize
        while curr < end:
            chunk = min(buffer_size, end - curr)
            if kernel32.ReadProcessMemory(hProcess, ctypes.c_void_p(curr), read_buf, chunk, ctypes.byref(bytes_read)):
                data = read_buf.raw[:bytes_read.value]
                
                # Check for name
                if name_utf16 in data:
                    idx = data.find(name_utf16)
                    hit_addr = curr + idx
                    # Check if 334 and 375 are nearby
                    window = data[max(0, idx-512) : min(len(data), idx+1024)]
                    if b"\x4e\x01" in window and b"\x77\x01" in window: # 334 and 375
                        print(f"[FOUND PLAYER WITH STATS] at 0x{hit_addr:X}")
                        found_player.append((hit_addr, window))
            curr += chunk
    addr += mbi.RegionSize
    if addr >= 0x7FFFFFFF0000:
        break

print(f"Total player matches: {len(found_player)}")
for hit_addr, win in found_player:
    print(f"\n--- Player at 0x{hit_addr:X} ---")
    print("Hex dump (first 256 bytes):")
    print(win[:256].hex())
    # Dump integers
    for off in range(0, len(win)-4, 4):
        val = struct.unpack_from("<I", win, off)[0]
        val_s = struct.unpack_from("<i", win, off)[0]
        val_f = struct.unpack_from("<f", win, off)[0]
        if val in (334, 375, 1, 24, 25, 100, 105, 110, 115, 90, 95):
            print(f"  off {off:4d} (+{off-512 if off>=512 else off}): u32={val}")

kernel32.CloseHandle(hProcess)

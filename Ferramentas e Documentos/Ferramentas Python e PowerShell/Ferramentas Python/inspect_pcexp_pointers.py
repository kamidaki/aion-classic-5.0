import ctypes
from ctypes import wintypes
import struct

PROCESS_VM_READ = 0x0010
kernel32 = ctypes.windll.kernel32

pid = 11076
hProcess = kernel32.OpenProcess(PROCESS_VM_READ, False, pid)

def read_mem(addr, size):
    buf = ctypes.create_string_buffer(size)
    n = ctypes.c_size_t()
    if kernel32.ReadProcessMemory(hProcess, ctypes.c_void_p(addr), buf, size, ctypes.byref(n)):
        return buf.raw[:n.value]
    return None

data = read_mem(0x4C54C000, 0x4000)
if data:
    print("Memory at 0x4C54C000 length:", len(data))
    # Look for pointers (64-bit addresses between 0x10000000 and 0x7FFFFFFF0000)
    for off in range(0, len(data)-7, 8):
        ptr = struct.unpack_from("<Q", data, off)[0]
        if 0x10000000 <= ptr <= 0x7FFFFFFF0000:
            target = read_mem(ptr, 64)
            if target and any(c >= 32 and c <= 126 for c in target[:10]):
                txt = target[:32].decode('ascii', errors='ignore')
                print(f"  off 0x{off:X} (0x{0x4C54C000+off:X}) -> ptr 0x{ptr:X}: {txt}")

kernel32.CloseHandle(hProcess)

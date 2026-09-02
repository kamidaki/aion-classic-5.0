import ctypes

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

data = read_mem(0x4C543880, 768)
if data:
    print("Memory at 0x4C543880:")
    strings = [s for s in data.split(b"\x00") if s]
    for s in strings:
        print(" ", s)

kernel32.CloseHandle(hProcess)

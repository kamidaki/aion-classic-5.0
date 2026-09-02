import ctypes
from ctypes import wintypes
import struct

PROCESS_VM_READ = 0x0010
kernel32 = ctypes.windll.kernel32

pid = 11076
hProcess = kernel32.OpenProcess(PROCESS_VM_READ, False, pid)

game_dll_base = 0x4B7F0000
game_dll_size = 0x01E61000

def read_mem(addr, size):
    buf = ctypes.create_string_buffer(size)
    n = ctypes.c_size_t()
    if kernel32.ReadProcessMemory(hProcess, ctypes.c_void_p(addr), buf, size, ctypes.byref(n)):
        return buf.raw[:n.value]
    return None

data = read_mem(game_dll_base, game_dll_size)
print(f"Read {len(data)} bytes from Game.dll")

# Search for class names: "warrior", "gladiator", "templar", "scout", "assassin", "ranger", "mage", "sorcerer", "elementallist", "priest", "cleric", "chanter", "monk", "thunderer", "brawler", "luminess", "phoenix", "reaper", "soul_reaper"
class_names = [
    b"warrior", b"gladiator", b"templar", b"scout", b"assassin", b"ranger",
    b"mage", b"sorcerer", b"elementallist", b"priest", b"cleric", b"chanter",
    b"monk", b"thunderer", b"brawler", b"luminess", b"phoenix", b"reaper", b"soul_reaper"
]

for cn in class_names:
    pos = 0
    hits = []
    while True:
        idx = data.find(cn, pos)
        if idx == -1:
            break
        addr = game_dll_base + idx
        hits.append(addr)
        pos = idx + len(cn)
    print(f"Class '{cn.decode()}': {len(hits)} occurrences in Game.dll")
    if hits:
        # inspect first hit context
        first_addr = hits[0]
        ctx = data[first_addr - game_dll_base : first_addr - game_dll_base + 64]
        print(f"  First at 0x{first_addr:X}: hex={ctx[:32].hex()} ascii={ctx[:32]}")

kernel32.CloseHandle(hProcess)

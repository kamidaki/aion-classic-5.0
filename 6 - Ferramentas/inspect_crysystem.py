import pefile
import re

with open(r"D:\GameForge\aionclassic\bin64\CrySystem.dll", "rb") as f:
    dll = f.read()

print(f"CrySystem.dll size: {len(dll)} bytes")

# Search for zip / pak strings
strings = re.findall(b"[a-zA-Z0-9_/\\-\\.]{4,}", dll)
pak_strings = [s.decode('ascii', errors='ignore') for s in strings if b'pak' in s.lower() or b'zip' in s.lower() or b'encrypt' in s.lower() or b'crypt' in s.lower()]
print(f"Found {len(pak_strings)} relevant strings:")
for s in pak_strings[:30]:
    print(" ", s)

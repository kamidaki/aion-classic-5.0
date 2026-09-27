import sys
import os
import struct
import io

sys.path.insert(0, ".")
from core.pak_engine import AionPakArchive

archive = AionPakArchive("D:/GameForge/aionclassic/objects/npc/shugomale/shugomale_Meshes.pak")
data = archive.read_file("shugomale.cgf")

# Find BoneNameList
name_off = 175320
num_names = struct.unpack_from("<I", data, name_off)[0]
raw_names = data[name_off+4:name_off+4+5000].split(b"\x00")[:num_names]
names = [n.decode("latin-1") for n in raw_names]
print(f"Num bone names: {num_names}, Names: {names[:10]}")

# Inspect BoneInitialPos at 166492
# BoneInitialPos chunk header is 16 bytes: chunk_type(4), version(4), offset(4), id(4)
# Let's check size between 166492 and 168612: 2120 bytes
bip_off = 166492
bip_data = data[bip_off:]
# What does BoneInitialPos contain?
print("BoneInitialPos start:", [hex(x) for x in struct.unpack_from("<8I", bip_data, 0)])

# Inspect BoneAnim at 168612
ba_off = 168612
ba_data = data[ba_off:]
print("BoneAnim start:", [hex(x) for x in struct.unpack_from("<8I", ba_data, 0)])

# Also let's inspect shugomale_Animations.pak for nidle
anim_archive = AionPakArchive("D:/GameForge/aionclassic/objects/npc/shugomale/shugomale_Animations.pak")
caf_data = anim_archive.read_file("shugomale_nidle_001_loop.caf")
print(f"CAF data length: {len(caf_data)}")
print("CAF header:", caf_data[:16])

# Parse CAF chunks
stream = io.BytesIO(caf_data)
# signature
sig = ""
while True:
    b = stream.read(1)
    if b == b"\x00":
        break
    sig += b.decode("ascii")
stream.read(1) # second null byte
type_of_file = struct.unpack("<I", stream.read(4))[0]
ver = struct.unpack("<I", stream.read(4))[0]
table_offset = struct.unpack("<I", stream.read(4))[0]
print(f"CAF Sig: {sig}, Type: {hex(type_of_file)}, Ver: {hex(ver)}, Table Off: {table_offset}")

stream.seek(table_offset)
num_chunks = struct.unpack("<I", stream.read(4))[0]
print(f"Num chunks in CAF: {num_chunks}")
from formats.cgf.parser import get_header
caf_headers = [get_header(stream) for _ in range(num_chunks)]
print("Sample CAF chunks:", caf_headers[:10])

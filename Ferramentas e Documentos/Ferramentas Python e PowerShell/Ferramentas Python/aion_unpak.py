import io
import os
import struct
import zipfile

def unpak_stream(data):
    """
    Aion PAKs have ZIP magic bytes inverted:
    PK\x03\x04 (0x04034b50) -> 0xfbcfb4af
    PK\x01\x02 (0x02014b50) -> 0xfefeb4af
    PK\x05\x06 (0x06054b50) -> 0xfafab4af / etc.
    """
    buf = bytearray(data)
    # Replace all occurrences of inverted zip headers
    # Local header:
    # 0xAF, 0xB4, 0xFC, 0xFB -> 0x50, 0x4B, 0x03, 0x04
    # Central directory header:
    # 0xAF, 0xB4, 0xFE, 0xFD -> 0x50, 0x4B, 0x01, 0x02
    # End of central directory header:
    # 0xAF, 0xB4, 0xFA, 0xF9 -> 0x50, 0x4B, 0x05, 0x06
    
    # Or let's scan for signatures:
    for i in range(len(buf) - 3):
        if buf[i] == 0xAF and buf[i+1] == 0xB4:
            if buf[i+2] == 0xFC and buf[i+3] == 0xFB:
                buf[i:i+4] = b'PK\x03\x04'
            elif buf[i+2] == 0xFE and buf[i+3] == 0xFD:
                buf[i:i+4] = b'PK\x01\x02'
            elif buf[i+2] == 0xFA and buf[i+3] == 0xF9:
                buf[i:i+4] = b'PK\x05\x06'
                
    return zipfile.ZipFile(io.BytesIO(buf))

def test_pak(pak_path):
    print(f"Reading {pak_path}...")
    with open(pak_path, "rb") as f:
        data = f.read()
    zf = unpak_stream(data)
    names = zf.namelist()
    print(f"  Total files: {len(names)}")
    for n in names[:10]:
        print(f"   - {n}")
    return zf

if __name__ == "__main__":
    test_pak(r"D:\GameForge\aionclassic\data\PC\PC.pak")
    test_pak(r"D:\GameForge\aionclassic\data\gamedata\gamedata.pak")

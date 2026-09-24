with open(r"D:\GameForge\aionclassic\data\PC\PC.pak", "rb") as f:
    raw = f.read(500)
    print("Raw header:")
    print(" ".join(f"{b:02x}" for b in raw[:64]))

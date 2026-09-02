with open(r"C:\Users\Fire\.gemini\antigravity-ide\brain\f4d4b775-bc82-4299-8288-9b4190b2c97b\.system_generated\tasks\task-1324.log", "r", encoding="utf-8", errors="replace") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "error[" in line or "error:" in line:
        print(f"Line {i}: {line.strip()}")
        for sub in lines[max(0, i-2) : min(len(lines), i+10)]:
            print("  ", sub.strip())

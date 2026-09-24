import sys

log_file = sys.argv[1] if len(sys.argv) > 1 else "build.log"
try:
    with open(log_file, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
except FileNotFoundError:
    print(f"Log file '{log_file}' not found.")
    sys.exit(0)

for i, line in enumerate(lines):
    if "error[" in line or "error:" in line:
        print(f"Line {i}: {line.strip()}")
        for sub in lines[max(0, i-2) : min(len(lines), i+10)]:
            print("  ", sub.strip())

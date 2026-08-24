import time
import os
import sys

LOG_PATHS = [
    r"D:\AION RUST\AionEMU\AionEMU\Cliente\GFAion\aionclassic\bin64\version_hook.log",
    r"D:\AION RUST\AionEMU\AionEMU\Cliente\GFAion\aionclassic\bin32\version_hook.log",
    r"D:\AION RUST\AionEMU\AionEMU\Produto Final\logs\login-server.log",
    r"D:\AION RUST\AionEMU\AionEMU\Produto Final\logs\game-server.log",
    r"D:\AION RUST\AionEMU\AionEMU\Produto Final\logs\chat-server.log",
    r"D:\AION RUST\AionEMU\AionEMU\Produto Final\logs\launcher.log",
]

OUTPUT_CAPTURE = r"D:\AION RUST\AionEMU\AionEMU\Docs-Refs\Wireshark_Collects_Classic4.5_OficialServer\live_session_analysis.txt"

def main():
    print("[*] Live Packet & Hook Collector iniciado.")
    print("[*] Monitorando portas 2106, 13001, 7777, 10241 e logs do version.dll...")
    
    with open(OUTPUT_CAPTURE, "w", encoding="utf-8") as out:
        out.write(f"=== SESSAO DE CAPTURA E TELEMETRIA AO VIVO - {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
        out.flush()

    file_positions = {}

    while True:
        for path in LOG_PATHS:
            if os.path.exists(path):
                if path not in file_positions:
                    file_positions[path] = os.path.getsize(path)
                
                curr_size = os.path.getsize(path)
                if curr_size > file_positions[path]:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        f.seek(file_positions[path])
                        new_lines = f.read()
                        file_positions[path] = f.tell()
                        
                        if new_lines.strip():
                            tag = os.path.basename(path)
                            formatted = f"[{time.strftime('%H:%M:%S')}] [{tag}]\n{new_lines}\n"
                            print(formatted, end="")
                            with open(OUTPUT_CAPTURE, "a", encoding="utf-8") as out:
                                out.write(formatted)
                                out.flush()
        time.sleep(0.5)

if __name__ == "__main__":
    main()

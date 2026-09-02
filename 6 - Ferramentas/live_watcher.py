# -*- coding: utf-8 -*-
"""
AION CLASSIC 5.0 - REALTIME WIRE & MEMORY MONITOR
Monitor em tempo real de tráfego de rede (Wireshark/dumpcap) e memória de processo (Aion.bin / game.dll).
"""
import sys, os, time, struct, subprocess, ctypes
from ctypes import wintypes

PROCESS_ALL_ACCESS = 0x1F0FFF

class MemoryInspector:
    def __init__(self):
        self.pid = None
        self.handle = None
        self.k32 = ctypes.windll.kernel32

    def find_process(self, process_name="Aion.bin"):
        try:
            out = subprocess.check_output(f'tasklist /FI "IMAGENAME eq {process_name}" /FO CSV /NH', shell=True).decode('latin1', errors='ignore')
            for line in out.strip().splitlines():
                parts = [p.strip(' "') for p in line.split(',')]
                if len(parts) >= 2 and parts[0].lower() == process_name.lower():
                    pid = int(parts[1])
                    if pid != self.pid:
                        self.pid = pid
                        self.handle = self.k32.OpenProcess(PROCESS_ALL_ACCESS, False, self.pid)
                        print(f"[MEM] Conectado ao processo {process_name} (PID={self.pid}, Handle=0x{self.handle:X})")
                    return self.pid
        except Exception as e:
            pass
        return None

    def read_bytes(self, address, size):
        if not self.handle: return None
        buf = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t(0)
        res = self.k32.ReadProcessMemory(self.handle, ctypes.c_void_p(address), buf, size, ctypes.byref(bytes_read))
        if res:
            return bytes(buf[:bytes_read.value])
        return None

    def write_bytes(self, address, data):
        if not self.handle: return False
        buf = ctypes.create_string_buffer(data)
        bytes_written = ctypes.c_size_t(0)
        res = self.k32.WriteProcessMemory(self.handle, ctypes.c_void_p(address), buf, len(data), ctypes.byref(bytes_written))
        return bool(res)

def start_capture_dumpcap(output_file, interface=5):
    dumpcap_path = r"E:\Programas instalados - Leves\Wireshark\dumpcap.exe"
    if not os.path.exists(dumpcap_path):
        dumpcap_path = r"C:\Program Files\Wireshark\dumpcap.exe"
    
    cmd = [
        dumpcap_path,
        "-i", str(interface),
        "-f", "tcp and (port 2106 or port 7777 or port 10241 or port 13001 or port 6600)",
        "-w", output_file,
        "-q"
    ]
    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[NET] Dumpcap iniciado na interface {interface}, gravando em {output_file} (PID={p.pid})")
    return p

if __name__ == '__main__':
    print("=================================================================")
    print(" AION CLASSIC 5.0 - STANDBY MONITOR ATIVO")
    print(" Pronto para capturar pacotes e inspecionar memória do jogo.")
    print("=================================================================")
    inspector = MemoryInspector()
    inspector.find_process("Aion.bin")

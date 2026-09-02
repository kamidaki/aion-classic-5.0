import os
import sys
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TOOLS_DIR)
import os
import pyshark
import struct
import blowfish

# Blowfish implementation matching commons/src/crypto/game.rs
STATIC_KEY = b"\x73\x64\x73\x26\x67\x66\x64\x23\x40\x23\x24\x25\x21\x7e\x2b\x60"

def get_xor_key(raw_seed):
    # raw_seed is u32 from SM_VERSION
    # let raw_seed = (seed as u64).wrapping_mul(0x343F_D).wrapping_add(0x269_EC3) as u32;
    seed = (raw_seed * 0x343FD + 0x269EC3) & 0xFFFFFFFF
    key = bytearray(8)
    key[0] = (seed & 0xFF) ^ 0x39
    key[1] = ((seed >> 8) & 0xFF) ^ 0x32
    key[2] = ((seed >> 16) & 0xFF) ^ 0x77
    key[3] = ((seed >> 24) & 0xFF) ^ 0x47
    key[4] = key[0] ^ 0xA8
    key[5] = key[1] ^ 0x24
    key[6] = key[2] ^ 0x38
    key[7] = key[3] ^ 0x56
    return bytes(key)

def decrypt_gameserver_stream(packets):
    # packets is list of (srcport, dstport, bytes)
    # Server packets have srcport == 7777
    # Client packets have dstport == 7777
    
    server_cipher = None
    client_cipher = None
    
    decrypted_packets = []
    
    # Assembly buffers for TCP stream
    c2s_stream = bytearray()
    s2c_stream = bytearray()
    
    for srcport, dstport, data in packets:
        if srcport == 7777: # S -> C
            s2c_stream.extend(data)
        elif dstport == 7777: # C -> S
            c2s_stream.extend(data)
            
    # Process S -> C
    idx = 0
    while idx + 2 <= len(s2c_stream):
        pkt_len = struct.unpack_from('<H', s2c_stream, idx)[0]
        if pkt_len == 0 or idx + pkt_len > len(s2c_stream):
            break
        pkt_data = bytearray(s2c_stream[idx+2 : idx+pkt_len])
        idx += pkt_len
        
        if server_cipher is None:
            # First packet is SM_VERSION (unencrypted blowfish, plaintext or static key)
            # Check if it is SM_VERSION (0x0000)
            # In Aion, SM_VERSION is sent unencrypted
            opcode = struct.unpack_from('<H', pkt_data, 0)[0]
            # SM_VERSION has opcode 0x0000, len 55/57
            if opcode == 0x0000:
                raw_seed = struct.unpack_from('<I', pkt_data, 10)[0]
                derived_key = get_xor_key(raw_seed)
                server_cipher = blowfish.Cipher(derived_key)
                client_cipher = blowfish.Cipher(derived_key)
                decrypted_packets.append(('S->C', opcode, bytes(pkt_data), 'SM_VERSION', raw_seed, derived_key.hex()))
                continue
            else:
                # Try decrypting with STATIC_KEY
                pass
        
        if server_cipher:
            # Decrypt packet in 8-byte blocks
            dec = bytearray()
            for b in range(0, len(pkt_data), 8):
                block = bytes(pkt_data[b:b+8])
                if len(block) == 8:
                    dec.extend(server_cipher.decrypt_block(block))
                else:
                    dec.extend(block)
            
            # Opcode is first 2 bytes
            opcode = struct.unpack_from('<H', dec, 0)[0] if len(dec) >= 2 else None
            decrypted_packets.append(('S->C', opcode, bytes(dec), '', 0, ''))
            
    # Process C -> S
    idx = 0
    while idx + 2 <= len(c2s_stream):
        pkt_len = struct.unpack_from('<H', c2s_stream, idx)[0]
        if pkt_len == 0 or idx + pkt_len > len(c2s_stream):
            break
        pkt_data = bytearray(c2s_stream[idx+2 : idx+pkt_len])
        idx += pkt_len
        
        if client_cipher:
            dec = bytearray()
            for b in range(0, len(pkt_data), 8):
                block = bytes(pkt_data[b:b+8])
                if len(block) == 8:
                    dec.extend(client_cipher.decrypt_block(block))
                else:
                    dec.extend(block)
            opcode = struct.unpack_from('<H', dec, 0)[0] if len(dec) >= 2 else None
            decrypted_packets.append(('C->S', opcode, bytes(dec), '', 0, ''))
            
    return decrypted_packets

def run_analysis():
    pcap_files = [
        os.path.join(PROJECT_ROOT, "5 - Documentação e Referências", "2 - Wireshark - Oficial Classic 5.0", "01_Login_World\Elyos\01_Login_World_Elyos_2026-08-27_10-03-03_00001_20260827100304.pcapng"),
        os.path.join(PROJECT_ROOT, "5 - Documentação e Referências", "2 - Wireshark - Oficial Classic 5.0", "01_Login_World\Asmodians\01_Login_World_Asmodians_2026-08-27_10-08-12_00001_20260827100812.pcapng"),
        os.path.join(PROJECT_ROOT, "5 - Documentação e Referências", "2 - Wireshark - Oficial Classic 5.0", "02_Character_Creation\Elyos\02_Character_Creation_Elyos_2026-08-27_10-10-24_00001_20260827101024.pcapng")
    ]
    
    for filepath in pcap_files:
        if not os.path.exists(filepath):
            continue
        print("=" * 100)
        print(f"ANÁLISE DO ARQUIVO: {os.path.basename(filepath)}")
        print("=" * 100)
        
        cap = pyshark.FileCapture(filepath, display_filter="tcp.port == 7777")
        packets = []
        for pkt in cap:
            try:
                tcp = pkt.tcp
                srcport = int(tcp.srcport)
                dstport = int(tcp.dstport)
                payload_hex = getattr(tcp, 'payload', None)
                if payload_hex:
                    raw_bytes = bytes.fromhex(payload_hex.replace(':', ''))
                    packets.append((srcport, dstport, raw_bytes))
            except Exception:
                pass
        cap.close()
        
        print(f"Total de segmentos TCP 7777 coletados: {len(packets)}")
        
        # Agora decifra e processa
        s2c_stream = bytearray()
        c2s_stream = bytearray()
        
        for srcport, dstport, data in packets:
            if srcport == 7777:
                s2c_stream.extend(data)
            elif dstport == 7777:
                c2s_stream.extend(data)
                
        # S -> C
        print("\n--- [SERVER -> CLIENT (S->C)] ---")
        idx = 0
        server_cipher = None
        s2c_list = []
        while idx + 2 <= len(s2c_stream):
            pkt_len = struct.unpack_from('<H', s2c_stream, idx)[0]
            if pkt_len == 0 or idx + pkt_len > len(s2c_stream):
                break
            pkt_data = bytearray(s2c_stream[idx+2 : idx+pkt_len])
            idx += pkt_len
            
            if server_cipher is None:
                opcode = struct.unpack_from('<H', pkt_data, 0)[0]
                if opcode == 0x0000: # SM_VERSION
                    raw_seed = struct.unpack_from('<I', pkt_data, 10)[0]
                    derived_key = get_xor_key(raw_seed)
                    server_cipher = blowfish.Cipher(derived_key)
                    print(f"[0x0000] SM_VERSION | Len: {len(pkt_data)} | Seed: 0x{raw_seed:08X} | DerivedKey: {derived_key.hex()}")
                    continue
            
            if server_cipher:
                dec = bytearray()
                for b in range(0, len(pkt_data), 8):
                    block = bytes(pkt_data[b:b+8])
                    if len(block) == 8:
                        dec.extend(server_cipher.decrypt_block(block))
                    else:
                        dec.extend(block)
                opcode = struct.unpack_from('<H', dec, 0)[0]
                s2c_list.append((opcode, len(dec), bytes(dec)))
                print(f"[0x{opcode:04X}] SM_PACKET | Payload Len: {len(dec)} | Hex (first 32): {dec[:32].hex()}")
                
        # C -> S
        print("\n--- [CLIENT -> SERVER (C->S)] ---")
        idx = 0
        client_cipher = None
        if server_cipher: # Use same key
            client_cipher = server_cipher
            while idx + 2 <= len(c2s_stream):
                pkt_len = struct.unpack_from('<H', c2s_stream, idx)[0]
                if pkt_len == 0 or idx + pkt_len > len(c2s_stream):
                    break
                pkt_data = bytearray(c2s_stream[idx+2 : idx+pkt_len])
                idx += pkt_len
                
                dec = bytearray()
                for b in range(0, len(pkt_data), 8):
                    block = bytes(pkt_data[b:b+8])
                    if len(block) == 8:
                        dec.extend(client_cipher.decrypt_block(block))
                    else:
                        dec.extend(block)
                opcode = struct.unpack_from('<H', dec, 0)[0]
                print(f"[0x{opcode:04X}] CM_PACKET | Payload Len: {len(dec)} | Hex (first 32): {dec[:32].hex()}")

if __name__ == "__main__":
    run_analysis()


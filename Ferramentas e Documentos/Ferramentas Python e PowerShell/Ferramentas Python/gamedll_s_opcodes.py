"""Tabela nome -> opcode dos pacotes S_ (servidor -> cliente), lida direto do Game.dll.

O Game.dll registra cada pacote do servidor com um destes pares

    lea r8, [rip+"S_NOME"]            lea rdx, [rip+"S_NOME"]
    mov dword ptr [rbp+x], OPCODE     mov dword ptr [rsp+x], OPCODE

entao o numero logo depois da referencia ao nome e o opcode decodificado (o mesmo de
`addPacketOpcode` no ServerPacketsOpcodes e da coluna "op" do aion_pcap.py). Conferido em
01/10/2026 contra opcodes provados por captura: S_CHARACTER_LIST 0xC7, S_RECONNECT_KEY 0xFF,
S_BUDDY_LIST 0x83, S_BLOCK_LIST 0xE0, S_SIGN_CLIENT 0xE6, S_BATTLEPASS_LIST 0x117.

Os C_ (cliente -> servidor) nao sao registrados assim; para eles so a captura.

    python gamedll_s_opcodes.py [Game.dll] [saida.txt]
"""
import re
import struct
import sys

PADRAO_DLL = r"G:\Projetos AION\Classic\Ferramentas e Documentos\Patch final - Client 5.0\bin64\Game.dll"


def secoes(d):
    e = struct.unpack_from('<I', d, 0x3c)[0]
    n = struct.unpack_from('<H', d, e + 6)[0]
    sh = e + 24 + struct.unpack_from('<H', d, e + 20)[0]
    return [struct.unpack_from('<IIII', d, sh + i * 40 + 8) for i in range(n)]


def tabela(d):
    secs = secoes(d)

    def f2r(f):
        for _vs, rva, rs, rp in secs:
            if rp <= f < rp + rs:
                return rva + f - rp

    nomes = {}
    for m in re.finditer(rb'S_[A-Z0-9_]{2,48}(?=\x00)', d):
        r = f2r(m.start())
        if r is not None:
            nomes[r] = m.group(0).decode()

    tab = {}
    for m in re.finditer(rb'[\x48\x4c]\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]', d):
        i = m.start()
        r = f2r(i)
        if r is None:
            continue
        alvo = r + 7 + struct.unpack_from('<i', d, i + 3)[0]
        if alvo not in nomes:
            continue
        trecho = d[i + 7:i + 24]
        op = None
        k = trecho.find(b'\xc7\x85')  # mov dword ptr [rbp+disp32], imm32 (lea r8,[nome] antes)
        if k >= 0:
            op = struct.unpack_from('<I', trecho, k + 6)[0]
        else:
            k = trecho.find(b'\xc7\x44\x24')  # mov dword ptr [rsp+disp8], imm32 (lea rdx,[nome] antes)
            if k >= 0:
                op = struct.unpack_from('<I', trecho, k + 4)[0]
        if op is not None and op < 0x400:
            tab[nomes[alvo]] = op
    return tab


def main(argv):
    dll = argv[0] if argv else PADRAO_DLL
    d = open(dll, 'rb').read()
    tab = tabela(d)
    linhas = ["0x%04X %s" % (op, nome) for nome, op in sorted(tab.items(), key=lambda x: (x[1], x[0]))]
    if len(argv) > 1:
        with open(argv[1], 'w', encoding='utf-8') as f:
            f.write("\n".join(linhas) + "\n")
    else:
        print("\n".join(linhas))
    print("%d pacotes S_" % len(tab), file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:])

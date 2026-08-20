"""
Extrai a tabela de opcodes de rede do Game.dll do cliente Aion Classic.

O cliente registra cada pacote em uma funcao gigante de inicializacao. Cada
registro tem a forma:

    lea  rdx/r8, [rip+disp32]      ; ponteiro para a string "S_XXX" / "C_XXX"
    mov  dword ptr [mem], imm32    ; imm32 == numero do opcode

As strings ficam em texto claro mesmo com o Game.dll protegido (Themida),
entao a tabela inteira pode ser lida estaticamente, sem sniffer.

Uso:  python tools/extract_opcodes.py <caminho/Game.dll> [-o docs/protocol]
"""
import argparse, csv, os, re, struct, sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe import PE

# lea rXX, [rip+disp32] -> prefixo de 3 bytes por registrador destino
LEA_PREFIXES = {
    b'\x48\x8d\x05': 'rax', b'\x48\x8d\x0d': 'rcx', b'\x48\x8d\x15': 'rdx',
    b'\x48\x8d\x1d': 'rbx', b'\x48\x8d\x35': 'rsi', b'\x48\x8d\x3d': 'rdi',
    b'\x4c\x8d\x05': 'r8',  b'\x4c\x8d\x0d': 'r9',  b'\x4c\x8d\x15': 'r10',
    b'\x4c\x8d\x1d': 'r11', b'\x4c\x8d\x25': 'r12', b'\x4c\x8d\x2d': 'r13',
    b'\x4c\x8d\x35': 'r14', b'\x4c\x8d\x3d': 'r15',
}

# mov dword ptr [...], imm32 -- as tres formas usadas pelo compilador da NCSoft
IMM_PATTERNS = [
    re.compile(rb'\xc7\x44\x24.(....)', re.S),      # mov [rsp+disp8],  imm32
    re.compile(rb'\xc7\x45.(....)', re.S),          # mov [rbp+disp8],  imm32
    re.compile(rb'\xc7\x85....(....)', re.S),       # mov [rbp+disp32], imm32
]

OPCODE_NAME = re.compile(rb'^(?:C|S)_[A-Z0-9_]{2,}$')
PRINTABLE = re.compile(rb'[ -~]{4,64}')
LOOKAHEAD = 48          # bytes apos o lea onde o imm32 aparece
LOOKBEHIND = 24         # alguns registros carregam o imm32 antes do lea
CLUSTER_GAP = 4096      # distancia maxima entre registros da mesma tabela


def find_opcode_strings(pe):
    """VA -> nome, para toda string que parece nome de pacote."""
    out = {}
    for m in PRINTABLE.finditer(pe.data):
        if OPCODE_NAME.match(m.group()):
            rva = pe.off2rva(m.start())
            if rva is not None:
                out[pe.imagebase + rva] = m.group().decode()
    return out


def find_lea_sites(pe, va2name):
    """Todo lea rip-relativo que aponta para uma string de opcode."""
    sites = []
    for prefix, reg in LEA_PREFIXES.items():
        pat = re.compile(re.escape(prefix) + rb'(....)', re.S)
        for m in pat.finditer(pe.data):
            disp = struct.unpack('<i', m.group(1))[0]
            target = pe.imagebase + pe.off2rva(m.start() + 7) + disp
            name = va2name.get(target)
            if name:
                sites.append((m.start(), reg, name))
    sites.sort()
    return sites


def largest_cluster(sites):
    """A tabela de registro e o maior grupo contiguo de sites."""
    clusters, cur = [], [sites[0]]
    for s in sites[1:]:
        if s[0] - cur[-1][0] < CLUSTER_GAP:
            cur.append(s)
        else:
            clusters.append(cur)
            cur = [s]
    clusters.append(cur)
    return max(clusters, key=len)


def immediate_after(data, off):
    """Primeiro `mov dword [...], imm32` proximo ao lea (a frente, senao atras)."""
    best = None
    for pat in IMM_PATTERNS:
        m = pat.search(data[off:off + LOOKAHEAD])
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), struct.unpack('<I', m.group(1))[0])
    if best is not None:
        return best[1]

    # o compilador as vezes emite o imm32 imediatamente antes do lea
    behind = data[max(0, off - LOOKBEHIND):off]
    last = None
    for pat in IMM_PATTERNS:
        for m in pat.finditer(behind):
            if last is None or m.start() > last[0]:
                last = (m.start(), struct.unpack('<I', m.group(1))[0])
    return last[1] if last else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('game_dll')
    ap.add_argument('-o', '--outdir', default='docs/protocol')
    args = ap.parse_args()

    pe = PE(args.game_dll)
    va2name = find_opcode_strings(pe)
    sites = find_lea_sites(pe, va2name)
    if not sites:
        sys.exit('Nenhuma string de opcode encontrada -- binario protegido ou versao diferente.')

    table = largest_cluster(sites)
    print(f'{os.path.basename(args.game_dll)}: {len(va2name)} strings, '
          f'{len(sites)} referencias, tabela em '
          f'0x{table[0][0]:x}..0x{table[-1][0]:x} ({len(table)} registros)')

    votes = defaultdict(Counter)
    unresolved = []
    for off, _reg, name in table:
        imm = immediate_after(pe.data, off)
        if imm is None:
            unresolved.append(name)
        else:
            votes[name][imm] += 1

    server, client = {}, {}
    collisions = []
    for name, counter in votes.items():
        opcode = counter.most_common(1)[0][0]
        target = server if name.startswith('S_') else client
        if opcode in target and target[opcode] != name:
            collisions.append((opcode, target[opcode], name))
        target[opcode] = name

    os.makedirs(args.outdir, exist_ok=True)
    for tag, mapping in (('server', server), ('client', client)):
        path = os.path.join(args.outdir, f'opcodes_{tag}.csv')
        with open(path, 'w', newline='', encoding='utf-8') as fh:
            w = csv.writer(fh)
            w.writerow(['opcode_dec', 'opcode_hex', 'name'])
            for op in sorted(mapping):
                w.writerow([op, f'0x{op:x}', mapping[op]])
        span = f'0..{max(mapping)}' if mapping else 'vazio'
        print(f'  {tag}: {len(mapping)} opcodes ({span}) -> {path}')

    if unresolved:
        print(f'  sem imediato ({len(unresolved)}): {", ".join(unresolved[:8])}'
              + (' ...' if len(unresolved) > 8 else ''))
    if collisions:
        print(f'  colisoes ({len(collisions)}): ' +
              ', '.join(f'0x{o:x} {a}/{b}' for o, a, b in collisions[:8]))


if __name__ == '__main__':
    main()

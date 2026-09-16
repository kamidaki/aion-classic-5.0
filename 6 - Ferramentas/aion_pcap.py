"""Decifra o protocolo de jogo do Aion Classic (porta 7777) a partir de uma pcapng.

A cifra e o enquadramento sao os de `commons/src/crypto/game.rs` e
`game-server/src/message/mod.rs`:

  fio:    [u16 len incluindo os 2 bytes][corpo cifrado]
  corpo:  [u16 opcode][1 byte de servidor][u16 checksum = !opcode][payload]

O primeiro pacote do servidor (S_KEY) viaja em claro e traz o seed nos ultimos 4
bytes. Dele sai a chave de 8 bytes; cada direcao mantem a sua, avancando pelo
tamanho do corpo que acabou de passar.

O checksum e a prova: se a cifra, a chave ou o enquadramento estiverem errados,
`checksum == !opcode` nao fecha. Nao ha como acertar por acaso.

Modos:

    --opcodes                        censo do que o cliente manda, com tamanho de corpo
    --correlacao                     pedido -> resposta, com o fundo descontado
    --censo-salva <arquivo.json>     grava o censo como linha de base
    --censo-compara <arquivo.json>   confere esta captura contra a linha de base

Os dois ultimos existem para responder "os opcodes sobreviveram ao patch?". Grava-se o censo de
uma captura boa de uma versao, e depois do patch basta uma captura curta com o cliente novo para
o veredito sair pronto. O que da forca ao teste e o **tamanho do corpo**: so o numero bater nao
prova nada, dois pacotes diferentes podem cair no mesmo valor -- bater numero e forma nao e
coincidencia. A linha de base do Classic 4.5 esta em `tools/censo-opcodes-classic-4.5.json`.

O censo varre **todas as sessoes de jogo** da captura, nao so a primeira. Uma subida longa nao
cabe num login so, e cada reconexao abre um TCP novo com o seu proprio S_KEY -- analisar so o
primeiro seria olhar vinte minutos de uma sessao de doze horas sem perceber. A correlacao continua
na primeira sessao, que juntar tempo de sessoes diferentes nao faz sentido.

Para saber se o patch mexeu no protocolo **sem capturar nada**, ver
`tools/diff_pacotes_cliente.py`, que compara a lista de pacotes dos dois `Game.dll`.
"""
import os
import struct, sys
from collections import defaultdict

STATIC_KEY = b"nKO/WctQ0AVLbpzfBkS6NevDYT8ourG5CRlmdjyJ72aswx4EPq1UgZhFMXH?3iI9"
SUB_SEED, XOR_SEED_32, XOR_SEED_64 = 0x3FF2CC87, 0xCD92E451, 0x87546CA100000000


def gen_xor_key(seed):
    seed = (seed - SUB_SEED) & 0xFFFFFFFF
    seed ^= XOR_SEED_32
    return (seed ^ XOR_SEED_64) & 0xFFFFFFFFFFFFFFFF


class Cifra:
    """Estado de uma direcao. A chave avanca pelo tamanho de cada corpo."""

    def __init__(self, seed):
        self.key = bytearray(struct.pack("<Q", gen_xor_key(seed)))

    def decrypt(self, data):
        d = bytearray(data)
        primeiro = self.key[0]
        for i in range(len(d) - 1, 0, -1):
            d[i] ^= self.key[i & 7] ^ STATIC_KEY[i & 63] ^ d[i - 1]
        novo = (struct.unpack("<Q", bytes(self.key))[0] + len(d)) & 0xFFFFFFFFFFFFFFFF
        self.key[:] = struct.pack("<Q", novo)
        if d:
            d[0] ^= primeiro
        return bytes(d)


def opcode_cliente(op):
    return ((op ^ 0x36) - 0xC4) & 0xFFFF


def opcode_servidor(op):
    return ((op ^ 0xD4) - 0xC4) & 0xFFFF


# ---------------------------------------------------------------- pcapng

def blocos(caminho):
    """Cada EPB da captura, como `(linktype, quadro, timestamp)`.

    O timestamp e o do proprio EPB, em unidades da interface (microssegundo por padrao). So a
    ordem relativa importa aqui -- e ela que permite dizer qual pacote de servidor veio depois de
    qual pedido do cliente.
    """
    with open(caminho, "rb") as f:
        dados = f.read()
    off, endian, linktype = 0, "<", 1
    while off + 8 <= len(dados):
        tipo = struct.unpack_from(endian + "I", dados, off)[0]
        if tipo == 0x0A0D0D0A:
            magic = struct.unpack_from("<I", dados, off + 8)[0]
            endian = "<" if magic == 0x1A2B3C4D else ">"
            tipo = struct.unpack_from(endian + "I", dados, off)[0]
        total = struct.unpack_from(endian + "I", dados, off + 4)[0]
        if total < 12 or off + total > len(dados):
            break
        corpo = dados[off + 8: off + total - 4]
        if tipo == 0x00000001:                      # IDB
            linktype = struct.unpack_from(endian + "H", corpo, 0)[0]
        elif tipo == 0x00000006:                    # EPB
            alto, baixo = struct.unpack_from(endian + "II", corpo, 4)
            cap = struct.unpack_from(endian + "I", corpo, 12)[0]
            yield linktype, corpo[20:20 + cap], (alto << 32) | baixo
        off += total


def tcp_de(linktype, quadro):
    if linktype == 1:                               # Ethernet
        if len(quadro) < 14 or struct.unpack_from(">H", quadro, 12)[0] != 0x0800:
            return None
        ip = quadro[14:]
    elif linktype == 0:                             # BSD loopback
        ip = quadro[4:]
    elif linktype == 101:                           # RAW
        ip = quadro
    else:
        return None
    if not ip or (ip[0] >> 4) != 4 or ip[9] != 6:
        return None
    ihl = (ip[0] & 0xF) * 4
    total = struct.unpack_from(">H", ip, 2)[0]
    src, dst = ip[12:16], ip[16:20]
    tcp = ip[ihl:total]
    if len(tcp) < 20:
        return None
    sport, dport = struct.unpack_from(">HH", tcp, 0)
    seq = struct.unpack_from(">I", tcp, 4)[0]
    off = (tcp[12] >> 4) * 4
    return (src, sport, dst, dport, seq, tcp[off:])


def fluxos(caminho, porta, com_tempo=False):
    """Reassembla por (origem, destino), ordenando por numero de sequencia.

    Com `com_tempo`, o valor de cada fluxo vira `(bytes, marcos)`, onde `marcos` e uma lista de
    `(offset no fluxo, timestamp)` -- um por segmento TCP. E dai que sai o instante de cada
    pacote: o timestamp do segmento em que ele comeca.
    """
    pedacos = defaultdict(dict)
    for linktype, quadro, ts in blocos(caminho):
        t = tcp_de(linktype, quadro)
        if not t:
            continue
        src, sport, dst, dport, seq, carga = t
        if not carga or porta not in (sport, dport):
            continue
        pedacos[(src, sport, dst, dport)].setdefault(seq, (carga, ts))
    saida = {}
    for chave, partes in pedacos.items():
        fluxo, marcos = bytearray(), []
        for seq in sorted(partes):
            carga, ts = partes[seq]
            marcos.append((len(fluxo), ts))
            fluxo += carga
        saida[chave] = (bytes(fluxo), marcos) if com_tempo else bytes(fluxo)
    return saida


def tempo_de(marcos, offset):
    """O timestamp do segmento que contem `offset`."""
    import bisect

    i = bisect.bisect_right([o for o, _ in marcos], offset) - 1
    return marcos[max(i, 0)][1] if marcos else 0


# ---------------------------------------------------------------- pacotes

def separa(fluxo, cifra, do_servidor, marcos=None, base=0):
    """Devolve (opcode, payload, checksum_fecha) para cada pacote do fluxo.

    Com `marcos` (de `fluxos(..., com_tempo=True)`), acumula em `separa.tempos` o instante de cada
    pacote, na mesma ordem da lista devolvida. `base` e o offset do primeiro byte de `fluxo`
    dentro do fluxo original -- o lado do servidor comeca depois do S_KEY de 11 bytes.
    """
    saida, off, tempos = [], 0, []
    while off + 2 <= len(fluxo):
        ln = struct.unpack_from("<H", fluxo, off)[0]
        if ln < 7 or off + ln > len(fluxo):
            break
        corpo = cifra.decrypt(fluxo[off + 2: off + ln])
        op, _srv, chk = struct.unpack_from("<HBH", corpo, 0)
        fecha = chk == (~op & 0xFFFF)
        decodificado = opcode_servidor(op) if do_servidor else opcode_cliente(op)
        saida.append((decodificado, corpo[5:], fecha))
        if marcos is not None:
            tempos.append(tempo_de(marcos, base + off))
        off += ln
    separa.tempos = tempos
    return saida


def abre(caminho, porta=7777):
    """Abre a captura e devolve os dois lados ja decifrados.

    As chaves `tempo_servidor` e `tempo_cliente` trazem o instante de cada pacote, na mesma ordem
    das listas -- e o que permite intercalar os dois lados e rodar a correlacao pedido/resposta.
    """
    todos = fluxos(caminho, porta, com_tempo=True)
    for chave, (fluxo, marcos) in todos.items():
        src, sport, dst, dport, = chave
        if sport != porta or len(fluxo) < 11:
            continue                                 # queremos o lado do servidor primeiro
        ln = struct.unpack_from("<H", fluxo, 0)[0]
        if ln != 11:
            continue
        seed = struct.unpack_from("<I", fluxo, 7)[0]
        volta, marcos_volta = todos.get((dst, dport, src, sport), (b"", []))
        servidor = separa(fluxo[11:], Cifra(seed), True, marcos, base=11)
        tempo_servidor = separa.tempos
        cliente = separa(volta, Cifra(seed), False, marcos_volta)
        tempo_cliente = separa.tempos
        return {
            "seed": seed,
            "servidor": servidor,
            "cliente": cliente,
            "tempo_servidor": tempo_servidor,
            "tempo_cliente": tempo_cliente,
        }
    return None


BYTE_DE_SERVIDOR = {True: 101, False: 111}     # corpo[2], constante em cada direcao


class CifraDaChave(Cifra):
    """Cifra que comeca de uma chave de 8 bytes ja conhecida, sem seed."""

    def __init__(self, chave):
        self.key = bytearray(struct.pack("<Q", chave))


def chave_sem_skey(fluxo, do_servidor, amostra=3000):
    """Chave de uma direcao cuja captura comecou com a sessao ja aberta (sem o S_KEY).

    Por byte do primeiro corpo: `corpo[2]` e constante (101 no servidor, 111 no cliente), o que da o k2;
    os bytes 4-7 nascem `A1 6C 54 87` (so somam o tamanho dos corpos, entao A2 cobre o vai-um); o
    checksum `!opcode` da o k1 e amarra o k3 ao k0. Sobram 256 valores de k0 por byte alto, e cada um e
    conferido nos `amostra` primeiros pacotes com a chave avancando. Empate (sessao curta) desempata pelo
    opcode <= 0x2FF. Devolve None se nenhum candidato fecha tudo.
    """
    corpos, off = [], 0
    while off + 2 <= len(fluxo) and len(corpos) < amostra:
        ln = struct.unpack_from("<H", fluxo, off)[0]
        if ln < 7 or off + ln > len(fluxo):
            return None
        corpos.append(fluxo[off + 2: off + ln])
        off += ln
    if not corpos:
        return None
    esperado, c, S = BYTE_DE_SERVIDOR[do_servidor], corpos[0], STATIC_KEY
    k2 = c[2] ^ S[2] ^ c[1] ^ esperado
    melhores = []
    for k4 in (0xA1, 0xA2):
        k1 = c[1] ^ S[1] ^ c[0] ^ (~(c[4] ^ k4 ^ S[4] ^ c[3]) & 0xFF)
        for k0 in range(256):
            k3 = c[3] ^ S[3] ^ c[2] ^ (~(c[0] ^ k0) & 0xFF)
            chave = struct.unpack("<Q", bytes([k0, k1, k2, k3, k4, 0x6C, 0x54, 0x87]))[0]
            atual, fecham, opcodes_ok = chave, 0, 0
            for b in corpos:
                kb = struct.pack("<Q", atual)
                p0 = b[0] ^ kb[0]
                p1, p2, p3, p4 = (b[i] ^ kb[i] ^ S[i] ^ b[i - 1] for i in range(1, 5))
                op = p0 | p1 << 8
                if (p3 | p4 << 8) == (~op & 0xFFFF) and p2 == esperado:
                    fecham += 1
                    decod = opcode_servidor(op) if do_servidor else opcode_cliente(op)
                    opcodes_ok += decod <= 0x2FF
                atual = (atual + len(b)) & 0xFFFFFFFFFFFFFFFF
            if fecham == len(corpos):
                melhores.append((opcodes_ok, chave))
    if not melhores:
        return None
    melhores.sort(reverse=True)
    return melhores[0][1]


def abre_todas(caminho, porta=7777, sem_skey=False):
    """Toda sessao de jogo da captura, nao so a primeira.

    Uma subida de nivel 1 ao 60 nao cabe num login so: cada reconexao abre um TCP novo, com o seu
    proprio S_KEY e a sua propria chave. O [`abre`] devolve a primeira e para -- de onde vem o
    risco de analisar 20 minutos de uma sessao de doze horas sem perceber. O censo usa esta.

    Com `sem_skey`, a sessao que a captura pegou ja aberta tambem entra: a chave de cada direcao sai
    de [`chave_sem_skey`], e a sessao vem com `"seed": None`.
    """
    todos = fluxos(caminho, porta, com_tempo=True)
    sessoes = []
    for chave, (fluxo, marcos) in todos.items():
        src, sport, dst, dport = chave
        if sport != porta or len(fluxo) < 11:
            continue
        volta, marcos_volta = todos.get((dst, dport, src, sport), (b"", []))
        if struct.unpack_from("<H", fluxo, 0)[0] == 11:
            seed = struct.unpack_from("<I", fluxo, 7)[0]
            servidor = separa(fluxo[11:], Cifra(seed), True, marcos, base=11)
            tempo_servidor = separa.tempos
            cliente = separa(volta, Cifra(seed), False, marcos_volta)
            tempo_cliente = separa.tempos
        elif sem_skey:
            seed, k_srv = None, chave_sem_skey(fluxo, True)
            if k_srv is None:
                continue
            servidor = separa(fluxo, CifraDaChave(k_srv), True, marcos)
            tempo_servidor = separa.tempos
            k_cli = chave_sem_skey(volta, False) if volta else None
            cliente = separa(volta, CifraDaChave(k_cli), False, marcos_volta) if k_cli is not None else []
            tempo_cliente = separa.tempos if k_cli is not None else []
        else:
            continue
        sessoes.append({
            "seed": seed,
            "servidor": servidor,
            "cliente": cliente,
            "tempo_servidor": tempo_servidor,
            "tempo_cliente": tempo_cliente,
        })
    return sessoes


def intercalado(r):
    """Os dois lados numa linha do tempo so: `(tempo, lado, opcode, payload)`.

    Empate de timestamp desempata pelo cliente primeiro -- um pedido e a resposta dele costumam
    cair no mesmo microssegundo de captura, e a resposta nao pode vir antes.
    """
    linha = [(t, 0, "cliente", op, p) for (op, p, f), t in zip(r["cliente"], r["tempo_cliente"]) if f]
    linha += [(t, 1, "servidor", op, p) for (op, p, f), t in zip(r["servidor"], r["tempo_servidor"]) if f]
    linha.sort(key=lambda x: (x[0], x[1]))
    return [(t, lado, op, p) for t, _, lado, op, p in linha]


# ---------------------------------------------------------------- censo

TABELA_RUST = "Emulador-Rust/game-server/src/message/client.rs"


def nomes_do_client_rs(raiz="."):
    """Le a tabela de opcodes de cliente do nosso `client.rs`.

    A tabela e uma lista de `(NOME, Tipo, 0xNN),`. Devolve `{opcode: nome}`; se o arquivo nao
    estiver la, devolve vazio e o censo sai sem a coluna de nome.
    """
    import os
    import re

    caminho = os.path.join(raiz, TABELA_RUST)
    if not os.path.exists(caminho):
        return {}
    with open(caminho, encoding="utf-8", errors="replace") as f:
        texto = f.read()
    achados = re.findall(r"\(\s*([A-Z0-9_]+)\s*,\s*(\w+)\s*,\s*(0x[0-9A-Fa-f]+)\s*\)", texto)
    return {int(op, 16): nome for nome, _tipo, op in achados}


def censo_de_opcodes(r, nomes=None):
    """Todo opcode que o cliente manda na captura, com quantas vezes e de que tamanho.

    E o inverso do que os nossos logs dao: aqui a lista e do que o cliente **realmente** manda
    numa sessao oficial, entao um handler nosso que nao aparece aqui esta sentado num opcode que
    o cliente nao usa. Tamanho do corpo tambem entra -- e o primeiro filtro para descartar um
    palpite de nome (ver o metodo em `capturas-aion-classic`).
    """
    nomes = nomes or {}
    sessoes = r if isinstance(r, list) else [r]
    vezes, tamanhos = defaultdict(int), defaultdict(set)
    for sessao in sessoes:
        for op, payload, fecha in sessao["cliente"]:
            if not fecha:
                continue
            vezes[op] += 1
            tamanhos[op].add(len(payload))

    linhas = []
    for op in sorted(vezes, key=lambda o: (-vezes[o], o)):
        linhas.append((op, vezes[op], sorted(tamanhos[op]), nomes.get(op)))
    orfaos = [(op, nome) for op, nome in sorted(nomes.items()) if op not in vezes]
    return linhas, orfaos


def correlacao(r, janela_ms=300, amostras_de_fundo=4000, semente=13):
    """Para cada opcode de cliente, que resposta do servidor aparece depois dele.

    **Descontar o fundo nao e refinamento, e o que faz a analise funcionar.** `MOVE_NEW` e 40% do
    trafego do cliente e `S_MOVE_NEW` e 43% do do servidor: os dois aparecem perto de qualquer
    coisa. O numero que vale e o `lift` -- quantas vezes a resposta e mais provavel depois do
    pedido do que numa janela qualquer da sessao.

    Roda as **duas direcoes**, que e a regra: um par so serve de ancora se o pedido puxa a resposta
    E a resposta e precedida pelo pedido, as duas com lift alto. Ver o cabecalho de
    `message/client.rs`.

    Devolve `{opcode_cliente: [(lift_ida, opcode_servidor, p_ida, p_fundo, lift_volta), ...]}`.
    """
    import bisect
    import random

    jan = janela_ms * 1_000_000
    tl = intercalado(r)
    srv = [(t, op) for t, lado, op, _ in tl if lado == "servidor"]
    cli = [(t, op) for t, lado, op, _ in tl if lado == "cliente"]
    if not srv or not cli:
        return {}
    ts_srv = [t for t, _ in srv]
    ts_cli = [t for t, _ in cli]

    def depois(t0):
        i = bisect.bisect_right(ts_srv, t0)
        j = bisect.bisect_right(ts_srv, t0 + jan)
        return {op for _, op in srv[i:j]}

    def antes(t0):
        i = bisect.bisect_left(ts_cli, t0 - jan)
        j = bisect.bisect_right(ts_cli, t0)
        return {op for _, op in cli[i:j]}

    rnd = random.Random(semente)
    fundo_srv, fundo_cli = defaultdict(int), defaultdict(int)
    lo, hi = ts_srv[0], ts_srv[-1] - jan
    for _ in range(amostras_de_fundo):
        t = rnd.randint(lo, max(hi, lo + 1))
        for op in depois(t):
            fundo_srv[op] += 1
        for op in antes(t):
            fundo_cli[op] += 1

    n_cli, n_srv = defaultdict(int), defaultdict(int)
    for _, op in cli:
        n_cli[op] += 1
    for _, op in srv:
        n_srv[op] += 1

    # volta: para cada resposta, com que frequencia cada pedido a precede
    volta = defaultdict(lambda: defaultdict(int))
    for t, s in srv:
        for c in antes(t):
            volta[s][c] += 1

    saida = {}
    for c in sorted(n_cli):
        vistos = defaultdict(int)
        for t, op in cli:
            if op != c:
                continue
            for s in depois(t):
                vistos[s] += 1
        linhas = []
        for s, k in vistos.items():
            p_ida = k / n_cli[c]
            p_fundo = fundo_srv[s] / amostras_de_fundo
            if p_ida < 0.25:
                continue
            lift_ida = p_ida / max(p_fundo, 1e-4)
            if lift_ida < 5:
                continue
            p_volta = volta[s][c] / max(n_srv[s], 1)
            lift_volta = p_volta / max(fundo_cli[c] / amostras_de_fundo, 1e-4)
            linhas.append((lift_ida, s, p_ida, p_fundo, lift_volta))
        linhas.sort(reverse=True)
        if linhas:
            saida[c] = linhas
    return saida


def salva_censo(caminho, linhas, meta):
    """Grava o censo num JSON, para servir de linha de base contra uma captura futura."""
    import json

    dados = {
        "sobre": meta,
        "opcodes": {
            "0x{:04X}".format(op): {"vezes": n, "tamanhos": ts, "nome": nome}
            for op, n, ts, nome in linhas
        },
    }
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write(chr(10))


def compara_censo(caminho, linhas):
    """Confere o censo desta captura contra uma linha de base de outra versao do cliente.

    E o teste que responde "os opcodes sobreviveram ao patch?". Um opcode que aparece nas duas
    capturas **com um tamanho de corpo em comum** e o mesmo pacote: bater numero e forma e
    coincidencia dificil, e isso conta como confirmacao.

    **A volta nao vale.** Tamanho que nao bate NAO prova que o numero andou -- prova so que
    aquele pacote nao apareceu com o mesmo corpo. Muito pacote tem corpo de tamanho variavel:
    o `CHECK_NICKNAME` deu 26 bytes com "Teiteiteitei" e 16 com "Jhujhyn", que e a mesma
    estrutura com um nome mais curto (28/08/2026). Por isso essa lista se chama **conferir**, e
    nao "mudou" -- ela aponta onde olhar, nao o que concluir. Quem estava com varios tamanhos ja
    na base vai marcado, que ai o sinal e ainda mais fraco.

    Cuidado que vale para os dois lados: **ausencia nao e prova de erro**. Se ninguem apagou
    personagem na sessao, `DELETE_CHARACTER` nao aparece, e isso nao diz nada sobre o numero
    dele. So o que aparece nas duas conta como confirmacao.
    """
    import json

    with open(caminho, encoding="utf-8") as f:
        base = json.load(f)
    antes = {int(k, 16): v for k, v in base["opcodes"].items()}
    agora = {op: {"vezes": n, "tamanhos": ts, "nome": nome} for op, n, ts, nome in linhas}

    iguais, conferir, sumiram, novos = [], [], [], []
    for op in sorted(set(antes) | set(agora)):
        a, b = antes.get(op), agora.get(op)
        if a and b:
            if set(a["tamanhos"]) & set(b["tamanhos"]):
                iguais.append((op, a, b))
            else:
                conferir.append((op, a, b))
        elif a:
            sumiram.append((op, a))
        else:
            novos.append((op, b))
    return base.get("sobre", {}), iguais, conferir, sumiram, novos


if __name__ == "__main__":
    modo_censo = "--opcodes" in sys.argv[1:]
    modo_corr = "--correlacao" in sys.argv[1:]
    salvar = compara = None
    argv = sys.argv[1:]
    for chave in ("--censo-salva", "--censo-compara"):
        if chave in argv:
            i = argv.index(chave)
            if i + 1 >= len(argv):
                print("{} precisa do caminho do arquivo".format(chave))
                sys.exit(2)
            valor = argv[i + 1]
            if chave == "--censo-salva":
                salvar = valor
            else:
                compara = valor
            del argv[i:i + 2]
    args = [a for a in argv if not a.startswith("--")]
    if salvar or compara:
        modo_censo = True
    if not args:
        print("uso: aion_pcap.py <captura.pcapng> [raiz] [--opcodes] [--correlacao]")
        print("     --censo-salva <arquivo.json>     grava a linha de base desta captura")
        print("     --censo-compara <arquivo.json>   confere esta captura contra a linha de base")
        sys.exit(2)

    r = abre(args[0])
    if not r:
        print("nao achei o S_KEY de 11 bytes na porta 7777")
        sys.exit(1)
    print(f"seed = 0x{r['seed']:08X}")
    for lado in ("servidor", "cliente"):
        ps = r[lado]
        ok = sum(1 for _, _, f in ps if f)
        print(f"{lado:9} {len(ps):5} pacotes, checksum fecha em {ok} ({ok*100//max(len(ps),1)}%)")

    if modo_corr:
        nomes = nomes_do_client_rs(args[1] if len(args) > 1 else ".")
        print("\n=== correlacao pedido -> resposta (janela de 300ms, fundo descontado) ===")
        print("um par so vale como ancora se as DUAS direcoes tiverem lift alto\n")
        for c, linhas in correlacao(r).items():
            print(f"cliente 0x{c:03X}  {nomes.get(c, '-- sem nome --')}")
            for lift, s, p_ida, p_fundo, lift_volta in linhas[:4]:
                print(
                    f"    -> servidor 0x{s:03X}   ida {p_ida * 100:5.1f}% (fundo {p_fundo * 100:4.1f}%, "
                    f"lift {lift:6.1f}x)   volta lift {lift_volta:6.1f}x"
                )

    if modo_censo:
        nomes = nomes_do_client_rs(args[1] if len(args) > 1 else ".")
        sessoes = abre_todas(args[0])
        if len(sessoes) > 1:
            total = sum(len(x["cliente"]) for x in sessoes)
            print()
            print("{} sessoes de jogo na captura, {} pacotes de cliente somados".format(
                len(sessoes), total))
        linhas, orfaos = censo_de_opcodes(sessoes or r, nomes)
        print(f"\n=== opcodes que o cliente manda ({len(linhas)} distintos) ===")
        print("opcode  vezes  tamanhos                 nome no client.rs")
        for op, n, ts, nome in linhas:
            t = ",".join(str(x) for x in ts)
            print(f" 0x{op:03X}  {n:5}  {t[:24]:24} {nome or '-- sem nome --'}")
        if nomes:
            print(f"\n=== handlers nossos que o cliente nunca manda aqui ({len(orfaos)} de {len(nomes)}) ===")
            for op, nome in orfaos:
                print(f" 0x{op:03X}  {nome}")

        if salvar:
            salva_censo(
                salvar,
                linhas,
                {
                    "captura": os.path.basename(args[0]),
                    "seed": "0x{:08X}".format(r["seed"]),
                    "pacotes_do_cliente": len(r["cliente"]),
                    "opcodes_distintos": len(linhas),
                },
            )
            print()
            print("linha de base gravada em {}".format(salvar))

        if compara:
            sobre, iguais, conferir, sumiram, novos = compara_censo(compara, linhas)
            print()
            print("=== esta captura contra {} ===".format(os.path.basename(compara)))
            if sobre:
                print("   base: {} ({} opcodes distintos)".format(
                    sobre.get("captura", "?"), sobre.get("opcodes_distintos", "?")))
            print("   confirmados (mesmo numero e mesma forma) : {:>4}".format(len(iguais)))
            print("   mesmo numero, corpo de outro tamanho     : {:>4}   (conferir)".format(len(conferir)))
            print("   estavam na base e nao apareceram         : {:>4}".format(len(sumiram)))
            print("   apareceram e nao estavam na base         : {:>4}".format(len(novos)))
            if conferir:
                print()
                print("   -- corpo de outro tamanho: OLHAR, nao concluir --")
                print("      corpo variavel explica a maioria; so vira renumeracao se a estrutura nao fechar")
                for op, a, b in conferir:
                    marca = "  [ja era variavel na base]" if len(a["tamanhos"]) > 1 else ""
                    print("      0x{:03X}  {:<22} base {} -> agora {}{}".format(
                        op, a.get("nome") or b.get("nome") or "-- sem nome --",
                        a["tamanhos"], b["tamanhos"], marca))
            if novos:
                print()
                print("   -- opcodes novos (podem ser pacotes que a sessao antiga nao exercitou) --")
                for op, b in novos:
                    print("      0x{:03X}  {:>5}x  tamanhos {}  {}".format(
                        op, b["vezes"], b["tamanhos"], b.get("nome") or "-- sem nome --"))
            if sumiram:
                print()
                print("   -- estavam na base e sumiram (ausencia NAO e prova de erro) --")
                for op, a in sumiram:
                    print("      0x{:03X}  {:>5}x  tamanhos {}  {}".format(
                        op, a["vezes"], a["tamanhos"], a.get("nome") or "-- sem nome --"))
            print()
            # O veredito pesa a evidencia positiva contra a duvida. Uma discordancia de tamanho
            # sozinha nunca derruba dezenas de confirmacoes -- corpo variavel e comum demais.
            if len(iguais) >= 10 and not conferir:
                print("   VEREDITO: {} opcodes bateram numero e forma, nenhum destoou.".format(len(iguais)))
                print("   A numeracao segue de pe.")
            elif len(iguais) >= 10 * max(len(conferir), 1):
                print("   VEREDITO: {} opcodes bateram numero e forma contra {} a conferir.".format(
                    len(iguais), len(conferir)))
                print("   A numeracao segue de pe; abrir os poucos de tamanho diferente um a um.")
            elif iguais:
                print("   VEREDITO: {} confirmados e {} destoando -- proporcao ruim demais para".format(
                    len(iguais), len(conferir)))
                print("   afirmar qualquer coisa. Abrir os payloads antes de concluir.")
            else:
                print("   VEREDITO: nenhum opcode conhecido bateu. A numeracao ANDOU.")

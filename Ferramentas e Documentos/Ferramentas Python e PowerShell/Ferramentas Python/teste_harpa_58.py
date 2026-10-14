"""Teste de formato: poe uma harpa do Live 5.8 no cliente Classic 5.0 como item novo.

O que faz:

1. **Cliente** -- em todo `.pak` que tem `client_items.xml`, acrescenta um `client_item` novo
   (clone de um item de teste existente, com `id`, `name` e `mesh` trocados). O XML binario nao e
   decodificado e recodificado inteiro: as strings novas entram no fim da tabela (os indices
   antigos nao mudam), o elemento novo e inserido na posicao do id e o contador de filhos da raiz
   sobe 1.
2. **Cliente** -- acrescenta a mesh `.cgf` e as texturas `.dds` da harpa nos paks de
   `objects\\items`.
3. **Servidor** -- acrescenta o `item_template` do mesmo id (clone do mesmo item) no
   `item_templates.xml` do Codigo Fonte e do Produto Final.

Todo `.pak` alterado ganha uma copia `<nome>.bak_harpa58` antes da primeira gravacao.

Uso:

    python teste_harpa_58.py              aplica o item, a mesh e as texturas
    python teste_harpa_58.py --animacao   poe as animacoes de harpa no LM e as declara no lm.cal
    python teste_harpa_58.py --dedos-posicao   regrava as animacoes trocando so a posicao dos dedos
    python teste_harpa_58.py --dedos-variante posicao|posicao+rotacao   troca a variante instalada
    python teste_harpa_58.py --efeito     traz do 5.8 o projetil do ataque basico (a nota musical)
    python teste_harpa_58.py --componente lista|marcadores|animacoes|sons|itens|dll original|harpa
                                               desliga ou religa uma peca, para isolar um defeito
    python teste_harpa_58.py --marcadores copia do 5.8 os marcadores e sons das animacoes de harpa
    python teste_harpa_58.py --strings    nome do tipo de arma (STR_TOOLTIP_HARP) nas linguas do cliente
    python teste_harpa_58.py --desfaz   restaura os paks e tira o template do servidor
"""
import math
import os
import re
import shutil
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aion_pak  # noqa: E402

CLIENTE = r"G:\ClaudeProject\Client\aionclassic"
REPO = r"G:\Projetos AION\Classic"
#: Cliente Live 5.8 limpo: todos os paks abrem com o `aion_pak`. (O instalado em
#: `G:\Aion Riftshade` guarda `Objects` e `Sounds` em `~aionpatch_*.pak`, com outro embaralhamento
#: e um deflate que nao e o do zlib -- esses nao abrem.)
LIVE_CLIENTE = r"C:\Users\Sclepius\Downloads\Aion 5.8 Europe"

#: (id-base, id novo, nome interno, mesh, nome no servidor). A base e um orbe de teste que existe
#: no cliente e no servidor; o clone troca o `weapon_type` para `2h_harp`, o tipo 19 que o hook
#: `harp_fix.h` do version.dll ensina ao `Game.dll`. Sem o hook o cliente le o nome como tipo 0.
#: A mesh e o icone sao os da "Harp for Practice" do Live (id 102000206, `harp_d_n_c1_01a`).
VARIANTES = (
    (100500003, 100599901, "test_harp_58_01", "HA_C001", "Harpa de Teste 5.8"),
)
TIPO_DE_ARMA = "2h_harp"
ICONE = "Icon_Item_Harp_C01"
#: Ataque basico da harpa, com os valores do `client_item` 102000206 do Live: a distancia, 25 m,
#: 2,4 s, agua. No servidor o alcance vai em milimetros.
ATAQUE_CLIENTE = {"attack_range": "25.000000", "attack_delay": "2400", "attack_type": "magical_water"}
#: O projetil do ataque basico, a nota musical. O efeito e as particulas dele nao existem no 5.0:
#: `--efeito` os traz do 5.8 (ver `aion_fx.py`).
PROJETIL = {"ammo_bone": "Lhand_bone", "ammo_fx": "fc_sys_hit.harp.ammo", "ammo_speed": "18"}
PAK_EFEITOS = r"Effects\Effects_Meshes.pak"
PRT_DO_PROJETIL = "prt/sys_hit.prt"
FXC_DO_PROJETIL = "fxc/fc_sys_hit.fxc"
INDICE_PRT = "prt/namelist_prt.index"
INDICE_FXC = "fxc/namelist_fxc.index"
PAK_SOM_DO_PROJETIL = r"sounds\effect\artist\artist.pak"
ATAQUE_SERVIDOR = {"attack_range": "25000", "attack_speed": "2400", "attack_type": "MAGICAL_WATER"}
#: Itens de tentativas anteriores (harpa como livro e como lamina em corrente): saem do servidor.
IDS_ANTIGOS = (100699901, 102499901)
#: Efeitos de brilho do orbe: ficam de fora para a mesh aparecer limpa.
TIRA_FILHOS = ("item_fx", "combat_item_fx")

PAKS_DE_ITENS = (
    r"data\items\items.pak",
    r"data\items\special\special.pak",
    r"data\items\special2\special2.pak",
    r"data\europe\Items\Items.pak",
)
PAK_MESH = r"objects\items\Mesh_Meshes_024.pak"
PAK_TEXTURA = r"objects\items\Mesh_Textures_047.pak"
#: Arquivos trazidos de `Objects\items` do 5.8. A `Ha_test_stick` e a varinha que o 5.8 usa
#: quando a harpa nao tem `<mesh>_stick.cgf` propria.
MESHES = ("HA_C001.cgf", "Ha_test_stick.cgf")
TEXTURAS = (
    "HA_C001.dds", "HA_C001_ddn.dds", "HA_C001_illum.dds", "HA_C001_matid.dds", "HA_C001_sp.dds",
    "Ha_test_stick.dds", "Ha_test_stick_ddn.dds", "Ha_test_stick_illum.dds",
    "Ha_test_stick_matid.dds", "Ha_test_stick_sp.dds",
)
TEMPLATES = (
    r"Código Fonte - Emulador\game-server\data\static_data\items\item_templates.xml",
    r"Emulador - Produto Final\GameServer\data\static_data\items\item_templates.xml",
)
SUFIXO_BACKUP = ".bak_harpa58"
PASTA_ANIMACAO = r"objects\pc\lm\animation"
#: Pak que recebe os `.caf` de harpa, e o que guarda a lista de animacoes do personagem.
PAK_ANIMACAO = r"objects\pc\lm\animation\Animation_Animations_020.pak"
PAK_CAL = r"objects\pc\lm\mesh\Mesh_Meshes_000.pak"
#: A mesma lista em binario cifrado (`lm.cab`): e a que o cliente usa depois de conectar ao
#: servidor (ver `aion_cab.py`). O `lm.cal` so vale antes disso.
PAK_CAB = r"objects\pc\lm\mesh\Mesh_Meshes_044.pak"
#: Animacoes que dao a mao relaxada (`nidle`) em cada esqueleto, para converter os dedos.
REPOUSO_58 = "LM_Cdraw_harp_001.caf"
REPOUSO_50 = "lm_nidle_001_loop.caf"
PAK_MARCADORES =r"data\AnimationMarkers\AnimationMarkers.pak"
PAK_SONS = r"sounds\motion\motion.pak"
LIVE_ANIMACAO =r"G:\Projetos AION\Classic\Classes_Live_5.8\2_Bard_Songweaver\Bard_PC_Animations"


# --------------------------------------------------------------------------------------------
# XML binario
# --------------------------------------------------------------------------------------------

def _varint(b, o):
    valor = desloc = 0
    while True:
        byte = b[o]
        o += 1
        valor |= (byte & 0x7F) << desloc
        if byte < 0x80:
            return valor, o
        desloc += 7


def _grava_varint(v):
    saida = bytearray()
    while True:
        byte = v & 0x7F
        v >>= 7
        if v:
            saida.append(byte | 0x80)
        else:
            saida.append(byte)
            return bytes(saida)


def _le_elemento(b, o):
    """Le um elemento inteiro para `(nome, texto|None, atributos, filhos)` e devolve o fim."""
    nome, o = _varint(b, o)
    flags, o = _varint(b, o)
    if flags > 7:
        raise ValueError(f"flags desconhecidas {flags} em {o}")
    texto = None
    if flags & 1:
        texto, o = _varint(b, o)
    atributos = []
    if flags & 2:
        n, o = _varint(b, o)
        for _ in range(n):
            k, o = _varint(b, o)
            v, o = _varint(b, o)
            atributos.append((k, v))
    filhos = []
    if flags & 4:
        n, o = _varint(b, o)
        for _ in range(n):
            f, o = _le_elemento(b, o)
            filhos.append(f)
    return (nome, texto, atributos, filhos), o


def _grava_elemento(e):
    nome, texto, atributos, filhos = e
    flags = (1 if texto is not None else 0) | (2 if atributos else 0) | (4 if filhos else 0)
    s = bytearray(_grava_varint(nome) + _grava_varint(flags))
    if texto is not None:
        s += _grava_varint(texto)
    if atributos:
        s += _grava_varint(len(atributos))
        for k, v in atributos:
            s += _grava_varint(k) + _grava_varint(v)
    if filhos:
        s += _grava_varint(len(filhos))
        for f in filhos:
            s += _grava_elemento(f)
    return bytes(s)


class _Tabela:
    def __init__(self, bruto):
        if len(bruto) % 2 or bruto[-2:] != b"\0\0":
            raise ValueError("tabela de strings nao termina em zero")
        self.bruto = bytearray(bruto)
        self.unidades = memoryview(bytes(bruto)).cast("H")

    def texto(self, i):
        fim = i
        while self.unidades[fim]:
            fim += 1
        return bytes(self.unidades[i:fim]).decode("utf-16le")

    def acrescenta(self, s):
        i = len(self.bruto) // 2
        self.bruto += s.encode("utf-16le") + b"\0\0"
        return i


def acrescenta_item(bxml, id_base, id_novo, nome_novo, mesh):
    """Devolve o `client_items.xml` binario com o item novo, e o texto do item clonado."""
    if bxml[0] != 0x80:
        raise ValueError("nao e XML binario")
    tam, o = _varint(bxml, 1)
    tab = _Tabela(bxml[o:o + tam])
    o += tam

    # Cabecalho da raiz: nome, flags e contador de filhos.
    ini_raiz = o
    _nome, o = _varint(bxml, o)
    flags, o = _varint(bxml, o)
    if flags != 4:
        raise ValueError(f"raiz com flags {flags}, esperava so filhos")
    pos_contador = o
    quantos, o = _varint(bxml, o)

    base = None
    ids = []
    posicoes = []
    for _ in range(quantos):
        posicoes.append(o)
        item, o = _le_elemento(bxml, o)
        id_item = None
        for nome, texto, _a, _f in item[3]:
            if tab.texto(nome) == "id":
                id_item = int(tab.texto(texto))
                break
        ids.append(id_item)
        if id_item == id_base:
            base = item
        if id_item == id_novo:
            raise ValueError(f"o id {id_novo} ja existe neste arquivo")
    if o != len(bxml):
        raise ValueError(f"sobraram {len(bxml) - o} bytes depois da raiz")
    if base is None:
        raise ValueError(f"item-base {id_base} nao encontrado")

    troca = {"id": str(id_novo), "name": nome_novo, "desc": DESC_DO_ITEM, "mesh": mesh,
             "weapon_type": TIPO_DE_ARMA,
             "icon_name": ICONE, **ATAQUE_CLIENTE}
    filhos = []
    for nome, texto, atributos, netos in base[3]:
        n = tab.texto(nome)
        if n in TIRA_FILHOS:
            continue
        if n in troca:
            texto = tab.acrescenta(troca[n])
        filhos.append((nome, texto, atributos, netos))
        if n == "material":
            # O projetil vem logo depois de <material>, como nos itens que ja tem um.
            for campo, valor in PROJETIL.items():
                filhos.append((tab.acrescenta(campo), tab.acrescenta(valor), [], []))
    novo = (base[0], base[1], base[2], filhos)

    # Mantem a ordem por id quando o arquivo esta ordenado; senao vai para o fim.
    ordenado = all(a <= b for a, b in zip(ids, ids[1:]))
    corte = len(bxml)
    if ordenado:
        for pos, id_item in zip(posicoes, ids):
            if id_item > id_novo:
                corte = pos
                break

    saida = bytearray([0x80])
    saida += _grava_varint(len(tab.bruto)) + tab.bruto
    saida += bxml[ini_raiz:pos_contador] + _grava_varint(quantos + 1)
    saida += bxml[pos_contador + len(_grava_varint(quantos)):corte]
    saida += _grava_elemento(novo)
    saida += bxml[corte:]
    return bytes(saida), quantos, ordenado


def acrescenta_filhos(bxml, novos):
    """Acrescenta elementos (`xml.etree` Element) no fim dos filhos da raiz de um XML binario.

    Como em [`acrescenta_item`], o que ja existe nao e recodificado: as strings novas vao para o
    fim da tabela e so o contador de filhos da raiz muda.
    """
    if bxml[0] != 0x80:
        raise ValueError("nao e XML binario")
    tam, o = _varint(bxml, 1)
    tab = _Tabela(bxml[o:o + tam])
    o += tam
    ini_raiz = o
    _nome, o = _varint(bxml, o)
    flags, o = _varint(bxml, o)
    if flags != 4:
        raise ValueError(f"raiz com flags {flags}, esperava so filhos")
    pos_contador = o
    quantos, o = _varint(bxml, o)

    # Indice (em unidades de 16 bits) de cada string que a tabela ja tem.
    indice, pos = {}, 0
    for parte in bytes(tab.bruto).decode("utf-16le").split("\0")[:-1]:
        indice.setdefault(parte, pos)
        pos += len(parte.encode("utf-16le")) // 2 + 1

    def idx(s):
        if s not in indice:
            indice[s] = tab.acrescenta(s)
        return indice[s]

    def converte(el):
        texto = el.text.strip() if el.text and el.text.strip() else None
        return (
            idx(el.tag),
            idx(texto) if texto is not None else None,
            [(idx(k), idx(v)) for k, v in el.attrib.items()],
            [converte(f) for f in el],
        )

    codificados = b"".join(_grava_elemento(converte(el)) for el in novos)
    saida = bytearray([0x80])
    saida += _grava_varint(len(tab.bruto)) + tab.bruto
    saida += bxml[ini_raiz:pos_contador] + _grava_varint(quantos + len(novos))
    saida += bxml[pos_contador + len(_grava_varint(quantos)):]
    saida += codificados
    return bytes(saida), quantos


# --------------------------------------------------------------------------------------------
# Gravacao de pak
# --------------------------------------------------------------------------------------------

def _comprime(dados):
    c = zlib.compressobj(9, zlib.DEFLATED, -15)
    bruto = c.compress(dados) + c.flush()
    # O XOR do inicio e a propria inversa: a mesma funcao que decifra, cifra.
    return aion_pak.decifra_inicio(bruto)


def regrava_pak(caminho, troca=None, acrescenta=None):
    """Reescreve o pak trocando o conteudo de entradas existentes e acrescentando novas.

    As entradas que nao mudam sao copiadas byte a byte (cabecalho local e fluxo comprimido).
    """
    troca = {k.lower(): v for k, v in (troca or {}).items()}
    acrescenta = dict(acrescenta or {})
    with open(caminho, "rb") as f:
        d = f.read()

    fim = aion_pak._acha_fim_do_diretorio(d)
    quantas = struct.unpack_from("<H", d, fim + 10)[0]
    off_dir = struct.unpack_from("<I", d, fim + 16)[0]

    registros = []  # (nome, registro central, bytes locais)
    o = off_dir
    for _ in range(quantas):
        n_nome, n_extra, n_com = struct.unpack_from("<HHH", d, o + 28)
        central = bytearray(d[o:o + 46 + n_nome + n_extra + n_com])
        nome = d[o + 46:o + 46 + n_nome].decode("utf-8", "replace")
        tam_c = struct.unpack_from("<I", d, o + 20)[0]
        off_local = struct.unpack_from("<I", d, o + 42)[0]
        ln, le = struct.unpack_from("<HH", d, off_local + 26)
        cab = bytearray(d[off_local:off_local + 30 + ln + le])
        if struct.unpack_from("<H", cab, 6)[0] & 8:
            raise ValueError(f"{nome}: entrada com data descriptor, nao suportado")
        fluxo = d[off_local + 30 + ln + le:off_local + 30 + ln + le + tam_c]

        if nome.lower() in troca:
            dados = troca.pop(nome.lower())
            fluxo = _comprime(dados)
            campos = struct.pack("<III", zlib.crc32(dados) & 0xFFFFFFFF, len(fluxo), len(dados))
            struct.pack_into("<H", cab, 8, 8)
            struct.pack_into("<H", central, 10, 8)
            cab[14:26] = campos
            central[16:28] = campos
        if nome in acrescenta:
            raise ValueError(f"{nome} ja existe em {caminho}")
        registros.append((nome, central, bytes(cab) + fluxo))
        o += len(central)
    if troca:
        raise ValueError(f"entradas nao encontradas em {caminho}: {sorted(troca)}")

    # Entradas novas: o molde dos campos fixos sai da ultima entrada do pak.
    molde_central = registros[-1][1]
    for nome, dados in acrescenta.items():
        nome_b = nome.encode("utf-8")
        fluxo = _comprime(dados)
        campos = struct.pack("<III", zlib.crc32(dados) & 0xFFFFFFFF, len(fluxo), len(dados))
        central = bytearray(molde_central[:46]) + nome_b
        struct.pack_into("<H", central, 8, 0)      # flags
        struct.pack_into("<H", central, 10, 8)     # deflate
        central[16:28] = campos
        struct.pack_into("<HHH", central, 28, len(nome_b), 0, 0)
        cab = bytearray(aion_pak.CABECALHO_LOCAL + bytes(central[6:16]) + campos)
        cab += struct.pack("<HH", len(nome_b), 0) + nome_b
        registros.append((nome, central, bytes(cab) + fluxo))
    registros.sort(key=lambda r: r[0].lower())

    corpo = bytearray()
    diretorio = bytearray()
    for _nome, central, local in registros:
        struct.pack_into("<I", central, 42, len(corpo))
        corpo += local
        diretorio += central
    eocd = bytearray(d[fim:])
    struct.pack_into("<HH", eocd, 8, len(registros), len(registros))
    struct.pack_into("<II", eocd, 12, len(diretorio), len(corpo))

    tmp = caminho + ".tmp_harpa58"
    with open(tmp, "wb") as f:
        f.write(corpo + diretorio + eocd)
    os.replace(tmp, caminho)


def _backup(caminho):
    copia = caminho + SUFIXO_BACKUP
    if not os.path.exists(copia):
        shutil.copy2(caminho, copia)
    return copia


def _confere_pak(caminho, antes, esperado):
    """Reabre o pak gravado, confere a contagem e le de volta (com CRC) o que mudou."""
    d, idx = aion_pak.abre(caminho)
    if len(idx) != antes + len(esperado) - sum(1 for n in esperado if esperado[n] == "troca"):
        raise ValueError(f"{caminho}: {len(idx)} entradas, esperava outra contagem")
    por_nome = {e.nome.lower(): e for e in idx}
    for nome in esperado:
        aion_pak.le(d, por_nome[nome.lower()])
    # Amostra das entradas intocadas, para pegar offset errado no diretorio.
    for e in idx[::max(1, len(idx) // 40)]:
        aion_pak.le(d, e)


# --------------------------------------------------------------------------------------------
# Servidor
# --------------------------------------------------------------------------------------------

_BLOCO = r'[ \t]*<item_template id="%d".*?</item_template>\r?\n'


def acrescenta_template(caminho, id_base, id_novo, nome_novo, nome_pt):
    with open(caminho, "rb") as f:
        texto = f.read().decode("utf-8")
    if f'id="{id_novo}"' in texto:
        return "ja tinha"
    m = re.search(_BLOCO % id_base, texto, re.S)
    if not m:
        raise ValueError(f"{caminho}: template-base {id_base} nao encontrado")
    bloco = m.group(0)
    novo = bloco.replace(f'id="{id_base}"', f'id="{id_novo}"', 1)
    novo = re.sub(r'name_en="[^"]*"', f'name_en="Test Harp 5.8 ({nome_novo})"', novo, count=1)
    novo = re.sub(r'name_pt="[^"]*"', 'name_pt="%s"' % nome_pt, novo, count=1)
    novo = re.sub(r'cName="[^"]*"', f'cName="{nome_novo}"', novo, count=1)
    for atributo, valor in ATAQUE_SERVIDOR.items():
        novo, n = re.subn(r'\b%s="[^"]*"' % atributo, f'{atributo}="{valor}"', novo, count=1)
        if n != 1:
            raise ValueError(f"{caminho}: o template-base nao tem {atributo}")
    if novo.count(str(id_novo)) != 1 or nome_novo not in novo:
        raise ValueError(f"{caminho}: o clone do template nao saiu como esperado")
    texto = texto[:m.end()] + novo + texto[m.end():]
    with open(caminho, "wb") as f:
        f.write(texto.encode("utf-8"))
    return "acrescentado"


def tira_template(caminho, id_novo):
    with open(caminho, "rb") as f:
        texto = f.read().decode("utf-8")
    novo, n = re.subn(_BLOCO % id_novo, "", texto, flags=re.S)
    if n:
        with open(caminho, "wb") as f:
            f.write(novo.encode("utf-8"))
    return n


# --------------------------------------------------------------------------------------------

def do_58(pasta, nomes):
    """Le arquivos do cliente 5.8 procurando em todos os paks de `pasta`. Devolve `{nome: bytes}`."""
    import glob
    quero = {n.lower() for n in nomes}
    achados = {}
    for p in sorted(glob.glob(os.path.join(LIVE_CLIENTE, pasta, "*.pak"))):
        d, idx = aion_pak.abre(p)
        for e in idx:
            if e.nome.lower() in quero and e.nome not in achados:
                achados[e.nome] = aion_pak.le(d, e)
    return achados


def aplica():
    sys.setrecursionlimit(10000)
    icone = do_58(r"Data\Items", [ICONE + ".dds"])
    for rel in PAKS_DE_ITENS:
        caminho = os.path.join(CLIENTE, rel)
        # O backup e o estado original: reaplicar parte dele, nao do pak ja alterado.
        origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
        d, idx = aion_pak.abre(origem)
        entrada = next(e for e in idx if e.nome.lower() == "client_items.xml")
        novo = aion_pak.le(d, entrada)
        quantos = None
        for id_base, id_novo, nome, mesh, _pt in VARIANTES:
            novo, n, ordenado = acrescenta_item(novo, id_base, id_novo, nome, mesh)
            quantos = n if quantos is None else quantos
        _backup(caminho)
        if origem != caminho:
            shutil.copy2(origem, caminho)
        # Os icones de item ficam no mesmo pak do `client_items.xml` principal.
        tem_icones = any(e.nome.lower().startswith("icon_item_") for e in idx)
        ja_tem = {e.nome.lower() for e in idx}
        icones = {n: b for n, b in icone.items() if tem_icones and n.lower() not in ja_tem}
        regrava_pak(caminho, troca={entrada.nome: novo}, acrescenta=icones)
        _confere_pak(caminho, len(idx), {entrada.nome: "troca", **{n: "novo" for n in icones}})
        # Prova de leitura: o arquivo gravado decodifica e tem o item novo.
        import aion_bxml
        d2, idx2 = aion_pak.abre(caminho)
        xml = aion_bxml.decodifica(aion_pak.le(d2, next(e for e in idx2 if e.nome == entrada.nome)))
        assert xml.count("<client_item>") == quantos + len(VARIANTES)
        for _b, id_novo, _n, mesh, _pt in VARIANTES:
            assert f"<id>{id_novo}</id>" in xml and f"<mesh>{mesh}</mesh>" in xml
        print(f"OK  {rel}: {quantos} -> {quantos + len(VARIANTES)} itens (ordenado por id: {ordenado})")

    for rel, nomes in ((PAK_MESH, MESHES), (PAK_TEXTURA, TEXTURAS)):
        caminho = os.path.join(CLIENTE, rel)
        novos = do_58(r"Objects\items", nomes)
        if len(novos) != len(nomes):
            raise ValueError(f"faltou no 5.8: {sorted(set(nomes) - set(novos))}")
        origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
        _d, idx = aion_pak.abre(origem)
        _backup(caminho)
        if origem != caminho:
            shutil.copy2(origem, caminho)
        regrava_pak(caminho, acrescenta=novos)
        _confere_pak(caminho, len(idx), {n: "novo" for n in novos})
        print(f"OK  {rel}: +{len(novos)} arquivos ({', '.join(novos)})")

    for rel in TEMPLATES:
        caminho = os.path.join(REPO, rel)
        for id_antigo in IDS_ANTIGOS:
            if tira_template(caminho, id_antigo):
                print(f"OK  {rel}: {id_antigo} removido")
        for id_base, id_novo, nome, _mesh, nome_pt in VARIANTES:
            tira_template(caminho, id_novo)  # o clone e refeito a cada vez, a partir da base
            r = acrescenta_template(caminho, id_base, id_novo, nome, nome_pt)
            print(f"OK  {rel}: {id_novo} {r}")


def _paks_de_animacao():
    pasta = os.path.join(CLIENTE, PASTA_ANIMACAO)
    return sorted(
        os.path.join(PASTA_ANIMACAO, a) for a in os.listdir(pasta) if a.lower().endswith(".pak")
    )


def linhas_de_harpa(cal, cafs):
    """Linhas novas do `lm.cal` para as animacoes de harpa.

    O cliente monta o nome da animacao com o sufixo do tipo de arma (`cidle` + `_harp` + `_001`)
    e procura esse nome no `.cal`. Toda entrada de orbe ganha uma irma de harpa: aponta para o
    `.caf` de harpa quando o 5.8 tem um de mesmo nome, e senao para o mesmo arquivo do orbe (as
    genericas, que nao dependem da arma). Os `.caf` de harpa sem equivalente de orbe -- as
    animacoes de skill do Bard -- entram com o nome do proprio arquivo.
    """
    por_nome = {c.lower(): c for c in cafs}
    existentes = set()
    entradas = []
    for linha in cal.splitlines():
        m = re.match(r"\s*([^\s=/][^\s=]*)\s*=\s*(\S+\.caf)", linha, re.I)
        if m:
            existentes.add(m.group(1).lower())
            entradas.append((m.group(1), m.group(2)))

    novas, usados = [], set()

    def acrescenta(nome, alvo):
        if nome.lower() not in existentes:
            existentes.add(nome.lower())
            novas.append(f"{nome}\t\t\t\t\t= {alvo}")

    for nome, alvo in entradas:
        if "_orb" not in nome.lower():
            continue
        pasta, _barra, arquivo = alvo.rpartition("\\")
        irmao = por_nome.get(re.sub("_orb", "_harp", arquivo, flags=re.I).lower())
        if irmao:
            usados.add(irmao.lower())
            alvo = pasta + "\\" + irmao
        acrescenta(re.sub("_orb", "_harp", nome, flags=re.I), alvo)
    for caf in cafs:
        if caf.lower() not in usados:
            nome = re.sub(r"(?i)^lm_|_loop(?=\.caf$)|\.caf$", "", caf)
            acrescenta(nome, "PC\\LM\\Animation\\" + caf)
    return novas


def registros_de_harpa(registros, cafs):
    """O mesmo que [`linhas_de_harpa`], para os registros do `lm.cab`."""
    por_nome = {c.lower(): c for c in cafs}
    existentes = {r[0].lower() for r in registros}
    novos, usados = [], set()

    def acrescenta(nome, caminho, flags, prob):
        if nome.lower() not in existentes:
            existentes.add(nome.lower())
            novos.append((nome, caminho, flags, prob))

    for nome, caminho, flags, prob in registros:
        if "_orb" not in nome.lower():
            continue
        pasta, _barra, arquivo = caminho.rpartition("\\")
        irmao = por_nome.get(re.sub("_orb", "_harp", arquivo, flags=re.I).lower())
        if irmao:
            usados.add(irmao.lower())
            caminho = pasta + "\\" + irmao
        acrescenta(re.sub("_orb", "_harp", nome, flags=re.I), caminho, flags, prob)
    for caf in cafs:
        if caf.lower() not in usados:
            nome = re.sub(r"(?i)^lm_|_loop(?=\.caf$)|\.caf$", "", caf)
            # -1.0 e o "sem prob" de todos os registros comuns.
            acrescenta(nome, "Objects\\PC\\LM\\Animation\\" + caf, 0, -1.0)
    return novos


# --------------------------------------------------------------------------------------------
# Dedos: do esqueleto do 5.8 para o do 5.0
# --------------------------------------------------------------------------------------------
#
# O corpo dos dois esqueletos e o mesmo osso a osso (mesmos deslocamentos em braco, antebraco e
# mao), mas a mao nao: o 5.8 tem cinco dedos de tres falanges e o 5.0 tem tres "dedos" de duas
# (Finger0 = polegar, Finger1 = indicador, Finger2 = os outros tres juntos). As trilhas de mesmo
# nome existem nos dois, com outro deslocamento e outra rotacao de repouso -- tocadas como vem,
# puxam as juntas da mao do 5.0 para o lugar das do 5.8.
#
# Cada trilha de um `.caf` e um chunk 0xCCCC000D: [u32 quantas chaves][u32 crc32 do nome do osso]
# e chaves de 32 bytes [i32 tempo][vec3 posicao][quat x,y,z,w], locais ao osso pai.

_CHUNK_TRILHA = 0xCCCC000D
#: osso do 5.0 -> ossos do 5.8 de onde vem a rotacao. A base do dedo tem um osso so de cada lado.
#: A ponta do 5.0 e um segmento unico que no 5.8 sao dois (falange media e distal): a direcao
#: dele e a da media mais cerca de metade da dobra da distal.
_PESO_DA_DISTAL = 0.5
_DEDOS = {
    "Finger0": ("Finger0",), "Finger01": ("Finger01", "Finger02"),
    "Finger1": ("Finger1",), "Finger11": ("Finger11", "Finger12"),
    "Finger2": ("Finger2",), "Finger21": ("Finger21", "Finger22"),
}


def _id_do_osso(nome):
    return zlib.crc32(nome.encode("latin-1")) & 0xFFFFFFFF


def _q_mul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz)


def _q_inv(q):
    return (-q[0], -q[1], -q[2], q[3])


def _q_pot(q, t):
    """A mesma rotacao com o angulo multiplicado por `t`."""
    x, y, z, w = q if q[3] >= 0 else tuple(-c for c in q)
    seno = (x * x + y * y + z * z) ** 0.5
    if seno < 1e-9:
        return (0.0, 0.0, 0.0, 1.0)
    meio = math.atan2(seno, w) * t
    k = math.sin(meio) / seno
    return (x * k, y * k, z * k, math.cos(meio))


def trilhas_do_caf(d):
    """`{id do osso: (offset das chaves, quantas)}` de um `.caf`."""
    _tipo, _versao, tabela = struct.unpack_from("<III", d, 8)
    achadas = {}
    for i in range(struct.unpack_from("<I", d, tabela)[0]):
        tipo, _v, off, _id = struct.unpack_from("<IIII", d, tabela + 4 + i * 16)
        if tipo == _CHUNK_TRILHA:
            quantas, osso = struct.unpack_from("<II", d, off)
            achadas[osso] = (off + 8, quantas)
    return achadas


def _chave(d, trilha, i):
    off, quantas = trilha
    v = struct.unpack_from("<i3f4f", d, off + min(i, quantas - 1) * 32)
    return v[0], v[1:4], v[4:8]


def repouso_dos_dedos(caf):
    """Posicao e rotacao da primeira chave de cada osso de dedo, pelo nome."""
    t = trilhas_do_caf(caf)
    pose = {}
    for lado in "LR":
        for nomes in _DEDOS.values():
            for n in nomes:
                osso = f"Bip01 {lado} {n}"
                if _id_do_osso(osso) in t:
                    _tempo, pos, rot = _chave(caf, t[_id_do_osso(osso)], 0)
                    pose[osso] = (pos, rot)
    return pose


def retarga_dedos(caf, repouso58, repouso50):
    """Reescreve as trilhas de dedo de um `.caf` do 5.8 para o esqueleto do 5.0.

    `repouso58` e `repouso50` sao a mesma pose (a mao relaxada do `nidle`) em cada esqueleto. A
    posicao passa a ser a do 5.0. Na base do dedo, cujo eixo de repouso muda de um esqueleto para
    o outro, a rotacao guarda so o quanto o dedo saiu do repouso do 5.8, aplicado sobre o repouso
    do 5.0. Na ponta, que nos dois e uma dobradica pura no eixo z, o angulo vai direto.
    """
    d = bytearray(caf)
    t = trilhas_do_caf(caf)
    for lado in "LR":
        for alvo, fontes in _DEDOS.items():
            osso = f"Bip01 {lado} {alvo}"
            trilha = t.get(_id_do_osso(osso))
            if not trilha or osso not in repouso50:
                continue
            origens = [f"Bip01 {lado} {f}" for f in fontes]
            origens = [o for o in origens if _id_do_osso(o) in t and o in repouso58]
            pos50, rot50 = repouso50[osso]
            if not origens:
                continue
            for i in range(trilha[1]):
                _tempo, _pos, q = _chave(caf, t[_id_do_osso(origens[0])], i)
                if len(fontes) == 1:
                    rot = _q_mul(rot50, _q_mul(_q_inv(repouso58[origens[0]][1]), q))
                else:
                    rot = q
                    for o in origens[1:]:
                        _tempo, _pos, distal = _chave(caf, t[_id_do_osso(o)], i)
                        rot = _q_mul(rot, _q_pot(distal, _PESO_DA_DISTAL))
                norma = sum(c * c for c in rot) ** 0.5 or 1.0
                struct.pack_into("<3f4f", d, trilha[0] + i * 32 + 4, *pos50, *(c / norma for c in rot))
    return bytes(d)


#: Os 12 ossos de dedo que existem nos dois esqueletos.
OSSOS_DE_DEDO = tuple(f"Bip01 {lado} {n}" for lado in "LR" for n in _DEDOS)
#: Copias do pak de animacao com cada variante da correcao dos dedos, ao lado dele.
SUFIXO_POS = ".dedos_pos"
SUFIXO_POS_ROT = ".dedos_pos_rot"


def so_posicao_dos_dedos(caf, posicoes):
    """Troca so a posicao das chaves dos 12 ossos de dedo; tempo, rotacao e o resto ficam como sao.

    `posicoes` e `{nome do osso: (x, y, z)}`, a posicao de referencia do esqueleto do 5.0.
    Devolve os bytes novos e `{nome do osso: quantas chaves}`.
    """
    d = bytearray(caf)
    t = trilhas_do_caf(caf)
    mexidas = {}
    for osso in OSSOS_DE_DEDO:
        trilha = t.get(_id_do_osso(osso))
        if not trilha:
            continue
        for i in range(trilha[1]):
            struct.pack_into("<3f", d, trilha[0] + i * 32 + 4, *posicoes[osso])
        mexidas[osso] = trilha[1]
    return bytes(d), mexidas


def posicoes_de_referencia_50():
    """Posicao local (em relacao ao osso pai) dos 12 ossos de dedo na bind pose do `lm.cgf` do 5.0."""
    caminho = os.path.join(CLIENTE, PAK_CAL)
    origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
    d, idx = aion_pak.abre(origem)
    cgf = aion_pak.le(d, next(e for e in idx if e.nome.lower() == "lm.cgf"))
    _tipo, _versao, tabela = struct.unpack_from("<III", cgf, 8)
    chunks = sorted(
        (struct.unpack_from("<IIII", cgf, tabela + 4 + i * 16)
         for i in range(struct.unpack_from("<I", cgf, tabela)[0])),
        key=lambda c: c[2],
    )
    fins = [c[2] for c in chunks[1:]] + [tabela]
    nomes = ossos = bind = None
    for (tipo, _v, off, _id), fim in zip(chunks, fins):
        if tipo == 0xCCCC0005:    # nomes, na ordem dos ossos
            n = struct.unpack_from("<I", cgf, off)[0]
            nomes = [x.decode("latin-1") for x in cgf[off + 4:fim].split(b"\0")[:n]]
        elif tipo == 0xCCCC0003:  # ossos: id, pai, filhos, controller id, ...
            n = struct.unpack_from("<I", cgf, off + 16)[0]
            passo = (fim - off - 20) // n
            ossos = [struct.unpack_from("<iiiI", cgf, off + 20 + i * passo) for i in range(n)]
        elif tipo == 0xCCCC0012:  # bind pose: matriz 4x3 por osso, no espaco do modelo
            n = struct.unpack_from("<II", cgf, off)[1]
            bind = [struct.unpack_from("<12f", cgf, off + 8 + i * 48) for i in range(n)]
    posicoes = {}
    for i, nome in enumerate(nomes):
        if nome not in OSSOS_DE_DEDO:
            continue
        if ossos[i][3] != _id_do_osso(nome):
            raise ValueError(f"{nome}: o id do osso nao e o crc32 do nome")
        pai = bind[ossos[i][1]]
        # Posicao do osso no referencial do pai: (t - t_pai) . R_pai^T, com as linhas de R como eixos.
        delta = [bind[i][9 + k] - pai[9 + k] for k in range(3)]
        posicoes[nome] = tuple(sum(delta[k] * pai[3 * eixo + k] for k in range(3)) for eixo in range(3))
    if len(posicoes) != len(OSSOS_DE_DEDO):
        raise ValueError("nem todos os ossos de dedo estao no lm.cgf do 5.0")
    return posicoes


def valida_so_posicao(original, novo, posicoes):
    """Prova que `novo` so difere de `original` na posicao das chaves dos ossos de dedo."""
    if len(original) != len(novo):
        raise ValueError("tamanho mudou")
    t = trilhas_do_caf(original)
    if trilhas_do_caf(novo) != t:
        raise ValueError("a tabela de trilhas mudou")
    permitido = bytearray(len(original))
    for osso in OSSOS_DE_DEDO:
        trilha = t.get(_id_do_osso(osso))
        if not trilha:
            continue
        for i in range(trilha[1]):
            chave = trilha[0] + i * 32
            permitido[chave + 4:chave + 16] = b"\1" * 12
            if struct.unpack_from("<3f", novo, chave + 4) != struct.unpack("<3f", struct.pack("<3f", *posicoes[osso])):
                raise ValueError(f"{osso}: posicao da chave {i} nao e a de referencia")
    fora = sum(1 for a, b, p in zip(original, novo, permitido) if a != b and not p)
    if fora:
        raise ValueError(f"{fora} bytes mudaram fora da posicao dos dedos")
    return sum(1 for a, b in zip(original, novo) if a != b)


def aplica_dedos_so_posicao(relatorio=None):
    """Regrava as animacoes de harpa do LM trocando so a posicao dos dedos (ver o relatorio)."""
    posicoes = posicoes_de_referencia_50()
    cafs = sorted(a for a in os.listdir(LIVE_ANIMACAO)
                  if a.lower().startswith("lm_") and a.lower().endswith(".caf"))
    novos, linhas = {}, []
    for a in cafs:
        with open(os.path.join(LIVE_ANIMACAO, a), "rb") as f:
            original = f.read()
        novos[a], mexidas = so_posicao_dos_dedos(original, posicoes)
        bytes_mudados = valida_so_posicao(original, novos[a], posicoes)
        linhas.append((a, len(trilhas_do_caf(original)), len(mexidas), sum(mexidas.values()), bytes_mudados))

    caminho = os.path.join(CLIENTE, PAK_ANIMACAO)
    original_pak = caminho + SUFIXO_BACKUP
    if not os.path.exists(original_pak):
        raise ValueError("sem o backup original do pak de animacao")
    d0, idx0 = aion_pak.abre(original_pak)
    destino = caminho + SUFIXO_POS
    shutil.copy2(original_pak, destino)
    regrava_pak(destino, acrescenta=novos)
    # Releitura do pak gravado: os 217 conferem byte a byte e as entradas antigas nao mudaram.
    d1, idx1 = aion_pak.abre(destino)
    por_nome = {e.nome: e for e in idx1}
    for a, dados in novos.items():
        if aion_pak.le(d1, por_nome[a]) != dados:
            raise ValueError(f"{a}: o que saiu do pak nao e o que foi gravado")
    for e in idx0:
        if aion_pak.le(d0, e) != aion_pak.le(d1, por_nome[e.nome]):
            raise ValueError(f"{e.nome}: entrada antiga do pak mudou")
    if len(idx1) != len(idx0) + len(novos):
        raise ValueError("contagem de entradas do pak nao fecha")
    shutil.copy2(destino, caminho)
    print(f"OK  {PAK_ANIMACAO}: {len(novos)} animacoes de harpa, so a posicao dos dedos trocada")
    print(f"    {len(idx0)} entradas antigas do pak identicas ao original; copia em *{SUFIXO_POS}")
    if relatorio:
        with open(relatorio, "w", encoding="utf-8", newline="\n") as f:
            f.write("arquivo;trilhas;ossos_de_dedo_alterados;chaves_alteradas;bytes_diferentes\n")
            for linha in linhas:
                f.write(";".join(str(c) for c in linha) + "\n")
    return posicoes, linhas


def instala_variante_dos_dedos(sufixo):
    """Poe no lugar do pak de animacao a copia de uma variante (`.dedos_pos` ou `.dedos_pos_rot`)."""
    caminho = os.path.join(CLIENTE, PAK_ANIMACAO)
    if not os.path.exists(caminho + sufixo):
        raise ValueError(f"nao existe {caminho + sufixo}")
    shutil.copy2(caminho + sufixo, caminho)
    print(f"OK  {PAK_ANIMACAO} <- *{sufixo}")


#: Pecas do trabalho da harpa no cliente de teste, para ligar e desligar uma de cada vez quando um
#: defeito aparece fora da harpa. Cada uma e a lista de arquivos que ela alterou.
COMPONENTES = {
    "lista": (PAK_CAL, PAK_CAB),
    "marcadores": (PAK_MARCADORES,),
    "animacoes": (PAK_ANIMACAO,),
    "sons": (PAK_SONS,),
    "itens": PAKS_DE_ITENS + (PAK_MESH, PAK_TEXTURA),
    "efeito": (PAK_EFEITOS, PAK_SOM_DO_PROJETIL),
    "dll": (r"bin64\version.dll",),
}
SUFIXO_LIGADO = ".harpa_ligada"


def alterna_componente(nome, estado):
    """`estado` = "original" tira a peca (guardando a versao da harpa ao lado); "harpa" a devolve."""
    for rel in COMPONENTES[nome]:
        caminho = os.path.join(CLIENTE, rel)
        ligado, original = caminho + SUFIXO_LIGADO, caminho + SUFIXO_BACKUP
        if estado == "original":
            if not os.path.exists(original):
                raise ValueError(f"sem o original de {rel}")
            if not os.path.exists(ligado):
                shutil.copy2(caminho, ligado)
            shutil.copy2(original, caminho)
        else:
            if not os.path.exists(ligado):
                print(f"    {rel}: ja esta na versao da harpa")
                continue
            shutil.copy2(ligado, caminho)
            os.remove(ligado)
        print(f"OK  {rel}: {estado}")


def entradas_oficiais_de_harpa(cafs):
    """As entradas de harpa do `lm.cal` do Live 5.8, apontadas para arquivos que o 5.0 tem.

    Substitui a derivacao a partir das entradas de orbe ([`linhas_de_harpa`]), que errava em 69
    nomes (o ataque andando para tras, por exemplo, caia na animacao do orbe). Cada alvo e o
    `.caf` de harpa trazido do 5.8 quando e um deles; senao, o arquivo de mesmo nome que o
    proprio 5.0 ja tem (as animacoes genericas, que nao dependem da arma). Devolve
    `[(nome, caminho no formato do .cal, prob ou -1)]`.
    """
    import glob
    cal = None
    for p in sorted(glob.glob(os.path.join(LIVE_CLIENTE, r"Objects\PC2\lm\mesh", "*.pak"))):
        d, idx = aion_pak.abre(p)
        e = next((x for x in idx if x.nome.lower() == "lm.cal"), None)
        if e:
            cal = aion_pak.le(d, e).decode("latin-1")
            break
    if cal is None:
        raise ValueError("nao achei o lm.cal do 5.8")
    harpa = {c.lower(): c for c in cafs}
    do50 = {}
    for rel in _paks_de_animacao():
        p = os.path.join(CLIENTE, rel)
        p = p + SUFIXO_BACKUP if os.path.exists(p + SUFIXO_BACKUP) else p
        for e in aion_pak.abre(p)[1]:
            do50.setdefault(e.nome.lower(), e.nome)
    saida, sem_arquivo = [], []
    for linha in cal.splitlines():
        m = re.match(r"\s*([^\s=/][^\s=]*)\s*=\s*(\S+\.caf)(.*)", linha, re.I)
        if not m or "harp" not in m.group(1).lower():
            continue
        arquivo = m.group(2).replace("/", "\\").rsplit("\\", 1)[-1]
        nome_real = harpa.get(arquivo.lower()) or do50.get(arquivo.lower())
        if not nome_real:
            sem_arquivo.append(m.group(1))
            continue
        prob = re.search(r"prob\s*=\s*([\d.]+)", m.group(3))
        # O .cab guarda a prob em float de 32 bits.
        prob = struct.unpack("<f", struct.pack("<f", float(prob.group(1))))[0] if prob else None
        saida.append((m.group(1), "PC\\LM\\Animation\\" + nome_real, prob if prob is not None else -1.0))
    print(f"    lista oficial do 5.8: {len(saida)} entradas de harpa; sem arquivo no 5.0: {len(sem_arquivo)}"
          + (f" ({', '.join(sem_arquivo[:8])}{'...' if len(sem_arquivo) > 8 else ''})" if sem_arquivo else ""))
    return saida


def aplica_animacao():
    """Poe as animacoes de harpa do 5.8 no LM com o nome delas, e as declara na lista do modelo."""
    import aion_cab
    # Desfaz a troca de conteudo dos testes anteriores (orbe, livro e lamina com animacao de harpa).
    for rel in _paks_de_animacao():
        caminho = os.path.join(CLIENTE, rel)
        if os.path.exists(caminho + SUFIXO_BACKUP):
            shutil.copy2(caminho + SUFIXO_BACKUP, caminho)

    cafs = sorted(a for a in os.listdir(LIVE_ANIMACAO)
                  if a.lower().startswith("lm_") and a.lower().endswith(".caf"))
    # A mao relaxada nos dois esqueletos: o saque da harpa comeca no `nidle` do 5.8, e o `nidle`
    # do proprio 5.0 da a mesma pose no esqueleto dele.
    with open(os.path.join(LIVE_ANIMACAO, REPOUSO_58), "rb") as f:
        repouso58 = repouso_dos_dedos(f.read())
    repouso50 = None
    for rel in _paks_de_animacao():
        d, idx = aion_pak.abre(os.path.join(CLIENTE, rel))
        e = next((x for x in idx if x.nome.lower() == REPOUSO_50), None)
        if e:
            repouso50 = repouso_dos_dedos(aion_pak.le(d, e))
            break
    if not repouso50 or len(repouso50) != 12 or len(repouso58) != 18:
        raise ValueError("nao achei a pose de repouso dos dedos nos dois esqueletos")

    novos = {}
    for a in cafs:
        with open(os.path.join(LIVE_ANIMACAO, a), "rb") as f:
            novos[a] = retarga_dedos(f.read(), repouso58, repouso50)
    caminho = os.path.join(CLIENTE, PAK_ANIMACAO)
    _backup(caminho)
    _d, idx = aion_pak.abre(caminho)
    regrava_pak(caminho, acrescenta=novos)
    _confere_pak(caminho, len(idx), {n: "novo" for n in novos})
    print(f"OK  {PAK_ANIMACAO}: +{len(novos)} animacoes de harpa")

    oficiais = entradas_oficiais_de_harpa(cafs)

    caminho = os.path.join(CLIENTE, PAK_CAL)
    origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
    d, idx = aion_pak.abre(origem)
    entrada = next(e for e in idx if e.nome.lower() == "lm.cal")
    cal = aion_pak.le(d, entrada).decode("latin-1")
    existentes = {m.group(1).lower() for m in re.finditer(r"(?m)^\s*([^\s=/][^\s=]*)\s*=", cal)}
    oficiais = [o for o in oficiais if o[0].lower() not in existentes]
    novas = [f"{n}\t\t\t\t\t= {alvo}" + (f"\t// prob={prob:g}" if prob >= 0 else "")
             for n, alvo, prob in oficiais]
    titulo = "// ---------- harp (Live 5.8), weapon type 19 ----------"
    cal = cal.rstrip("\r\n") + "\r\n\r\n" + titulo + "\r\n" + "\r\n".join(novas) + "\r\n"
    _backup(caminho)
    if origem != caminho:
        shutil.copy2(origem, caminho)
    regrava_pak(caminho, troca={entrada.nome: cal.encode("latin-1")})
    _confere_pak(caminho, len(idx), {entrada.nome: "troca"})
    print(f"OK  {PAK_CAL}: lm.cal com +{len(novas)} entradas de harpa")

    caminho = os.path.join(CLIENTE, PAK_CAB)
    origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
    d, idx = aion_pak.abre(origem)
    entrada = next(e for e in idx if e.nome.lower() == "lm.cab")
    registros = aion_cab.le(aion_pak.le(d, entrada))
    ja = {r[0].lower() for r in registros}
    novos = [(n, "Objects\\" + alvo, 0, prob) for n, alvo, prob in oficiais if n.lower() not in ja]
    # O cliente procura por busca binaria: os registros vem ordenados pelo caminho, sem
    # diferenciar maiusculas (o `sort` do Python e estavel, como a ordem original pede).
    registros = sorted(registros + novos, key=lambda r: r[1].lower())
    cab = aion_cab.grava(registros)
    assert aion_cab.le(cab) == registros
    _backup(caminho)
    if origem != caminho:
        shutil.copy2(origem, caminho)
    regrava_pak(caminho, troca={entrada.nome: cab})
    _confere_pak(caminho, len(idx), {entrada.nome: "troca"})
    print(f"OK  {PAK_CAB}: lm.cab com +{len(novos)} registros de harpa ({len(registros)} no total)")


def aplica_efeito():
    """Traz do 5.8 o efeito do projetil da harpa (a nota musical) e o que ele usa."""
    import glob
    import aion_fx

    def entradas(caminho):
        d, idx = aion_pak.abre(caminho)
        return d, {e.nome.lower(): e for e in idx}

    caminho = os.path.join(CLIENTE, PAK_EFEITOS)
    origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
    d50, m50 = entradas(origem)
    d58, m58 = entradas(os.path.join(LIVE_CLIENTE, PAK_EFEITOS))

    # Prova das duas conversoes de formato nos arquivos desta instalacao, antes de gravar.
    prt50 = aion_pak.le(d50, m50[PRT_DO_PROJETIL])
    prt58 = aion_pak.le(d58, m58[PRT_DO_PROJETIL])
    iguais, comuns = aion_fx.confere_prt(prt58, prt50)
    print(f"    .prt: {iguais} de {comuns} particulas comuns convertem identicas ao 5.0")
    amostra = sorted(n for n in m50 if n.endswith(".fxc") and n in m58)[::9]
    iguais, comuns = aion_fx.confere_fxc(
        (aion_pak.le(d58, m58[n]), aion_pak.le(d50, m50[n])) for n in amostra)
    print(f"    .fxc: {iguais} de {comuns} efeitos comuns ({len(amostra)} arquivos) convertem identicos")

    # Os efeitos de harpa sao as raizes com "harp" no nome; os filhos vem junto, com qualquer nome.
    registros58 = aion_fx.le(prt58, b"CRY")[2]
    raizes = [aion_fx.nome(r) for r in registros58 if "harp" in aion_fx.nome(r).lower()
              and struct.unpack_from("<i", r, aion_fx.PRT_PAI_58)[0] < 0]
    prt, particulas = aion_fx.acrescenta_prt(prt50, prt58, raizes)
    print(f"    efeitos de harpa: {', '.join(raizes)} ({len(particulas)} registros com os filhos)")
    fxc = aion_fx.fxc_para_50(aion_pak.le(d58, m58[FXC_DO_PROJETIL]))
    if FXC_DO_PROJETIL in m50:
        raise ValueError(f"{FXC_DO_PROJETIL} ja existe no 5.0")
    # Sem entrada nos indices de nomes o efeito nao existe para o jogo (ver `aion_fx.py`).
    efeitos = [aion_fx.nome(r) for r in aion_fx.le(fxc, b"FXC")[2]]
    biblioteca = efeitos[0].split(".", 1)[0]
    indices = {}
    for nome_do_indice, novo in (
        (INDICE_PRT, lambda a, b: aion_fx.indexa_prt(a, b, particulas)),
        (INDICE_FXC, lambda a, b: aion_fx.indexa_fxc(a, b, biblioteca)),
    ):
        indices[m50[nome_do_indice].nome] = novo(aion_pak.le(d50, m50[nome_do_indice]),
                                                 aion_pak.le(d58, m58[nome_do_indice]))
    _backup(caminho)
    if origem != caminho:
        shutil.copy2(origem, caminho)
    regrava_pak(caminho, troca={m50[PRT_DO_PROJETIL].nome: prt, **indices},
                acrescenta={FXC_DO_PROJETIL: fxc})
    _confere_pak(caminho, len(m50), {m50[PRT_DO_PROJETIL].nome: "troca", FXC_DO_PROJETIL: "novo",
                                     **{n: "troca" for n in indices}})
    print(f"    indices de nomes: +{len(particulas)} em {INDICE_PRT}, +{len(efeitos)} em {INDICE_FXC}")
    print(f"OK  {PAK_EFEITOS}: {PRT_DO_PROJETIL} +{len(particulas)} ({', '.join(particulas)})")
    print(f"    {FXC_DO_PROJETIL} novo ({', '.join(efeitos)})")

    # Arquivos que essas particulas citam: texturas e meshes de efeito, e o som do disparo.
    v, campo, registros = aion_fx.le(prt, b"CRY")
    citados = set()
    for r in registros:
        if aion_fx.nome(r) in particulas:
            citados.update(r[i * 128:(i + 1) * 128].split(b"\0")[0].decode("latin-1")
                           for i in range(1, 9))
            citados.add(r[2718:2978].split(b"\0")[0].decode("latin-1"))
    citados.discard("")
    tem = set()
    for p in glob.glob(os.path.join(CLIENTE, "Effects", "*.pak")) + \
            glob.glob(os.path.join(CLIENTE, "sounds", "effect", "**", "*.pak"), recursive=True):
        tem.update(e.nome.lower().replace("/", "\\").rsplit("\\", 1)[-1] for e in aion_pak.abre(p)[1])
    faltam = sorted(c for c in citados if "\\" in c and c.lower().rsplit("\\", 1)[-1] not in tem)
    sons = [c for c in faltam if c.lower().startswith("sounds\\effect\\artist\\")]
    if sons:
        caminho = os.path.join(CLIENTE, PAK_SOM_DO_PROJETIL)
        origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
        _d, idx = aion_pak.abre(origem)
        novos = do_58(os.path.dirname(PAK_SOM_DO_PROJETIL), [s.rsplit("\\", 1)[-1] for s in sons])
        _backup(caminho)
        if origem != caminho:
            shutil.copy2(origem, caminho)
        regrava_pak(caminho, acrescenta=novos)
        _confere_pak(caminho, len(idx), {n: "novo" for n in novos})
        print(f"OK  {PAK_SOM_DO_PROJETIL}: +{len(novos)} ({', '.join(novos)})")
        faltam = [c for c in faltam if c.rsplit("\\", 1)[-1].lower() not in {n.lower() for n in novos}]
    print(f"    arquivos citados que continuam faltando no 5.0: {faltam or 'nenhum'}")
    sem_barra = sorted(c for c in citados if "\\" not in c)
    if sem_barra:
        print(f"    outros efeitos citados (nao conferidos): {sem_barra}")


def aplica_marcadores():
    """Copia do cliente 5.8 os marcadores das animacoes de harpa do LM, e os sons que eles tocam.

    O `AnimationMarkers\\lm.xml` diz, por animacao, em que instante cada coisa acontece: quando a
    arma passa do osso das costas para o da mao (`equip_weapon`), o ponto de acerto (`hitpoint`),
    sons, efeitos e rastros. Sem a entrada, a animacao toca mas a arma so troca de osso no fim.
    """
    import xml.etree.ElementTree as ET
    import aion_bxml
    sys.setrecursionlimit(10000)

    d58, idx58 = aion_pak.abre(os.path.join(LIVE_CLIENTE, PAK_MARCADORES))
    xml58 = aion_bxml.decodifica(aion_pak.le(d58, next(e for e in idx58 if e.nome.lower() == "lm.xml")))
    raiz58 = ET.fromstring(xml58.split("?>", 1)[1])

    caminho = os.path.join(CLIENTE, PAK_MARCADORES)
    origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
    d, idx = aion_pak.abre(origem)
    entrada = next(e for e in idx if e.nome.lower() == "lm.xml")
    bxml = aion_pak.le(d, entrada)
    existentes = set(re.findall(r'<animation [^>]*name="([^"]*)"', aion_bxml.decodifica(bxml).lower()))
    novos = [a for a in raiz58 if "harp" in a.get("name", "").lower()
             and a.get("name").lower() not in existentes]
    novo, quantos = acrescenta_filhos(bxml, novos)
    conferido = aion_bxml.decodifica(novo)
    assert conferido.count("<animation ") == quantos + len(novos)
    assert 'name="cdraw_harp_001"' in conferido
    _backup(caminho)
    if origem != caminho:
        shutil.copy2(origem, caminho)
    regrava_pak(caminho, troca={entrada.nome: novo})
    _confere_pak(caminho, len(idx), {entrada.nome: "troca"})
    print(f"OK  {PAK_MARCADORES}: lm.xml com +{len(novos)} animacoes de harpa ({quantos + len(novos)} no total)")

    # Sons de movimento que esses marcadores tocam e o 5.0 nao tem.
    pedidos = set()
    for a in novos:
        for s in a.iter("sound"):
            arquivo = s.get("file", "").replace("/", "\\").lower()
            if arquivo.startswith("sounds\\motion\\"):
                pedidos.add(arquivo.rsplit("\\", 1)[1])
    caminho = os.path.join(CLIENTE, PAK_SONS)
    origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
    _d, idx = aion_pak.abre(origem)
    tem = {e.nome.lower() for e in idx}
    faltam = sorted(pedidos - tem)
    novos_sons = do_58(r"Sounds\motion", faltam)
    if novos_sons:
        _backup(caminho)
        if origem != caminho:
            shutil.copy2(origem, caminho)
        regrava_pak(caminho, acrescenta=novos_sons)
        _confere_pak(caminho, len(idx), {n: "novo" for n in novos_sons})
    sem = [n for n in faltam if n not in {s.lower() for s in novos_sons}]
    print(f"OK  {PAK_SONS}: +{len(novos_sons)} sons; faltam {len(sem)}: {', '.join(sem)}")


#: Strings novas, `(arquivo, id, nome, {lingua: texto})`. A faixa 1.900.000 a 2.199.999 esta
#: livre em todas as linguas do 5.0.
#: - Nome do tipo de arma no tooltip: o `harp_fix.h` pede o id 1990001 para o tipo 19. O 5.8 usa
#:   STR_TOOLTIP_HARP com o id 904448, que no 5.0 ja e outra string. Ingles = o do Live
#:   (l10n/eng do Riftshade); os outros sao traducao nossa.
#: - Nome do item de teste: o clone herdava o `desc` do orbe (STR_TEST_ORB_18A).
STRINGS = (
    ("strings/client_strings_ui.xml", 1990001, "STR_TOOLTIP_HARP",
     {"ENG": "Harp", "DEU": "Harfe", "FRA": "Harpe", "BRA": "Harpa"}),
    ("strings/client_strings_item.xml", 1990002, "STR_TEST_HARP_58",
     {"ENG": "Test Harp 5.8", "DEU": "Testharfe 5.8", "FRA": "Harpe de test 5.8",
      "BRA": "Harpa de Teste 5.8"}),
)
DESC_DO_ITEM = "STR_TEST_HARP_58"
#: ENG/DEU/FRA: XML binario no pak ofuscado. BRA: ZIP comum com XML em UTF-16; o
#: `z_Patch001.pak` vem depois do `Data.pak` e traz os `client_strings_*.xml` inteiros.
PAKS_DE_STRINGS = {
    "ENG": r"l10n\ENG\Data\Data.pak",
    "DEU": r"l10n\DEU\Data\Data.pak",
    "FRA": r"l10n\FRA\data\data.pak",
    "BRA": r"l10n\BRA\Data\z_Patch001.pak",
}


def _string_xml(id_string, nome, texto):
    return (f"  <string>\n    <id>{id_string}</id>\n    <name>{nome}</name>\n"
            f"    <body>{texto}</body>\n  </string>\n")


def aplica_strings():
    import zipfile
    import xml.etree.ElementTree as ET
    import aion_bxml
    for lingua, rel in PAKS_DE_STRINGS.items():
        caminho = os.path.join(CLIENTE, rel)
        # Sempre a partir do original: reaplicar nao duplica.
        origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
        por_arquivo = {}
        for arquivo, id_string, nome, textos in STRINGS:
            por_arquivo.setdefault(arquivo, []).append((id_string, nome, textos[lingua]))
        lidos = {}
        if lingua == "BRA":
            with zipfile.ZipFile(origem) as z:
                entradas = [(i, z.read(i)) for i in z.infolist()]
            _backup(caminho)
            tmp = caminho + ".tmp_harpa58"
            with zipfile.ZipFile(tmp, "w") as z:
                for info, dados in entradas:
                    novas = por_arquivo.get(info.filename.lower())
                    if novas:
                        xml = dados.decode("utf-16")
                        for id_string, _n, _t in novas:
                            if f"<id>{id_string}</id>" in xml:
                                raise ValueError(f"{rel}: o id {id_string} ja existe")
                        fim = xml.rindex("</strings>")
                        xml = xml[:fim] + "".join(_string_xml(*n) for n in novas) + xml[fim:]
                        dados = xml.encode("utf-16")
                    z.writestr(info, dados, compress_type=info.compress_type)
            os.replace(tmp, caminho)
            with zipfile.ZipFile(caminho) as z:
                assert z.testzip() is None and len(z.infolist()) == len(entradas)
                for arquivo in por_arquivo:
                    lidos[arquivo] = z.read(arquivo).decode("utf-16")
        else:
            d, idx = aion_pak.abre(origem)
            troca = {}
            for arquivo, novas in por_arquivo.items():
                entrada = next(e for e in idx if e.nome.lower() == arquivo)
                bxml = aion_pak.le(d, entrada)
                texto_xml = aion_bxml.decodifica(bxml)
                for id_string, _n, _t in novas:
                    if f"<id>{id_string}</id>" in texto_xml:
                        raise ValueError(f"{rel}: o id {id_string} ja existe")
                troca[entrada.nome], _ = acrescenta_filhos(
                    bxml, [ET.fromstring(_string_xml(*n)) for n in novas])
            _backup(caminho)
            if origem != caminho:
                shutil.copy2(origem, caminho)
            regrava_pak(caminho, troca=troca)
            _confere_pak(caminho, len(idx), {n: "troca" for n in troca})
            d2, idx2 = aion_pak.abre(caminho)
            for arquivo in por_arquivo:
                e2 = next(e for e in idx2 if e.nome.lower() == arquivo)
                lidos[arquivo] = aion_bxml.decodifica(aion_pak.le(d2, e2))
        for arquivo, novas in por_arquivo.items():
            for id_string, nome, texto in novas:
                lido = lidos[arquivo]
                bloco = re.search(r"<string>\s*<id>%d</id>.*?</string>" % id_string, lido, re.S)
                assert bloco and f"<body>{texto}</body>" in bloco.group(0)
                assert lido.count(f"<id>{id_string}</id>") == 1
                print(f"OK  {rel}: {nome} = {id_string} '{texto}'")


def _paks_com_backup():
    raizes = [os.path.join(CLIENTE, "objects"), os.path.join(CLIENTE, "sounds"),
              os.path.join(CLIENTE, "Effects"),
              os.path.dirname(os.path.join(CLIENTE, PAK_MARCADORES))]
    raizes += [os.path.dirname(os.path.join(CLIENTE, rel)) for rel in PAKS_DE_ITENS]
    raizes += [os.path.dirname(os.path.join(CLIENTE, rel)) for rel in PAKS_DE_STRINGS.values()]
    # `data\items` contem `special\` e `special2\`: sem repetir.
    vistos = set()
    for raiz in raizes:
        for base, _dirs, arqs in os.walk(raiz):
            for a in arqs:
                caminho = os.path.join(base, a[:-len(SUFIXO_BACKUP)])
                if a.endswith(SUFIXO_BACKUP) and caminho not in vistos:
                    vistos.add(caminho)
                    yield caminho


def desfaz():
    for caminho in _paks_com_backup():
        shutil.copy2(caminho + SUFIXO_BACKUP, caminho)
        print(f"restaurado {os.path.relpath(caminho, CLIENTE)}")
    for rel in TEMPLATES:
        ids = [v[1] for v in VARIANTES] + list(IDS_ANTIGOS)
        n = sum(tira_template(os.path.join(REPO, rel), i) for i in ids)
        print(f"{rel}: {n} template(s) removido(s)")


if __name__ == "__main__":
    if "--desfaz" in sys.argv:
        desfaz()
    elif "--animacao" in sys.argv:
        aplica_animacao()
    elif "--efeito" in sys.argv:
        aplica_efeito()
    elif "--componente" in sys.argv:
        i = sys.argv.index("--componente")
        alterna_componente(sys.argv[i + 1], sys.argv[i + 2])
    elif "--dedos-posicao" in sys.argv:
        aplica_dedos_so_posicao(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                             "dedos_harpa_so_posicao.csv"))
    elif "--dedos-variante" in sys.argv:
        instala_variante_dos_dedos({"posicao": SUFIXO_POS, "posicao+rotacao": SUFIXO_POS_ROT}[
            sys.argv[sys.argv.index("--dedos-variante") + 1]])
    elif "--marcadores" in sys.argv:
        aplica_marcadores()
    elif "--strings" in sys.argv:
        aplica_strings()
    else:
        aplica()

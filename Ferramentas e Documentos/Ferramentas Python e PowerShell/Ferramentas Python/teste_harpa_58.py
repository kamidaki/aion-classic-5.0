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
    python teste_harpa_58.py --icone-classe   icone pequeno das classes do Bard (emblemas do 5.8 e Skins)
    python teste_harpa_58.py --botao-criacao   botao do Bard na tela de criacao (textura, Preset e layout)
    python teste_harpa_58.py --plataforma-criacao   plataforma do Bard no mapa da criacao (levels/login)
    python teste_harpa_58.py --painel-criacao   painel da direita da criacao (descricao, atributos, etiquetas)
    python teste_harpa_58.py --vozes      voz da selecao do Bard/Artist (vlogin2_*) nos paks de voz
    python teste_harpa_58.py --classe-animacoes   selecao/criacao/idle do Bard (as 4 racas)
    python teste_harpa_58.py --corrige-harpa-previa   so a malha e o item da Elyos feminina
    python teste_harpa_58.py --ajusta-harpa-previa    corrige a altura da malha ja instalada
    python teste_harpa_58.py --racas      harpa no LF, DM e DF (animacoes do LF, listas e marcadores)
    python teste_harpa_58.py --strings    nome do tipo de arma (STR_TOOLTIP_HARP) nas linguas do cliente
    python teste_harpa_58.py --barra-inicial   barra de atalhos inicial do Bard (client_default_key.xml)
    python teste_harpa_58.py --desfaz   restaura os paks e tira o template do servidor
"""
import math
import hashlib
import os
import re
import shutil
import struct
import sys
import zlib
from functools import lru_cache

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
#: Selecao do Bard (marcador Nselect_bard_lobby_001): efeito FC_Sys_LoginStage.AR.<raca> e o som
#: que o marcador toca como arquivo.
FXC_DA_SELECAO = "fxc/fc_sys_loginstage.fxc"
SONS_DA_SELECAO = (r"Sounds\effect\artist\skill_harp_SongofAromatherapy_cast.ogg",)
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
#: Harpas da previa da tela de criacao (so no cliente): as duas primeiras sao as do 5.8;
#: a terceira e exclusiva da Elyos feminina, para corrigir so a malha da harpa.
#: A animacao de criacao poe o `Lhand_bone` a 30-40 cm da mao, para a origem destes modelos; a
#: HA_C001 (de teste) tem outra origem e orientacao e fica dentro do corpo na personagem feminina.
#: Elyos usa a npc_harp_best_01, Asmodiano a npc_harp_idvritra01a_01 (as do Live).
ITENS_DA_PREVIA = (
    (100500003, 102000908, "npc_harp_best_01", "HA_IDRun01a"),
    (100500003, 102001020, "npc_harp_idvritra01a_01", "HA_IDVritra01a"),
    (100500003, 102099908, "npc_harp_best_01_elyos_f", "HA_IDRun01a_ElyosF"),
)
MESHES_DA_PREVIA = ("HA_IDRun01a.cgf", "HA_IDVritra01a.cgf")
MESH_ELYOS_F = "HA_IDRun01a_ElyosF.cgf"
# A rotacao completa entre maos LF/DF inclinava a harpa. So a componente em torno de Y
# (67,679 graus) vira a face do instrumento e preserva seu eixo longo, que ja aparecia em pe
# na malha original. O centro medio dos 1209 vertices da HA_IDRun01a.cgf oficial e o pivo;
# o deslocamento do no e (I - R) * centro. Assim o corpo nao volta para a mao da varinha.
CORRECAO_HARPA_ELYOS_F = (
    (0.37979448, 0.0, 0.92507089),
    (0.0, 1.0, 0.0),
    (-0.92507089, 0.0, 0.37979448),
)
QUAT_HARPA_ELYOS_F = (0.0, 0.5568687105, 0.0, 0.8306005293)
CENTRO_HARPA_ELYOS_F = (0.07022414, -0.31550619, -0.01984606)
# Seis centimetros em direcao a camera da previa, expressos no referencial do Lhand_bone
# na pose DF_Nidle_bard_create. A camera e a animacao permanecem intactas.
AVANCO_HARPA_ELYOS_F = (-0.02582616, -0.02953973, -0.04539178)
SHA_HARPA_ELYOS = "23a2648233a13fe8ee770140560de6909193c43caed53c966a01d6d4d743e224"


def malha_harpa_elyos_feminina(original):
    """Corrige o no principal do CGF oficial; os efeitos e a malha original ficam intactos."""
    if hashlib.sha256(original).hexdigest() != SHA_HARPA_ELYOS:
        raise ValueError("HA_IDRun01a.cgf nao e a malha oficial conferida do Live 5.8")
    tabela = struct.unpack_from("<I", original, 16)[0]
    quantidade = struct.unpack_from("<I", original, tabela)[0]
    nos = []
    for i in range(quantidade):
        tipo, _versao, posicao, _id = struct.unpack_from("<4I", original, tabela + 4 + 16 * i)
        if tipo == 0xCCCC000B and original[posicao + 16:posicao + 80].split(b"\0", 1)[0] == b"HA_IDRun01a":
            nos.append(posicao)
    if len(nos) != 1:
        raise ValueError("no principal da HA_IDRun01a.cgf nao encontrado uma unica vez")
    base = nos[0]
    saida = bytearray(original)
    rotacao = CORRECAO_HARPA_ELYOS_F
    posicao = [CENTRO_HARPA_ELYOS_F[i] - sum(rotacao[i][j] * CENTRO_HARPA_ELYOS_F[j]
                                                for j in range(3)) + AVANCO_HARPA_ELYOS_F[i]
               for i in range(3)]
    matriz = [rotacao[j][i] for i in range(3) for j in range(3)]
    matriz = [matriz[0], matriz[1], matriz[2], 0.0,
              matriz[3], matriz[4], matriz[5], 0.0,
              matriz[6], matriz[7], matriz[8], 0.0,
              *(v * 100 for v in posicao), 1.0]
    struct.pack_into("<16f", saida, base + 100, *matriz)
    struct.pack_into("<3f", saida, base + 164, *(v * 100 for v in posicao))
    struct.pack_into("<4f", saida, base + 176, *QUAT_HARPA_ELYOS_F)
    return bytes(saida)
TEXTURAS_DA_PREVIA = (
    "HA_IDRun01a.dds", "HA_IDRun01a_ddn.dds", "HA_IDRun01a_illum.dds", "HA_IDRun01a_matid.dds",
    "HA_IDRun01a_sp.dds",
    "HA_IDVritra01a.dds", "HA_IDVritra01a_ddn.dds", "HA_IDVritra01a_illum.dds", "HA_IDVritra01a_mask.dds",
    "HA_IDVritra01a_matid.dds", "HA_IDVritra01a_sp.dds",
)
#: A HA_IDVritra01a pede dois efeitos em objects\pc2\male, pasta que o 5.0 nao tem: vao para
#: objects\items e o caminho no material da mesh (campo de tamanho fixo) passa a apontar para la.
TEXTURAS_PC2_DA_PREVIA = ("FX_IDVritra01a_n.dds", "FX_IDVritra01a_p.dds")
CAMINHOS_PC2 = ((rb"objects\pc2\male\fx_idvritra01a_n.dds", rb"objects\items\fx_idvritra01a_n.dds"),
                (rb"objects\pc2\male\fx_idvritra01a_p.dds", rb"objects\items\fx_idvritra01a_p.dds"))


def troca_caminho_fixo(dados, antigo, novo):
    """Troca um caminho num campo de tamanho fixo (completado com zeros), sem mudar o tamanho."""
    achados = [i for i in range(len(dados)) if dados.lower().startswith(antigo.lower(), i)]
    if len(achados) != 1:
        raise ValueError(f"{antigo!r}: {len(achados)} ocorrencias")
    i = achados[0]
    if len(novo) > len(antigo) or dados[i + len(antigo)] != 0:
        raise ValueError(f"{antigo!r}: campo inesperado")
    saida = bytearray(dados)
    saida[i:i + len(antigo)] = novo + bytes(len(antigo) - len(novo))
    return bytes(saida)


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


#: Campos de classe do `client_items` (nivel minimo por classe; 0 = nao pode) que o 5.0 tem. O 5.8 tem
#: tambem `artist` e `bard` (e os `*_max`), que o cliente 5.0 passa a ler pelo `harp_fix.h` (tabela de
#: campos do ItemTable). Regra do 5.8, medida nos itens dele: com o mesmo nivel em todas as classes, o
#: `bard` e esse nivel (35.829 contra 231); item de outras classes (armas, livros de skill) tem `bard` 0;
#: `artist` e igual ao `bard` (99,4%). O nivel sai sempre dos dados do 5.0 (o 5.8 mudou niveis de itens);
#: do 5.8 vem so se o Bard pode usar o item, quando o item existe la.
CLASSES_DO_ITEM_50 = ("warrior", "fighter", "knight", "scout", "assassin", "ranger", "mage", "wizard",
                      "elementalist", "cleric", "priest", "chanter", "monk", "thunderer", "striker",
                      "battlemaster", "orchestrator", "lumines", "engineer", "gunner", "runewarrior",
                      "runeblade")
CAMPOS_DO_BARD = ("artist", "bard")
ARQUIVOS_DE_ITENS_58 = r"Data\Items\Items.pak"


@lru_cache(maxsize=None)
def _bard_pode_no_58():
    """{id: o Bard pode usar} de todos os `client_items_*.xml` do 5.8 limpo."""
    import aion_bxml
    d, idx = aion_pak.abre(os.path.join(LIVE_CLIENTE, ARQUIVOS_DE_ITENS_58))
    saida = {}
    for e in idx:
        nome = e.nome.lower()
        if not (nome.startswith("client_items") and nome.endswith(".xml")):
            continue
        bruto = aion_pak.le(d, e)
        texto = aion_bxml.decodifica(bruto) if bruto[:1] == b"\x80" else bruto.decode("utf-8", "replace")
        for m in re.finditer(r"<client_item>\s*<id>(\d+)</id>(.*?)</client_item>", texto, re.S):
            bard = re.search(r"<bard>(\d+)</bard>", m.group(2))
            if bard:
                saida[int(m.group(1))] = bard.group(1) != "0"
    return saida


def _mais_comum(valores):
    contagem = {}
    for v in valores:
        contagem[v] = contagem.get(v, 0) + 1
    return max(sorted(contagem), key=lambda v: contagem[v]) if contagem else None


def campos_de_classe_do_bard(bxml, ids_do_bard=()):
    """`client_items.xml` binario com `artist`/`bard` (e `artist_max`/`bard_max`, se o item tem os
    `*_max` de classe) em todo item. Os ids de `ids_do_bard` (harpa, set do Bard) o Bard sempre pode usar.
    Devolve os bytes e um resumo {origem da regra: itens}."""
    if bxml[0] != 0x80:
        raise ValueError("nao e XML binario")
    tam, o = _varint(bxml, 1)
    tab = _Tabela(bxml[o:o + tam])
    o += tam
    raiz, fim = _le_elemento(bxml, o)
    if fim != len(bxml):
        raise ValueError("sobraram bytes depois da raiz")
    texto, indice, pos = {}, {}, 0
    for parte in bytes(tab.bruto).decode("utf-16le").split("\0")[:-1]:
        texto[pos] = parte
        indice.setdefault(parte, pos)
        pos += len(parte.encode("utf-16le")) // 2 + 1

    def idx(s):
        if s not in indice:
            indice[s] = tab.acrescenta(s)
        return indice[s]

    pode58, ids_do_bard = _bard_pode_no_58(), set(ids_do_bard)
    resumo = {}
    for item in raiz[3]:
        if texto[item[0]] != "client_item":
            continue
        campos = {texto[f[0]]: texto[f[1]] for f in item[3] if f[1] is not None}
        if any(c in campos for c in CAMPOS_DO_BARD):
            raise ValueError(f"item {campos.get('id')} ja tem campo do Bard")
        id_item = int(campos["id"])
        niveis = [campos[c] for c in CLASSES_DO_ITEM_50 if c in campos]
        nivel = _mais_comum([n for n in niveis if n != "0"])
        if id_item in ids_do_bard:
            origem, pode = "item do Bard", True
        elif id_item in pode58:
            origem, pode = "5.8", pode58[id_item]
        else:
            origem, pode = "regra (generico)", len(niveis) == len(CLASSES_DO_ITEM_50) and len(set(niveis)) == 1
        valor = nivel if pode and nivel else "0"
        resumo[(origem, valor != "0")] = resumo.get((origem, valor != "0"), 0) + 1
        novos = [(idx(c), idx(valor), [], []) for c in CAMPOS_DO_BARD]
        maximos = [campos[c + "_max"] for c in CLASSES_DO_ITEM_50 if c + "_max" in campos]
        if maximos and valor != "0":
            maximo = _mais_comum(maximos)
            novos += [(idx(c + "_max"), idx(maximo), [], []) for c in CAMPOS_DO_BARD]
        item[3].extend(novos)
    saida = bytes([0x80]) + _grava_varint(len(tab.bruto)) + bytes(tab.bruto) + _grava_elemento(raiz)
    return saida, resumo


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

    previa = any(id_novo == item[1] for item in ITENS_DA_PREVIA)
    troca = {"id": str(id_novo), "name": nome_novo, "desc": DESC_DO_ITEM, "mesh": mesh,
             "weapon_type": TIPO_DE_ARMA,
             "icon_name": ICONE, **ATAQUE_CLIENTE}
    if previa:
        # No Live, as duas harpas da criacao nomeiam explicitamente o osso da harpa.
        # O orbe usado como molde nao tem esses campos; sem eles a previa herda o
        # encaixe generico do Classic e a varinha fica fora da pose da harpa.
        troca.update(material="mat_bow_m", ui_sound_type="Sounds/item/item_att_harp",
                     equip_bone="Lhand_bone", combat_equip_bone="Lhand_bone")
    campos_base = {tab.texto(nome) for nome, _texto, _atributos, _netos in base[3]}
    filhos = []
    for nome, texto, atributos, netos in base[3]:
        n = tab.texto(nome)
        if n in TIRA_FILHOS or (previa and n in ("blade_fx", "trail_tex")):
            continue
        if n in troca:
            texto = tab.acrescenta(troca[n])
        filhos.append((nome, texto, atributos, netos))
        if previa and n == "icon_name":
            for campo in ("equip_bone", "combat_equip_bone"):
                if campo not in campos_base:
                    filhos.append((tab.acrescenta(campo), tab.acrescenta("Lhand_bone"), [], []))
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


class NoBxml:
    """Elemento de um XML binario aberto por [`edita_bxml`]: nome, texto, atributos e filhos."""

    def __init__(self, tab, nome, texto=None, atributos=None, filhos=None):
        self._tab, self._nome, self._texto = tab, nome, texto
        self._attrs = list(atributos or [])
        self.filhos = list(filhos or [])

    @property
    def nome(self):
        return self._tab.texto(self._nome)

    def get(self, chave, padrao=None):
        for k, v in self._attrs:
            if self._tab.texto(k) == chave:
                return self._tab.texto(v)
        return padrao

    def set(self, chave, valor):
        for i, (k, _v) in enumerate(self._attrs):
            if self._tab.texto(k) == chave:
                self._attrs[i] = (k, self._tab.indice(valor))
                return
        self._attrs.append((self._tab.indice(chave), self._tab.indice(valor)))

    def novo(self, nome, **atributos):
        """Elemento novo (sem pai); os atributos na ordem dada."""
        return NoBxml(self._tab, self._tab.indice(nome), None,
                      [(self._tab.indice(k), self._tab.indice(v)) for k, v in atributos.items()])

    def procura(self, **atributos):
        """Primeiro descendente (ou o proprio) com esses atributos."""
        if all(self.get(k) == v for k, v in atributos.items()):
            return self
        for f in self.filhos:
            achado = f.procura(**atributos)
            if achado:
                return achado
        return None

    def _tupla(self):
        return (self._nome, self._texto, self._attrs, [f._tupla() for f in self.filhos])


def edita_bxml(bxml, editor):
    """Abre um XML binario, chama `editor(raiz)` (um [`NoBxml`]) e devolve os bytes regravados.

    A tabela de strings original fica como esta; as strings novas vao para o fim dela.
    """
    if bxml[0] != 0x80:
        raise ValueError("nao e XML binario")
    tam, o = _varint(bxml, 1)
    tab = _Tabela(bxml[o:o + tam])
    o += tam
    tupla, fim = _le_elemento(bxml, o)
    if fim != len(bxml):
        raise ValueError("sobraram bytes depois da raiz")
    indice, pos = {}, 0
    for parte in bytes(tab.bruto).decode("utf-16le").split("\0")[:-1]:
        indice.setdefault(parte, pos)
        pos += len(parte.encode("utf-16le")) // 2 + 1

    def idx(s):
        if s not in indice:
            indice[s] = tab.acrescenta(s)
        return indice[s]
    tab.indice = idx

    def no(t):
        return NoBxml(tab, t[0], t[1], t[2], [no(f) for f in t[3]])
    raiz = no(tupla)
    editor(raiz)
    return bytes([0x80]) + _grava_varint(len(tab.bruto)) + bytes(tab.bruto) + _grava_elemento(raiz._tupla())


def acrescenta_previa_elyos_feminina(bxml):
    """Acrescenta o item feminino a um client_items.xml ja instalado, preservando os outros itens."""
    def editor(raiz):
        base = None
        for item in raiz.filhos:
            if item.nome != "client_item":
                continue
            identificador = next((f for f in item.filhos if f.nome == "id"), None)
            if identificador is None:
                continue
            numero = int(raiz._tab.texto(identificador._texto))
            if numero == 102099908:
                raise ValueError("item feminino Elyos ja existe no client_items.xml")
            if numero == 102000908:
                base = item
        if base is None:
            raise ValueError("item-base da previa Elyos 102000908 ausente")

        def copia(no):
            return NoBxml(raiz._tab, no._nome, no._texto, no._attrs, [copia(f) for f in no.filhos])

        item = copia(base)
        valores = {"id": "102099908", "name": "npc_harp_best_01_elyos_f",
                   "mesh": "HA_IDRun01a_ElyosF", "material": "mat_bow_m",
                   "ui_sound_type": "Sounds/item/item_att_harp",
                   "equip_bone": "Lhand_bone", "combat_equip_bone": "Lhand_bone"}
        item.filhos = [f for f in item.filhos if f.nome not in ("blade_fx", "trail_tex")]
        presentes = set()
        for f in item.filhos:
            if f.nome in valores:
                f._texto = raiz._tab.indice(valores[f.nome])
                presentes.add(f.nome)
        indice = next(i for i, f in enumerate(item.filhos) if f.nome == "icon_name") + 1
        for campo in ("equip_bone", "combat_equip_bone"):
            if campo not in presentes:
                item.filhos.insert(indice, NoBxml(raiz._tab, raiz._tab.indice(campo),
                                                 raiz._tab.indice(valores[campo])))
                indice += 1
        if presentes | {"equip_bone", "combat_equip_bone"} != set(valores):
            raise ValueError("item-base da previa Elyos nao tem os campos esperados")
        raiz.filhos.append(item)

    return edita_bxml(bxml, editor)


def troca_skinrefs(bxml, preset, por_estado):
    """Troca o `name` de `<SkinRef state=N>` de um `<Preset name=preset>` (XML binario).

    `por_estado = {"20": "v4_class_bard", ...}`. O documento e relido e regravado inteiro; as
    strings novas vao para o fim da tabela.
    """
    if bxml[0] != 0x80:
        raise ValueError("nao e XML binario")
    tam, o = _varint(bxml, 1)
    tab = _Tabela(bxml[o:o + tam])
    o += tam
    raiz, fim = _le_elemento(bxml, o)
    if fim != len(bxml):
        raise ValueError("sobraram bytes depois da raiz")
    trocados = set()

    def atributo(el, nome):
        for k, v in el[2]:
            if tab.texto(k) == nome:
                return tab.texto(v)
        return None

    def troca(el):
        nome, texto, atributos, filhos = el
        if tab.texto(nome) == "Preset" and atributo(el, "name") == preset:
            novos = []
            for f in filhos:
                estado = atributo(f, "state")
                if tab.texto(f[0]) == "SkinRef" and estado in por_estado:
                    attrs = [(k, tab.acrescenta(por_estado[estado]) if tab.texto(k) == "name" else v)
                             for k, v in f[2]]
                    f = (f[0], f[1], attrs, f[3])
                    trocados.add(estado)
                novos.append(f)
            return (nome, texto, atributos, novos)
        return (nome, texto, atributos, [troca(f) for f in filhos])

    raiz = troca(raiz)
    if trocados != set(por_estado):
        raise ValueError(f"Preset {preset}: estados nao achados {sorted(set(por_estado) - trocados)}")
    return bytes([0x80]) + _grava_varint(len(tab.bruto)) + bytes(tab.bruto) + _grava_elemento(raiz)


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
    if not flags & 4 or flags > 7:
        raise ValueError(f"raiz com flags {flags}, esperava filhos")
    # Texto e atributos da raiz (ex.: <Preload name=...>) ficam como estao; so o contador muda.
    if flags & 1:
        _texto, o = _varint(bxml, o)
    if flags & 2:
        n, o = _varint(bxml, o)
        for _ in range(2 * n):
            _x, o = _varint(bxml, o)
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


#: O cliente guarda as tabelas de dados ja convertidas em `data\dump\tables.dmp` e, com
#: `ValidTableDump=1` no `config.ini` ao lado, nao rele os XMLs dos paks (nem passa pelos hooks de
#: conversao do `harp_fix.h`). Todo pak gravado aqui invalida o cache: o proximo boot remonta.
CONFIG_DO_CACHE = r"data\dump\config.ini"


def _invalida_cache_de_tabelas():
    caminho = os.path.join(CLIENTE, CONFIG_DO_CACHE)
    if not os.path.exists(caminho):
        return
    with open(caminho, encoding="latin-1") as f:
        texto = f.read()
    novo = re.sub(r"(?m)^ValidTableDump=1\s*$", "ValidTableDump=0", texto)
    if novo != texto:
        with open(caminho, "w", encoding="latin-1", newline="") as f:
            f.write(novo)
        print(f"OK  {CONFIG_DO_CACHE}: ValidTableDump=0 (o cliente remonta o tables.dmp)")


def _backup(caminho):
    _invalida_cache_de_tabelas()  # todo pak gravado passa por aqui antes
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
    # Grupo da arma no servidor (o clone vem do orbe) e o nome que vai nos pacotes: o mesmo
    # STR_TEST_HARP_58 que o `client_items.xml` usa.
    for atributo, valor in (("item_group", "HARP"), ("desc", str(ID_DO_NOME_DO_ITEM))):
        novo, n = re.subn(r'\b%s="[^"]*"' % atributo, f'{atributo}="{valor}"', novo, count=1)
        if n != 1:
            raise ValueError(f"{caminho}: o template-base nao tem {atributo}")
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


# --------------------------------------------------------------------------------------------
# Set inicial do Bard (Novice Songweaver): clone do set Novice Luminess (atributos) com a malha, o
# icone e as cores do set Novice Sorcerer. O Lumines01a so tem corpo feminino (LFRB_/DFRB_, nem o 5.8
# tem o masculino) e o item e gender_permitted female: o Bard masculino ficava invisivel. A malha
# RB_R105/RB_C002 do Sorcerer e "all". Ids livres no cliente e no servidor.
# --------------------------------------------------------------------------------------------
SET_INICIAL_DO_BARD = (  # (Novice Luminess, Novice Sorcerer = malha/icone/cor, id novo)
    (110101549, 110101547, 110199549), (113101435, 113101433, 113199435), (112101376, 112101374, 112199376),
    (111101417, 111101415, 111199417), (114101465, 114101463, 114199465), (125003451, 125003449, 125101451))
ID_BASE_STRING_DO_SET = 1991960
ARQUIVO_STRINGS_DE_ITEM = "strings/client_strings_item2.xml"
#: Campos que vem do Sorcerer (o que ele nao tem sai do clone): a tunica da Luminess tem visual_slot
#: "torso leg" (vestido, ocupa a perna) e escondia a calca do Bard; a do Sorcerer nao tem.
CAMPOS_DO_MOLDE = ("mesh", "icon_name", "gender_permitted", "default_color_m", "default_color_f", "visual_slot")
PLAYER_INITIAL_DATA = (
    r"Código Fonte - Emulador\game-server\data\static_data\player_initial_data.xml",
    r"Emulador - Produto Final\GameServer\data\static_data\player_initial_data.xml",
)


def _campos_do_item(xml, id_item):
    m = re.search(r"<client_item>\s*<id>%d</id>.*?</client_item>" % id_item, xml, re.S)
    if not m:
        raise ValueError(f"item {id_item} nao esta no client_items")
    return dict(re.findall(r"<([a-z_0-9]+)>([^<]*)</\1>", m.group(0)))


@lru_cache(maxsize=None)
def _itens_originais():
    """O client_items.xml original (backup) do pak da Europa, decodificado."""
    import aion_bxml
    caminho = os.path.join(CLIENTE, r"data\europe\Items\Items.pak")
    origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
    d, idx = aion_pak.abre(origem)
    return aion_bxml.decodifica(aion_pak.le(d, next(e for e in idx if e.nome.lower() == "client_items.xml")))


@lru_cache(maxsize=None)
def STRINGS_DO_SET():
    """Nome de cada peca: o da peca da Luminess no 5.0, com Songweaver (STR_CLASS_NAME_BARD) no lugar."""
    import aion_bxml
    caminho = os.path.join(CLIENTE, r"l10n\ENG\Data\Data.pak")
    origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
    d, idx = aion_pak.abre(origem)
    texto = aion_bxml.decodifica(aion_pak.le(d, next(e for e in idx if e.nome.lower() == ARQUIVO_STRINGS_DE_ITEM)))
    saida = []
    for k, (lum, _sor, _novo) in enumerate(SET_INICIAL_DO_BARD):
        desc = _campos_do_item(_itens_originais(), lum)["desc"]
        corpo = re.search(r"<name>%s</name>\s*<body>([^<]*)</body>" % re.escape(desc), texto, re.I).group(1)
        if "Luminess’" not in corpo:
            raise ValueError(f"{desc}: nome sem 'Luminess’': {corpo}")
        nome = desc.replace("_LUMINES_", "_BARD_")
        corpo = corpo.replace("Luminess’", "Songweaver’s")
        saida.append((ARQUIVO_STRINGS_DE_ITEM, ID_BASE_STRING_DO_SET + k, nome,
                      {lingua: corpo for lingua in ("ENG", "DEU", "FRA", "BRA")}))
    return tuple(saida)


def _troca_do_set():
    """{id novo: (id base, {campo: valor})} do client_item de cada peca."""
    xml = _itens_originais()
    textos = {nome: id_string for _a, id_string, nome, _t in STRINGS_DO_SET()}
    saida = {}
    for lum, sor, novo in SET_INICIAL_DO_BARD:
        base, molde = _campos_do_item(xml, lum), _campos_do_item(xml, sor)
        desc = base["desc"].replace("_LUMINES_", "_BARD_")
        assert desc in textos
        troca = {"id": str(novo), "name": base["name"].replace("_lumines_", "_bard_"), "desc": desc}
        troca.update({c: molde.get(c) for c in CAMPOS_DO_MOLDE if c in molde or c in base})  # None = tirar
        saida[novo] = (lum, troca)
    return saida


def clona_item(bxml, id_base, id_novo, troca):
    """`client_items.xml` binario com um clone do item `id_base`, trocando os campos de `troca`
    (valor None tira o campo do clone)."""
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
    base, ids, posicoes = None, [], []
    for _ in range(quantos):
        posicoes.append(o)
        item, o = _le_elemento(bxml, o)
        id_item = next((int(tab.texto(t)) for n, t, _a, _f in item[3] if tab.texto(n) == "id"), None)
        ids.append(id_item)
        if id_item == id_base:
            base = item
        if id_item == id_novo:
            raise ValueError(f"o id {id_novo} ja existe neste arquivo")
    if base is None:
        raise ValueError(f"item-base {id_base} nao encontrado")
    faltam = set(troca)
    filhos = []
    for nome, texto, atributos, netos in base[3]:
        n = tab.texto(nome)
        if n in troca:
            faltam.discard(n)
            if troca[n] is None:
                continue
            texto = tab.acrescenta(troca[n])
        filhos.append((nome, texto, atributos, netos))
    faltam = {c for c in faltam if troca[c] is not None}
    if faltam:
        raise ValueError(f"item-base {id_base} sem os campos {sorted(faltam)}")
    novo = (base[0], base[1], base[2], filhos)
    ordenado = all(a <= b for a, b in zip(ids, ids[1:]))
    corte = len(bxml)
    if ordenado:
        corte = next((pos for pos, i in zip(posicoes, ids) if i > id_novo), len(bxml))
    saida = bytearray([0x80])
    saida += _grava_varint(len(tab.bruto)) + tab.bruto
    saida += bxml[ini_raiz:pos_contador] + _grava_varint(quantos + 1)
    saida += bxml[pos_contador + len(_grava_varint(quantos)):corte]
    saida += _grava_elemento(novo)
    saida += bxml[corte:]
    return bytes(saida)


def aplica_set_do_bard_servidor():
    """item_template de cada peca (clone da Luminess, com o nome novo) e o BARD do player_initial_data."""
    textos = {nome: (id_string, t["ENG"]) for _a, id_string, nome, t in STRINGS_DO_SET()}
    for rel in TEMPLATES:
        caminho = os.path.join(REPO, rel)
        with open(caminho, "rb") as f:
            texto = f.read().decode("utf-8")
        for novo, (lum, troca) in _troca_do_set().items():
            texto = re.sub(_BLOCO % novo, "", texto, flags=re.S)  # o clone e refeito a cada vez
            m = re.search(_BLOCO % lum, texto, re.S)
            id_string, nome_en = textos[troca["desc"]]
            bloco = m.group(0).replace(f'id="{lum}"', f'id="{novo}"', 1)
            for atributo, valor in (("name_en", nome_en), ("name_pt", nome_en), ("cName", troca["name"]),
                                    ("desc", str(id_string))):
                bloco, n = re.subn(r'\b%s="[^"]*"' % atributo, f'{atributo}="{valor}"', bloco, count=1)
                if n != 1:
                    raise ValueError(f"{rel}: o template {lum} nao tem {atributo}")
            texto = texto[:m.end()] + bloco + texto[m.end():]
        with open(caminho, "wb") as f:
            f.write(texto.encode("utf-8"))
        print(f"OK  {rel}: +{len(SET_INICIAL_DO_BARD)} pecas do set Novice Songweaver")
    for rel in PLAYER_INITIAL_DATA:
        caminho = os.path.join(REPO, rel)
        with open(caminho, encoding="utf-8", newline="") as f:
            texto = f.read()
        eol = "\r\n" if "\r\n" in texto[:4096] else "\n"
        texto = re.sub(r"\t<!-- Bard: .*?</player_data>" + re.escape(eol), "", texto, flags=re.S)
        lum = re.search(r'\t<player_data class="LUMINESS">.*?</player_data>', texto, re.S).group(0)
        bard = lum.replace('class="LUMINESS"', 'class="BARD"')
        bard = bard.replace('<item id="102600408" count="1" />',
                            f'<item id="{VARIANTES[0][1]}" count="1" /> <!-- harpa de teste 5.8 (tipo 19) -->')
        for lum_id, _sor, novo in SET_INICIAL_DO_BARD:
            assert f'<item id="{lum_id}" count="1" />' in bard, lum_id
            bard = bard.replace(f'<item id="{lum_id}" count="1" />', f'<item id="{novo}" count="1" />')
        bloco = ("\t<!-- Bard: como a Luminess (a posicao 10 da tela de criacao), com a harpa no lugar da arma "
                 "e o set Novice Songweaver (malha do Sorcerer, os dois sexos); o 5.8 nao traz tabela de itens "
                 "iniciais no cliente. -->" + eol + bard + eol)
        fim = texto.rindex("</player_initial_data>")
        texto = texto[:fim] + bloco + texto[fim:]
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(texto)
        print(f"OK  {rel}: BARD com a harpa e o set Novice Songweaver")


#: Barra de atalhos inicial (`pc\client_default_key.xml`): 36 teclas por classe (1-12 a linha de baixo,
#: 13-24 a do Alt, 25-36 a do Ctrl), achadas pelo indice da classe na tela de criacao (0x9CBDF0 le o
#: `class`, 0x652460 procura pela classe do personagem). O Bard nao tinha linhas nem indice e recebia
#: as da Luminess; o `harp_fix.h` da a ele o indice 13 so nessa tabela. O 5.8 nao tem essa tabela: as
#: linhas comuns sao as da Luminess (ataque, itens de iniciante, Mending, Aromatherapy, pegar item,
#: descansar, voltar para casa) e, como nas outras classes, entram so as skills que o personagem ja
#: tem ao nascer: o Pulse.
PAK_DA_BARRA_INICIAL = r"data\PC\PC.pak"
CLASSE_MOLDE_DA_BARRA = "Lumines"
PREFIXO_DO_MOLDE = "LU_"
SKILLS_DA_BARRA_DO_BARD = {"2": "Ar_SongofAir_G1"}


def barra_inicial_do_bard(bxml):
    """`client_default_key.xml` binario com as 36 linhas do Bard (classe `Bard`, ids depois do maior)."""
    def editor(raiz):
        tab = raiz._tab

        def campos(no):
            return {tab.texto(f._nome): (tab.texto(f._texto) if f._texto is not None else None) for f in no.filhos}

        linhas = [n for n in raiz.filhos if n.nome == "client_default_key"]
        if any((campos(n).get("class") or "").lower() == "bard" for n in linhas):
            raise ValueError("client_default_key ja tem o Bard")
        molde = [campos(n) for n in linhas if campos(n).get("class") == CLASSE_MOLDE_DA_BARRA]
        if len(molde) != 36:
            raise ValueError(f"{CLASSE_MOLDE_DA_BARRA}: {len(molde)} linhas, esperava 36")
        proximo = max(int(campos(n)["id"]) for n in linhas) + 1
        for i, c in enumerate(sorted(molde, key=lambda c: int(c["key_value"]))):
            tecla = c["key_value"]
            skill = SKILLS_DA_BARRA_DO_BARD.get(tecla)
            if skill is None and c.get("skill_name") and not c["skill_name"].startswith(PREFIXO_DO_MOLDE):
                skill = c["skill_name"]
            valores = [("id", str(proximo + i)), ("name", f"Bard{tecla}"), ("class", "Bard"), ("key_value", tecla)]
            if skill:
                valores.append(("skill_name", skill))
            linha = raiz.novo("client_default_key")
            linha.filhos = [NoBxml(tab, tab.indice(k), tab.indice(v)) for k, v in valores]
            raiz.filhos.append(linha)
    return edita_bxml(bxml, editor)


def aplica_barra_inicial():
    import aion_bxml
    caminho = os.path.join(CLIENTE, PAK_DA_BARRA_INICIAL)
    origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
    d, idx = aion_pak.abre(origem)
    entrada = next(e for e in idx if e.nome.lower() == "client_default_key.xml")
    novo = barra_inicial_do_bard(aion_pak.le(d, entrada))
    _backup(caminho)
    if origem != caminho:
        shutil.copy2(origem, caminho)
    regrava_pak(caminho, troca={entrada.nome: novo})
    _confere_pak(caminho, len(idx), {entrada.nome: "troca"})
    d2, idx2 = aion_pak.abre(caminho)
    xml = aion_bxml.decodifica(aion_pak.le(d2, next(e for e in idx2 if e.nome == entrada.nome)))
    linhas = re.findall(r"<client_default_key>(.*?)</client_default_key>", xml, re.S)
    bard = [l for l in linhas if "<class>Bard</class>" in l]
    assert len(bard) == 36 and any("<skill_name>Ar_SongofAir_G1</skill_name>" in l for l in bard)
    assert not any(PREFIXO_DO_MOLDE in l for l in bard)
    print(f"OK  {PAK_DA_BARRA_INICIAL}: client_default_key.xml com as 36 teclas do Bard "
          f"({sum('<skill_name>' in l for l in bard)} com atalho)")


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
        for id_base, id_novo, nome, mesh in [v[:4] for v in VARIANTES] + list(ITENS_DA_PREVIA):
            novo, n, ordenado = acrescenta_item(novo, id_base, id_novo, nome, mesh)
            quantos = n if quantos is None else quantos
        set_do_bard = _troca_do_set()
        for id_novo, (id_base, troca) in set_do_bard.items():  # na mesma gravacao (o pak sai do backup)
            novo = clona_item(novo, id_base, id_novo, troca)
        ids_do_bard = [v[1] for v in VARIANTES] + [v[1] for v in ITENS_DA_PREVIA] + list(set_do_bard)
        novo, resumo = campos_de_classe_do_bard(novo, ids_do_bard)
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
        novos_itens = [v[:4] for v in VARIANTES] + list(ITENS_DA_PREVIA)
        assert xml.count("<client_item>") == quantos + len(novos_itens) + len(set_do_bard)
        for _b, id_novo, _n, mesh in novos_itens:
            assert f"<id>{id_novo}</id>" in xml and f"<mesh>{mesh}</mesh>" in xml
        for id_novo, (_b, troca) in set_do_bard.items():
            campos = _campos_do_item(xml, id_novo)
            assert all(campos.get(c) == v for c, v in troca.items()), (rel, id_novo)
        assert xml.count("<bard>") == xml.count("<client_item>") == xml.count("<artist>")
        for id_novo in ids_do_bard:
            assert _campos_do_item(xml, id_novo).get("bard", "0") != "0", (rel, id_novo)
        print(f"OK  {rel}: {quantos} -> {quantos + len(novos_itens) + len(set_do_bard)} itens "
              f"(harpa e set Novice Songweaver; ordenado por id: {ordenado})")
        print(f"    artist/bard: " + ", ".join(f"{o} {'pode' if p else 'nao pode'} {n}"
                                               for (o, p), n in sorted(resumo.items())))

    for rel, nomes in ((PAK_MESH, MESHES + MESHES_DA_PREVIA), (PAK_TEXTURA, TEXTURAS + TEXTURAS_DA_PREVIA)):
        caminho = os.path.join(CLIENTE, rel)
        novos = do_58(r"Objects\items", nomes)
        if len(novos) != len(nomes):
            raise ValueError(f"faltou no 5.8: {sorted(set(nomes) - set(novos))}")
        if rel == PAK_MESH:
            novos[MESH_ELYOS_F] = malha_harpa_elyos_feminina(novos["HA_IDRun01a.cgf"])
            for antigo, novo in CAMINHOS_PC2:
                novos["HA_IDVritra01a.cgf"] = troca_caminho_fixo(novos["HA_IDVritra01a.cgf"], antigo, novo)
        else:
            pc2 = do_58(r"Objects\PC2\male", TEXTURAS_PC2_DA_PREVIA)
            if len(pc2) != len(TEXTURAS_PC2_DA_PREVIA):
                raise ValueError(f"faltou no 5.8: {sorted(set(TEXTURAS_PC2_DA_PREVIA) - set(pc2))}")
            novos.update(pc2)
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
    aplica_set_do_bard_servidor()


def aplica_correcao_harpa_previa():
    """Instala apenas a malha e o item da harpa de criacao da Elyos feminina."""
    sys.setrecursionlimit(10000)
    mesh_pak = os.path.join(CLIENTE, PAK_MESH)
    dados, indice = aion_pak.abre(mesh_pak)
    por_nome = {e.nome.lower(): e for e in indice}
    if MESH_ELYOS_F.lower() in por_nome:
        raise ValueError(f"{MESH_ELYOS_F} ja existe; restaure o backup antes de reaplicar")
    original = aion_pak.le(dados, por_nome["ha_idrun01a.cgf"])
    malha = malha_harpa_elyos_feminina(original)

    itens = []
    for rel in PAKS_DE_ITENS:
        caminho = os.path.join(CLIENTE, rel)
        dados, indice_itens = aion_pak.abre(caminho)
        entrada = next(e for e in indice_itens if e.nome.lower() == "client_items.xml")
        novo = acrescenta_previa_elyos_feminina(aion_pak.le(dados, entrada))
        itens.append((rel, caminho, len(indice_itens), entrada.nome, novo))

    sufixo = ".bak_elyos_harpa"
    for caminho in (mesh_pak, *(item[1] for item in itens)):
        if os.path.exists(caminho + sufixo):
            raise ValueError(f"backup da correcao ja existe: {caminho + sufixo}")

    shutil.copy2(mesh_pak, mesh_pak + sufixo)
    regrava_pak(mesh_pak, acrescenta={MESH_ELYOS_F: malha})
    _confere_pak(mesh_pak, len(indice), {MESH_ELYOS_F: "novo"})
    print(f"OK  {PAK_MESH}: +{MESH_ELYOS_F}")

    for rel, caminho, quantidade, nome, novo in itens:
        shutil.copy2(caminho, caminho + sufixo)
        regrava_pak(caminho, troca={nome: novo})
        _confere_pak(caminho, quantidade, {nome: "troca"})
        print(f"OK  {rel}: +item 102099908")
    _invalida_cache_de_tabelas()


def ajusta_altura_harpa_previa():
    """Substitui somente a malha feminina instalada com altura anterior conhecida."""
    caminho = os.path.join(CLIENTE, PAK_MESH)
    dados, indice = aion_pak.abre(caminho)
    por_nome = {e.nome.lower(): e for e in indice}
    feminina = por_nome[MESH_ELYOS_F.lower()]
    anterior = aion_pak.le(dados, feminina)
    versoes_anteriores = {
        "a484723f302cc6488fdcb31ab3a094948cfb0c194d5b436c0dc232247f2c1b14": "baixa",
        "f0c0bb798154da020ba09dffccb3fae31a60152dd2978b9802ce22fbf7fdb582": "alta",
        "e5447fd86d68787a96d60969757a9a83b340a0a440838209d2875627ab04de2b": "mao_varinha",
        "8bb3791c3cfb591a19b33e4ec0e1170cf26fe0f1c84ef5f097701143818bbec1": "deitada",
        "f4cbba1184a847ea5e9c8a5f38dece31b50d9683a8bc3e32a886b0e63be554dd": "recuada",
    }
    versao = versoes_anteriores.get(hashlib.sha256(anterior).hexdigest())
    if versao is None:
        raise ValueError("malha feminina instalada nao e a versao anterior esperada")
    original = aion_pak.le(dados, por_nome["ha_idrun01a.cgf"])
    corrigida = malha_harpa_elyos_feminina(original)
    backup = caminho + ".bak_elyos_harpa_altura_" + versao
    if os.path.exists(backup):
        raise ValueError(f"backup ja existe: {backup}")
    shutil.copy2(caminho, backup)
    regrava_pak(caminho, troca={feminina.nome: corrigida})
    _confere_pak(caminho, len(indice), {feminina.nome: "troca"})
    print(f"OK  {PAK_MESH}: {MESH_ELYOS_F} avancada 6 cm")


def _paks_de_animacao(raca="lm"):
    rel = os.path.join("objects", "pc", raca, "animation")
    pasta = os.path.join(CLIENTE, rel)
    return sorted(
        os.path.join(rel, a) for a in os.listdir(pasta) if a.lower().endswith(".pak")
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


def posicoes_de_referencia_50(raca="lm"):
    """Posicao local (em relacao ao osso pai) dos 12 ossos de dedo na bind pose do `<raca>.cgf` do 5.0."""
    caminho = os.path.join(CLIENTE, "objects", "pc", raca, "mesh", "Mesh_Meshes_000.pak")
    origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
    d, idx = aion_pak.abre(origem)
    cgf = aion_pak.le(d, next(e for e in idx if e.nome.lower() == f"{raca}.cgf"))
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
        raise ValueError(f"nem todos os ossos de dedo estao no {raca}.cgf do 5.0")
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
    "efeito": (PAK_EFEITOS, PAK_SOM_DO_PROJETIL, r"Sounds\effect\effect.pak"),
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


def entradas_oficiais_de_harpa(cafs, raca="lm"):
    """As entradas de harpa do `lm.cal` do Live 5.8, apontadas para arquivos que o 5.0 tem.

    Substitui a derivacao a partir das entradas de orbe ([`linhas_de_harpa`]), que errava em 69
    nomes (o ataque andando para tras, por exemplo, caia na animacao do orbe). Cada alvo e o
    `.caf` de harpa trazido do 5.8 quando e um deles; senao, o arquivo de mesmo nome que o
    proprio 5.0 ja tem (as animacoes genericas, que nao dependem da arma). Devolve
    `[(nome, caminho no formato do .cal, prob ou -1)]`.

    `raca` e a lista lida (`lm`, `lf`, `dm`, `df`). A pasta de cada alvo e a que o 5.8 aponta: la
    o DM usa as animacoes de harpa do LM e o DF as do LF. `cafs` sao os de harpa dessa pasta.
    """
    import glob
    cal = None
    for p in sorted(glob.glob(os.path.join(LIVE_CLIENTE, "Objects", "PC2", raca, "mesh", "*.pak"))):
        d, idx = aion_pak.abre(p)
        e = next((x for x in idx if x.nome.lower() == f"{raca}.cal"), None)
        if e:
            cal = aion_pak.le(d, e).decode("latin-1")
            break
    if cal is None:
        raise ValueError(f"nao achei o {raca}.cal do 5.8")
    harpa = {c.lower(): c for c in cafs}
    do50 = {}  # pasta -> {arquivo em minusculas: nome} dos paks originais do 5.0
    saida, sem_arquivo = [], []
    for linha in cal.splitlines():
        m = re.match(r"\s*([^\s=/][^\s=]*)\s*=\s*(\S+\.caf)(.*)", linha, re.I)
        if not m or "harp" not in m.group(1).lower():
            continue
        partes = m.group(2).replace("/", "\\").split("\\")
        arquivo, pasta = partes[-1], partes[-3].upper()
        if pasta not in do50:
            do50[pasta] = {}
            for rel in _paks_de_animacao(pasta.lower()):
                p = os.path.join(CLIENTE, rel)
                p = p + SUFIXO_BACKUP if os.path.exists(p + SUFIXO_BACKUP) else p
                for e in aion_pak.abre(p)[1]:
                    do50[pasta].setdefault(e.nome.lower(), e.nome)
        nome_real = harpa.get(arquivo.lower()) or do50[pasta].get(arquivo.lower())
        if not nome_real:
            sem_arquivo.append(m.group(1))
            continue
        prob = re.search(r"prob\s*=\s*([\d.]+)", m.group(3))
        # O .cab guarda a prob em float de 32 bits.
        prob = struct.unpack("<f", struct.pack("<f", float(prob.group(1))))[0] if prob else None
        saida.append((m.group(1), f"PC\\{pasta}\\Animation\\" + nome_real, prob if prob is not None else -1.0))
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

    _grava_listas("lm", _todas_as_entradas("lm"))


def _pak_da_lista(raca, extensao):
    """O pak de malhas da raca que guarda `<raca>.cal` ou `<raca>.cab` (o original, se ha backup)."""
    for rel in sorted(os.listdir(os.path.join(CLIENTE, "objects", "pc", raca, "mesh"))):
        if not rel.lower().endswith(".pak"):
            continue
        rel = os.path.join("objects", "pc", raca, "mesh", rel)
        caminho = os.path.join(CLIENTE, rel)
        origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
        d, idx = aion_pak.abre(origem)
        entrada = next((e for e in idx if e.nome.lower() == f"{raca}.{extensao}"), None)
        if entrada:
            return rel, caminho, origem, d, idx, entrada
    raise ValueError(f"nao achei o {raca}.{extensao} no 5.0")


def _grava_listas(raca, oficiais):
    """Declara as entradas de harpa no `<raca>.cal` e no `<raca>.cab` (a partir dos originais)."""
    import aion_cab
    rel, caminho, origem, d, idx, entrada = _pak_da_lista(raca, "cal")
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
    print(f"OK  {rel}: {raca}.cal com +{len(novas)} entradas de harpa")

    rel, caminho, origem, d, idx, entrada = _pak_da_lista(raca, "cab")
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
    print(f"OK  {rel}: {raca}.cab com +{len(novos)} registros de harpa ({len(registros)} no total)")


#: As outras racas. No 5.8 o DM usa as animacoes de harpa do LM e o DF as do LF (as listas
#: `dm.cal`/`df.cal` apontam para `PC2\LM` e `PC2\LF`); so o LF tem `.caf` proprios.
OUTRAS_RACAS = ("lf", "dm", "df")
PASTA_DAS_ANIMACOES = {"lm": "lm", "lf": "lf", "dm": "lm", "df": "lf"}
#: Pak que recebe os `.caf` de harpa do LF: a ultima do LF, como a 020 no LM.
PAK_ANIMACAO_LF = r"objects\pc\lf\animation\Animation_Animations_019.pak"


def cafs_de_harpa(pasta):
    """Os `.caf` de harpa do 5.8 de uma pasta de animacoes (`lm` ou `lf`)."""
    return sorted(a for a in os.listdir(LIVE_ANIMACAO)
                  if a.lower().startswith(pasta + "_") and a.lower().endswith(".caf"))


def aplica_animacao_lf():
    """Poe os `.caf` de harpa do LF, so com a posicao dos dedos trocada (a variante do LM)."""
    posicoes = posicoes_de_referencia_50("lf")
    novos = {}
    for a in cafs_de_harpa("lf"):
        with open(os.path.join(LIVE_ANIMACAO, a), "rb") as f:
            original = f.read()
        novos[a], _mexidas = so_posicao_dos_dedos(original, posicoes)
        valida_so_posicao(original, novos[a], posicoes)
    caminho = os.path.join(CLIENTE, PAK_ANIMACAO_LF)
    origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
    d0, idx0 = aion_pak.abre(origem)
    ja = {e.nome.lower() for e in idx0}
    repetidos = sorted(n for n in novos if n.lower() in ja)
    if repetidos:
        raise ValueError(f"{PAK_ANIMACAO_LF} ja tem {repetidos[:5]}")
    _backup(caminho)
    if origem != caminho:
        shutil.copy2(origem, caminho)
    regrava_pak(caminho, acrescenta=novos)
    # Releitura: os novos conferem byte a byte e as entradas antigas nao mudaram.
    d1, idx1 = aion_pak.abre(caminho)
    por_nome = {e.nome: e for e in idx1}
    for a, dados in novos.items():
        if aion_pak.le(d1, por_nome[a]) != dados:
            raise ValueError(f"{a}: o que saiu do pak nao e o que foi gravado")
    for e in idx0:
        if aion_pak.le(d0, e) != aion_pak.le(d1, por_nome[e.nome]):
            raise ValueError(f"{e.nome}: entrada antiga do pak mudou")
    print(f"OK  {PAK_ANIMACAO_LF}: +{len(novos)} animacoes de harpa (so a posicao dos dedos trocada)")


def aplica_racas():
    """Harpa no LF, DM e DF: animacoes do LF, listas das tres racas e marcadores das quatro."""
    aplica_animacao_lf()
    for raca in OUTRAS_RACAS:
        _grava_listas(raca, _todas_as_entradas(raca))
    aplica_marcadores(("lm",) + OUTRAS_RACAS)


# --------------------------------------------------------------------------------------------
# Animacoes da classe Bard (selecao, criacao, idle no mundo)
# --------------------------------------------------------------------------------------------
#
# O `Game.dll` monta o nome dessas animacoes com o sufixo da classe (Nidle_<classe>_lobby_001,
# Nselect_<classe>_lobby_001, Nidle_<classe>_create_001, nidle_<classe>_001...); o `harp_fix.h`
# acrescenta os sufixos "_artist" e "_bard" (classes 17 e 20). As entradas vem do `.cal` do 5.8,
# so as de nome que o 5.0 monta: as variantes por arma do lobby (Nidle_Bard_orb_lobby_001...) sao
# do Live, nenhuma classe do 5.0 as usa.

_TOKEN_DE_CLASSE = re.compile(r"(?i)(^|_)(bard|artist)(_|$)")
_ARMAS_DO_LOBBY = re.compile(
    r"(?i)_(1hand|dagger|mace|2hand|2weapon|staff|polearm|bow|orb|book|1gun|2gun|cannon|harp|"
    r"keyblade|noweapon)_lobby_")
#: Pak de cada pasta de animacao que recebe os `.caf` de classe. Nenhum outro passo mexe nele
#: (o LM 020 e o LF 019 sao os das animacoes de harpa, regravados por `--racas`/`--dedos-*`).
PAKS_DE_ANIMACAO_DE_CLASSE = {
    "lm": r"objects\pc\lm\animation\Animation_Animations_019.pak",
    "lf": r"objects\pc\lf\animation\Animation_Animations_018.pak",
    "dm": r"objects\pc\dm\animation\Animation_Animations_001.pak",
    "df": r"objects\pc\df\animation\Animation_Animations_001.pak",
}


#: Pose da tela de criacao dos Elyos: as animacoes LM/LF_Nidle_bard_create do 5.8 tem a pose do
#: outro sexo em relacao as DM/DF (braco direito 76 / 81 graus diferente); as DM/DF sao as certas
#: (Asmodianos conferidos em jogo). O Elyos usa as DM/DF, como o 5.0 ja faz entre LM e DM em outras
#: classes (esqueletos compativeis). Ver tambem COPIA_DA_SOMBRA (plataforma).
CRIACAO_DOS_ELYOS = {"lm": r"PC\DM\Animation\DM_Nidle_bard_create_001_loop.caf",
                     "lf": r"PC\DF\Animation\DF_Nidle_bard_create_001_loop.caf"}


def entradas_de_classe(raca):
    """As entradas do `<raca>.cal` do 5.8 com o nome da classe Bard/Artist, para o 5.0.

    Devolve `[(nome, caminho no formato do .cal, prob ou -1)]` e os `.caf` que elas pedem,
    `{pasta: {arquivo}}`.
    """
    import glob
    cal = None
    for p in sorted(glob.glob(os.path.join(LIVE_CLIENTE, "Objects", "PC2", raca, "mesh", "*.pak"))):
        d, idx = aion_pak.abre(p)
        e = next((x for x in idx if x.nome.lower() == f"{raca}.cal"), None)
        if e:
            cal = aion_pak.le(d, e).decode("latin-1")
            break
    saida, arquivos = [], {}
    for linha in cal.splitlines():
        m = re.match(r"\s*([^\s=/][^\s=]*)\s*=\s*(\S+\.caf)(.*)", linha, re.I)
        if not m or not _TOKEN_DE_CLASSE.search(m.group(1)) or "harp" in m.group(1).lower() \
                or _ARMAS_DO_LOBBY.search(m.group(1)):
            continue
        partes = m.group(2).replace("/", "\\").split("\\")
        arquivo, pasta = partes[-1], partes[-3].upper()
        prob = re.search(r"prob\s*=\s*([\d.]+)", m.group(3))
        prob = struct.unpack("<f", struct.pack("<f", float(prob.group(1))))[0] if prob else -1.0
        saida.append((m.group(1), f"PC\\{pasta}\\Animation\\{arquivo}", prob))
        arquivos.setdefault(pasta.lower(), set()).add(arquivo)
    if raca in CRIACAO_DOS_ELYOS:
        caminho = CRIACAO_DOS_ELYOS[raca]
        saida = [(n, caminho, p) if re.search(r"(?i)^nidle_(bard|artist)_create_\d+$", n) else (n, c, p)
                 for n, c, p in saida]
    return saida, arquivos


def _todas_as_entradas(raca):
    """Harpa + classe: o que vai no `<raca>.cal`/`.cab` (sempre os dois, numa gravacao so)."""
    harpa = entradas_oficiais_de_harpa(cafs_de_harpa(PASTA_DAS_ANIMACOES[raca]), raca)
    classe, _arquivos = entradas_de_classe(raca)
    nomes = {n.lower() for n, _a, _p in harpa}
    return harpa + [e for e in classe if e[0].lower() not in nomes]


def aplica_animacoes_de_classe():
    """Animacoes de selecao/criacao/idle do Bard nas quatro racas, listas e marcadores."""
    import glob
    pedidos = {}
    for raca in ("lm", "lf", "dm", "df"):
        for pasta, arquivos in entradas_de_classe(raca)[1].items():
            pedidos.setdefault(pasta, set()).update(arquivos)
    for pasta, arquivos in sorted(pedidos.items()):
        rel = PAKS_DE_ANIMACAO_DE_CLASSE[pasta]
        caminho = os.path.join(CLIENTE, rel)
        origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
        # O que o 5.0 ja tem nessa pasta (originais) nao vem do 5.8.
        tem = set()
        for p in glob.glob(os.path.join(CLIENTE, "objects", "pc", pasta, "animation", "*.pak")):
            q = p + SUFIXO_BACKUP if os.path.exists(p + SUFIXO_BACKUP) else p
            tem |= {e.nome.lower() for e in aion_pak.abre(q)[1]}
        faltam = sorted(a for a in arquivos if a.lower() not in tem)
        if not faltam:
            continue
        do58 = do_58(os.path.join("Objects", "PC2", pasta, "animation"), faltam)
        if len(do58) != len(faltam):
            raise ValueError(f"faltou no 5.8: {sorted(set(faltam) - set(do58))}")
        # Dedos: a mesma variante das animacoes de harpa (so a posicao, esqueleto da pasta).
        posicoes = posicoes_de_referencia_50(pasta)
        novos = {}
        for nome, dados in do58.items():
            novos[nome], _ = so_posicao_dos_dedos(dados, posicoes)
            valida_so_posicao(dados, novos[nome], posicoes)
        d0, idx0 = aion_pak.abre(origem)
        _backup(caminho)
        if origem != caminho:
            shutil.copy2(origem, caminho)
        regrava_pak(caminho, acrescenta=novos)
        d1, idx1 = aion_pak.abre(caminho)
        por_nome = {e.nome: e for e in idx1}
        for nome, dados in novos.items():
            if aion_pak.le(d1, por_nome[nome]) != dados:
                raise ValueError(f"{nome}: o que saiu do pak nao e o que foi gravado")
        if len(idx1) != len(idx0) + len(novos):
            raise ValueError(f"{rel}: contagem de entradas nao fecha")
        print(f"OK  {rel}: +{len(novos)} ({', '.join(sorted(novos))})")
    for raca in ("lm", "lf", "dm", "df"):
        _grava_listas(raca, _todas_as_entradas(raca))
    aplica_marcadores(("lm",) + OUTRAS_RACAS)


#: Efeito de interface da barra de carga (skills Charge), tocado pelo `charge_fix.h` como o 5.8 faz
#: (Game.dll 5.8 0x442470): o clarao na bolinha do estagio atingido. O `sys_uifx.prt` do 5.0 nao tem o
#: grupo Charge. O sys_UIfx.Charge.last do 5.8 (brilho da barra no ultimo estagio) fica de fora: no 5.0
#: ele se acumula a cada cast.
EFEITOS_DA_CARGA = ("sys_UIfx.Charge.basic",)


def animacoes_de_modelos(cgfs):
    """As animacoes do 5.8 que os modelos `cgfs` (caminhos objects\\...\\x.cgf) usam e o 5.0 nao tem.

    O CryAnimation.dll (5.0 e 5.8) le o `<modelo>.cal` da pasta do modelo; sem ele, procura
    `<modelo>_*.caf` ali mesmo (string "_*.caf") e toca a `nidle_001`. Sem os arquivos o modelo
    aparece parado: o sapo do Blazing Requiem (frog\\Ba_Frog_nidle_001.caf), o golfinho do Dragon Song
    (dolphin_fx.cal), as abelhas, borboletas, o corvo... Os .caf de um .cal sao relativos a Objects\\.
    Devolve `{pak relativo do 5.8: {entrada: dados}}`, no formato do `procura_58` do `aplica_efeito`.
    """
    import glob
    em58 = {}  # caminho completo (minusculo) -> (pak relativo, dados, entrada)
    for p in glob.glob(os.path.join(LIVE_CLIENTE, "Objects", "**", "*.pak"), recursive=True):
        try:
            d, idx = aion_pak.abre(p)
        except aion_pak.PakInvalido:
            continue
        rel = os.path.relpath(p, LIVE_CLIENTE)
        for e in idx:
            if e.nome.lower().endswith((".cal", ".caf")):
                caminho = os.path.join(os.path.dirname(rel), e.nome.replace("/", "\\")).lower()
                em58.setdefault(caminho, (rel, d, e))
    em50 = set()  # os originais (o backup, se ha), para o passo poder ser refeito
    for p in glob.glob(os.path.join(CLIENTE, "objects", "**", "*.pak"), recursive=True):
        q = p + SUFIXO_BACKUP if os.path.exists(p + SUFIXO_BACKUP) else p
        try:
            idx = aion_pak.abre(q)[1]
        except aion_pak.PakInvalido:
            continue
        pasta = os.path.relpath(os.path.dirname(p), CLIENTE)
        em50.update(os.path.join(pasta, e.nome.replace("/", "\\")).lower() for e in idx)
    pedidos = set()
    for cgf in cgfs:
        pasta, nome = os.path.dirname(cgf.lower()), os.path.basename(cgf.lower())[:-4]
        cal = os.path.join(pasta, nome + ".cal")
        if cal in em58:
            pedidos.add(cal)
            _rel, d, e = em58[cal]
            for caf in re.findall(r"=\s*(\S+\.caf)", aion_pak.le(d, e).decode("latin-1"), re.I):
                pedidos.add(os.path.join("objects", caf.replace("/", "\\")).lower())
        else:
            pedidos.update(k for k in em58 if os.path.dirname(k) == pasta and k.endswith(".caf")
                           and os.path.basename(k).startswith(nome + "_"))
    achados = {}
    for k in sorted(pedidos - em50):
        if k not in em58:
            continue  # o .cal do 5.8 cita animacoes que nem o 5.8 tem (FairyAngelPET_nwalk_001_loop)
        rel, d, e = em58[k]
        achados.setdefault(rel, {})[e.nome] = aion_pak.le(d, e)
    return achados


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
    efeitos = [aion_fx.nome(r) for r in aion_fx.le(fxc, b"FXC")[2]]
    biblioteca = efeitos[0].split(".", 1)[0]
    troca = {m50[PRT_DO_PROJETIL].nome: prt}
    acrescenta = {FXC_DO_PROJETIL: fxc}

    # Selecao do Bard: os efeitos FC_Sys_LoginStage.AR.* (com os filhos) no .fxc que o 5.0 ja tem,
    # e as particulas que eles citam -- em bibliotecas que o 5.0 tem (sys_lobby) ou nao
    # (skill_ba_songofrest, que vira arquivo novo so com o que e citado).
    fxc_lobby50 = aion_pak.le(d50, m50[FXC_DA_SELECAO])
    fxc_lobby58 = aion_pak.le(d58, m58[FXC_DA_SELECAO])
    raizes_lobby = [aion_fx.nome(r) for r in aion_fx.le(fxc_lobby58, b"FXC")[2]
                    if ".AR." in aion_fx.nome(r)
                    and struct.unpack_from("<i", r, aion_fx.FXC_PAI_58)[0] < 0]
    fxc_lobby, efeitos_lobby = aion_fx.acrescenta_fxc(fxc_lobby50, fxc_lobby58, raizes_lobby)
    troca[m50[FXC_DA_SELECAO].nome] = fxc_lobby
    citadas = set()
    for r in aion_fx.le(fxc_lobby58, b"FXC")[2]:
        if aion_fx.nome(r) in efeitos_lobby:
            citadas.update(s.decode("latin-1") for s in re.findall(rb"[\x20-\x7e]{4,}", r)
                           if b"." in s and not s.startswith(b"FC_Sys_LoginStage"))
    # Efeitos das skills do Bard: cada .fxc inteiro, e as particulas que os efeitos citam.
    bibliotecas_skills, efeitos_skills = [], []
    # Os .fxc das skills do Bard ja trazidas (bard_skills_58.LOTE), tirados dos campos *_fx delas:
    # o 5.0 nao tem nenhum; entram inteiros, com as particulas que citam (sons inclusive).
    import bard_skills_58
    fxc_das_skills = bard_skills_58.FXC_DAS_SKILLS()
    for chave_fxc in fxc_das_skills:
        if chave_fxc in m50:
            # Biblioteca que o 5.0 ja tem (fc_pr_restorelife do Cleric, fc_cast_evopoint): vale a do
            # 5.0, desde que tenha todo efeito que as skills citam.
            tem = {aion_fx.nome(r).lower() for r in aion_fx.le(aion_pak.le(d50, m50[chave_fxc]), b"FXC")[2]}
            biblioteca_lib = chave_fxc[4:-4]
            faltam = {v for v in bard_skills_58.EFEITOS_CITADOS()
                      if v.lower().startswith(biblioteca_lib + ".") and v.lower() not in tem}
            if faltam:
                raise ValueError(f"{chave_fxc} ja existe no 5.0, mas sem {sorted(faltam)}")
            continue
        fxc58_skill = aion_pak.le(d58, m58[chave_fxc])
        acrescenta[m58[chave_fxc].nome] = aion_fx.fxc_para_50(fxc58_skill)
        regs = aion_fx.le(fxc58_skill, b"FXC")[2]
        proprios = {aion_fx.nome(r) for r in regs}
        efeitos_skills += sorted(proprios)
        bibliotecas_skills.append(aion_fx.nome(regs[0]).split(".", 1)[0])
        for r in regs:
            citadas.update(c for c in (s.decode("latin-1") for s in re.findall(rb"[\x20-\x7e]{4,}", r))
                           if "." in c and c not in proprios)
    # Uma particula pode disparar outras pelo nome (campos de string sem caminho): as citadas que o
    # 5.0 nao tem entram tambem, sempre pela raiz da arvore delas no 5.8, ate fechar. Vale para as
    # particulas da harpa (sys_hit) e as da selecao.
    citadas.update(EFEITOS_DA_CARGA)
    prts = {PRT_DO_PROJETIL: prt}  # chave -> .prt do 5.0 ja com o que foi acrescentado

    def atual(chave):
        if chave in prts:
            return prts[chave]
        return aion_pak.le(d50, m50[chave]) if chave in m50 else None

    def nomes_de(dados):
        return {aion_fx.nome(r).lower() for r in aion_fx.le(dados, b"CRY")[2]} if dados else set()

    def citadas_por(dados, nomes):
        saida = set()
        for r in aion_fx.le(dados, b"CRY")[2]:
            if aion_fx.nome(r) in nomes:
                for i in range(1, 9):
                    s = r[i * 128:(i + 1) * 128].split(b"\0")[0].decode("latin-1")
                    if s and "\\" not in s and "/" not in s and "." in s:
                        saida.add(s)
        return saida

    particulas_lobby, sem_fonte = [], []
    pendentes = set(citadas) | citadas_por(prt, set(particulas))
    while pendentes:
        por_lib = {}
        for c in pendentes:
            por_lib.setdefault(f"prt/{c.split('.', 1)[0].lower()}.prt", set()).add(c)
        pendentes = set()
        for chave, nomes in sorted(por_lib.items()):
            ja = nomes_de(atual(chave))
            faltam = sorted(n for n in nomes if n.lower() not in ja)
            if not faltam:
                continue
            if chave not in m58:
                # Citada e sem fonte nem no 5.8 limpo (ex.: MON_Kaisinel_MRT.V3.ShockwaveTrap): fica
                # de fora, como no proprio 5.8.
                sem_fonte.extend(faltam)
                continue
            dados58 = aion_pak.le(d58, m58[chave])
            regs58 = aion_fx.le(dados58, b"CRY")[2]
            por_nome = {aion_fx.nome(r).lower(): i for i, r in enumerate(regs58)}
            raizes_novas = set()
            for n in faltam:
                i = por_nome.get(n.lower())
                if i is None:
                    # Biblioteca existe mas o nome nao, nem no 5.8 (fc_Ar_SongofAir cita
                    # skill_Ar_SongofCold.G1.fire_sp): fica de fora, como no proprio 5.8.
                    sem_fonte.append(n)
                    continue
                while struct.unpack_from("<i", regs58[i], aion_fx.PRT_PAI_58)[0] >= 0:
                    i = struct.unpack_from("<i", regs58[i], aion_fx.PRT_PAI_58)[0]
                raizes_novas.add(aion_fx.nome(regs58[i]))
            if not raizes_novas:
                continue
            novo, nomes_novos = aion_fx.acrescenta_prt(atual(chave), dados58, sorted(raizes_novas))
            prts[chave] = novo
            particulas_lobby += nomes_novos
            pendentes |= citadas_por(novo, set(nomes_novos))
    # Citadas sem .prt: podem ser materiais de efeito (mat/<biblioteca>.fxm, aplicados a meshes de
    # efeito, como BA_mrt_injury.v4.flow_line2). O registro do .fxm tem o mesmo leiaute nas duas
    # versoes (1936 bytes; os campos que diferem nos registros comuns sao lixo de memoria no 5.0 e
    # zero no 5.8); o 4o byte do cabecalho e 0 no 5.0 e 'h' no 5.8, e fica o do 5.0. Nao ha indice
    # de nomes de material.
    materiais = {}
    for n in sorted(set(sem_fonte)):
        chave = f"mat/{n.split('.', 1)[0].lower()}.fxm"
        if chave in m58 and chave not in m50:
            dados = bytearray(aion_pak.le(d58, m58[chave]))
            if dados[:3] != b"EFM" or (len(dados) - 9) != struct.unpack_from("<I", dados, 5)[0] * 1936:
                raise ValueError(f"{chave}: .fxm com formato inesperado")
            dados[3] = 0
            materiais[m58[chave].nome] = bytes(dados)
    if materiais:
        acrescenta.update(materiais)
        sem_fonte = [n for n in sem_fonte
                     if f"mat/{n.split('.', 1)[0].lower()}.fxm" not in {k.lower() for k in materiais}]
        print(f"    materiais de efeito: {', '.join(sorted(materiais))}")
    prt = prts[PRT_DO_PROJETIL]
    troca[m50[PRT_DO_PROJETIL].nome] = prt
    prts_novos = {k: v for k, v in prts.items() if k != PRT_DO_PROJETIL}
    for chave, novo in prts_novos.items():
        if chave in m50:
            troca[m50[chave].nome] = novo
        else:
            acrescenta[m58[chave].nome] = novo
    print(f"    selecao do Bard: {len(efeitos_lobby)} efeitos em {FXC_DA_SELECAO}, "
          f"{len(particulas_lobby)} particulas ({', '.join(sorted(prts_novos))})")
    if sem_fonte:
        print(f"    particulas citadas sem fonte nem no 5.8: {sorted(set(sem_fonte))}")

    # Sem entrada nos indices de nomes o efeito nao existe para o jogo (ver `aion_fx.py`).
    i_prt = aion_pak.le(d50, m50[INDICE_PRT])
    i_fxc = aion_pak.le(d50, m50[INDICE_FXC])
    i_prt58, i_fxc58 = aion_pak.le(d58, m58[INDICE_PRT]), aion_pak.le(d58, m58[INDICE_FXC])
    i_prt = aion_fx.indexa_prt(i_prt, i_prt58, particulas + particulas_lobby)
    i_fxc = aion_fx.indexa_fxc(i_fxc, i_fxc58, biblioteca)
    for lib in bibliotecas_skills:
        i_fxc = aion_fx.indexa_fxc(i_fxc, i_fxc58, lib)
    i_fxc = aion_fx.indexa_fxc_nomes(i_fxc, i_fxc58, efeitos_lobby)
    troca[m50[INDICE_PRT].nome] = i_prt
    troca[m50[INDICE_FXC].nome] = i_fxc

    _backup(caminho)
    if origem != caminho:
        shutil.copy2(origem, caminho)
    regrava_pak(caminho, troca=troca, acrescenta=acrescenta)
    _confere_pak(caminho, len(m50), {**{n: "troca" for n in troca}, **{n: "novo" for n in acrescenta}})
    print(f"    indices de nomes: +{len(particulas) + len(particulas_lobby)} em {INDICE_PRT}, "
          f"+{len(efeitos) + len(efeitos_lobby) + len(efeitos_skills)} em {INDICE_FXC}")
    print(f"OK  {PAK_EFEITOS}: {PRT_DO_PROJETIL} +{len(particulas)}, {FXC_DO_PROJETIL} novo, "
          f"{FXC_DA_SELECAO} +{len(efeitos_lobby)}, {', '.join(sorted(prts_novos))}")
    print(f"OK  efeitos das skills: {', '.join(fxc_das_skills)} ({len(efeitos_skills)} efeitos)")

    # Arquivos que essas particulas citam: texturas e meshes de efeito, e sons.
    citados = set()
    todas = set(particulas) | set(particulas_lobby)
    for dados, nomes in [(b, todas) for b in prts.values()]:
        for r in aion_fx.le(dados, b"CRY")[2]:
            if aion_fx.nome(r) in nomes:
                citados.update(r[i * 128:(i + 1) * 128].split(b"\0")[0].decode("latin-1")
                               for i in range(1, 9))
                citados.add(r[2718:2978].split(b"\0")[0].decode("latin-1"))
    for dados in materiais.values():
        citados.update(s.decode("latin-1") for s in re.findall(rb"[\x20-\x7e]{5,}", dados)
                       if b"\\" in s or b"/" in s)
    citados = {c.replace("/", "\\") for c in citados}
    citados.discard("")
    # Som do marcador da selecao do Bard (AnimationMarkers), tocado como arquivo.
    citados.update(SONS_DA_SELECAO)
    tem = set()
    for p in glob.glob(os.path.join(CLIENTE, "Effects", "*.pak")) + \
            glob.glob(os.path.join(CLIENTE, "sounds", "effect", "**", "*.pak"), recursive=True) + \
            glob.glob(os.path.join(CLIENTE, "textures", "**", "*.pak"), recursive=True):
        # Os originais: os paks gravados aqui sao refeitos a partir deles.
        q = p + SUFIXO_BACKUP if os.path.exists(p + SUFIXO_BACKUP) else p
        tem.update(e.nome.lower().replace("/", "\\").rsplit("\\", 1)[-1] for e in aion_pak.abre(q)[1])
    faltam = sorted(c for c in citados if "\\" in c and c.lower().rsplit("\\", 1)[-1] not in tem)
    # Sons: vao para o pak do 5.0 de mesmo caminho do pak do 5.8 que os tem (artist.pak,
    # effect.pak...), se o 5.0 ainda nao os tiver ali.
    por_pasta = {}
    for c in faltam:
        if c.lower().startswith("sounds\\"):
            pasta, arquivo = c.rsplit("\\", 1)
            por_pasta.setdefault(pasta.lower(), set()).add(arquivo.lower())
    trazidos = set()
    for pasta, arquivos in sorted(por_pasta.items()):
        for p58 in sorted(glob.glob(os.path.join(LIVE_CLIENTE, pasta, "*.pak"))):
            rel = os.path.relpath(p58, LIVE_CLIENTE)
            caminho = os.path.join(CLIENTE, rel)
            if not os.path.exists(caminho):
                continue
            origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
            _d, idx = aion_pak.abre(origem)
            ja = {e.nome.lower() for e in idx}
            d58, idx58 = aion_pak.abre(p58)
            novos = {e.nome: aion_pak.le(d58, e) for e in idx58
                     if e.nome.lower() in arquivos and e.nome.lower() not in ja}
            trazidos |= arquivos & ja
            if not novos:
                continue
            _backup(caminho)
            if origem != caminho:
                shutil.copy2(origem, caminho)
            regrava_pak(caminho, acrescenta=novos)
            _confere_pak(caminho, len(idx), {n: "novo" for n in novos})
            print(f"OK  {rel}: +{len(novos)} ({', '.join(sorted(novos))})")
            trazidos |= {n.lower() for n in novos}
    faltam = [c for c in faltam if not (c.lower().startswith("sounds\\")
                                        and c.rsplit("\\", 1)[-1].lower() in trazidos)]
    # Meshes e texturas de efeito: vao para o pak do 5.0 de mesmo caminho do pak do 5.8 que as tem
    # (Effects\ e Objects\, menos objects\items, cujos modelos tem passo proprio logo abaixo).
    def procura_58(nomes):
        achados = {}
        bases = {c.lower().rsplit("\\", 1)[-1] for c in nomes}
        for p in glob.glob(os.path.join(LIVE_CLIENTE, "Effects", "*.pak")) + \
                glob.glob(os.path.join(LIVE_CLIENTE, "Objects", "**", "*.pak"), recursive=True):
            rel58 = os.path.relpath(p, LIVE_CLIENTE)
            if rel58.lower().startswith("objects\\items\\"):
                continue
            try:
                d, idx = aion_pak.abre(p)
            except aion_pak.PakInvalido:
                continue
            for e in idx:
                if e.nome.lower().replace("/", "\\").rsplit("\\", 1)[-1] in bases:
                    achados.setdefault(rel58, {})[e.nome] = aion_pak.le(d, e)
        return achados

    # O que o 5.0 ja tem em objects\ (originais), pelo nome do arquivo: boids\bee.cgf esta no
    # boids_Meshes.pak do 5.0 e nao precisa vir.
    tem_objetos = set()
    for p in glob.glob(os.path.join(CLIENTE, "objects", "**", "*.pak"), recursive=True):
        q = p + SUFIXO_BACKUP if os.path.exists(p + SUFIXO_BACKUP) else p
        try:
            tem_objetos.update(e.nome.lower().replace("/", "\\").rsplit("\\", 1)[-1] for e in aion_pak.abre(q)[1])
        except aion_pak.PakInvalido:
            continue
    faltam = [c for c in faltam if not (c.lower().startswith("objects\\")
                                        and c.lower().rsplit("\\", 1)[-1] in tem_objetos)]
    # Os modelos de item que vem logo abaixo (aplica_modelos_de_efeito) tambem citam texturas fora de
    # objects\items: objects\items\Plants_FX02.cgf (Mvt. 1: Spring) pede effects\v4\cgf\Plants_FX02.dds,
    # que o 5.0 nao tem. Entram aqui, para irem no Effects_Textures.pak junto com as outras.
    cgfs_de_item = {c.lower().rsplit("\\", 1)[-1] for c in faltam
                    if c.lower().startswith("objects\\items\\") and c.lower().endswith(".cgf")}
    if cgfs_de_item:
        for p in glob.glob(os.path.join(LIVE_CLIENTE, "Objects", "items", "*.pak")):
            d_item, idx_item = aion_pak.abre(p)
            for e in idx_item:
                if e.nome.lower().replace("/", "\\").rsplit("\\", 1)[-1] in cgfs_de_item:
                    for s in re.findall(rb"[\x20-\x7e]{4,}\.dds", aion_pak.le(d_item, e), re.I):
                        c = s.decode("latin-1").replace("/", "\\")
                        if c.lower().startswith("effects\\") and c.lower().rsplit("\\", 1)[-1] not in tem \
                                and c not in faltam:
                            faltam.append(c)
                            print(f"    textura de efeito citada pelo modelo de item {e.nome}: {c}")
    por_pak = procura_58([c for c in faltam if not c.lower().startswith("objects\\items\\")])
    # Um modelo trazido (.cgf) cita as texturas dele pelo caminho: as que o 5.0 nao tem vem junto
    # (bee_hornet_fx/bee_hornet_01.cgf do Ba_SongofDelayDamage pede bee_hornet_01*.dds; sem elas
    # a abelha sai com a textura de erro).
    texturas_de_modelo = set()
    for arquivos in por_pak.values():
        for nome_58, dados in arquivos.items():
            if nome_58.lower().endswith(".cgf"):
                for s in re.findall(rb"[\x20-\x7e]{4,}\.dds", dados, re.I):
                    c = s.decode("latin-1").replace("/", "\\")
                    if not c.lower().startswith("textures\\defaults\\") \
                            and c.lower().rsplit("\\", 1)[-1] not in tem | tem_objetos:
                        texturas_de_modelo.add(c)
    if texturas_de_modelo:
        for rel58, arquivos in procura_58(sorted(texturas_de_modelo)).items():
            por_pak.setdefault(rel58, {}).update(arquivos)
        print(f"    texturas citadas pelos modelos trazidos: {sorted(texturas_de_modelo)}")
    # Animacoes dos modelos citados (os que o 5.0 ja tinha e os trazidos), menos os de objects\items,
    # que tem passo proprio: sem elas o modelo aparece parado.
    animacoes = animacoes_de_modelos(sorted(
        c for c in citados if c.lower().endswith(".cgf") and c.lower().startswith("objects\\")
        and not c.lower().startswith("objects\\items\\")))
    for rel58, arquivos in animacoes.items():
        por_pak.setdefault(rel58, {}).update(arquivos)
    if animacoes:
        print(f"    animacoes dos modelos citados: {sorted(n for a in animacoes.values() for n in a)}")
    # O 5.0 nem sempre tem o pak de mesmo caminho: objects\misc\boids\x.dds esta no 5.8 em
    # Objects\misc\Mesh_Textures_003.pak (entrada "boids/x.dds") e no 5.0 em
    # objects\misc\boids\boids_Textures.pak (entrada "x.dds"). Ai vai para o pak de texturas da
    # pasta do arquivo, com o nome relativo a ela.
    remapeado = {}
    for rel, arquivos in por_pak.items():
        if os.path.exists(os.path.join(CLIENTE, rel)):
            remapeado.setdefault(rel, {}).update(arquivos)
            continue
        for nome_58, dados in arquivos.items():
            pasta = os.path.join(os.path.dirname(rel), os.path.dirname(nome_58.replace("/", "\\")))
            # Textura no pak de texturas da pasta; modelo (.cgf) no de meshes (Roseleaf.cgf do 5.8
            # Objects\misc\Mesh_Meshes_002 -> objects\misc\misc_Meshes.pak do 5.0).
            tipo = "textures" if nome_58.lower().endswith(".dds") else \
                "meshes" if nome_58.lower().endswith((".cgf", ".cal")) else \
                "animations" if nome_58.lower().endswith(".caf") else None
            alvo = [p for p in glob.glob(os.path.join(CLIENTE, pasta, "*.pak"))
                    if tipo and os.path.basename(p).lower().endswith(f"_{tipo}.pak")]
            if len(alvo) != 1:
                print(f"    {nome_58} ({rel}): sem pak de destino no 5.0, fica de fora")
                continue
            remapeado.setdefault(os.path.relpath(alvo[0], CLIENTE), {})[nome_58.replace("\\", "/").rsplit("/", 1)[-1]] = dados
    por_pak = remapeado
    for rel, arquivos in sorted(por_pak.items()):
        caminho = os.path.join(CLIENTE, rel)
        if rel.lower() == PAK_EFEITOS.lower():
            # Arquivos que o 5.8 guarda no proprio Effects_Meshes.pak (v4/cgf/ba_helix2.pep): vao
            # no pak que acabou de ser gravado acima, acrescentados a ele (nao ao backup).
            origem = caminho
        else:
            origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
        _d, idx = aion_pak.abre(origem)
        _backup(caminho)
        if origem != caminho:
            shutil.copy2(origem, caminho)
        regrava_pak(caminho, acrescenta=arquivos)
        _confere_pak(caminho, len(idx), {n: "novo" for n in arquivos})
        print(f"OK  {rel}: +{len(arquivos)} ({', '.join(arquivos)})")
        trazidos = {n.lower().replace("/", "\\").rsplit("\\", 1)[-1] for n in arquivos}
        faltam = [c for c in faltam if c.lower().rsplit("\\", 1)[-1] not in trazidos]
    # Modelos de item citados por particulas (objects\items\string_FX.cgf, as cordas de luz da
    # harpa): o modelo inteiro -- .cgf, .cal, .saf, os .caf que o .cal lista e as texturas.
    modelos = [c for c in faltam if c.lower().startswith("objects\\items\\") and c.lower().endswith(".cgf")]
    if modelos:
        trazidos = aplica_modelos_de_efeito([c.rsplit("\\", 1)[-1] for c in modelos])
        faltam = [c for c in faltam if c.rsplit("\\", 1)[-1].lower() not in trazidos]
    print(f"    arquivos citados que continuam faltando no 5.0: {faltam or 'nenhum'}")
    sem_barra = sorted(c for c in citados if "\\" not in c)
    if sem_barra:
        print(f"    outros efeitos citados (nao conferidos): {sem_barra}")


#: Paks de `objects\items` que recebem modelos citados por efeitos. Nenhum outro passo os regrava
#: (a harpa vai no Mesh_Meshes_024 e no Mesh_Textures_047).
PAK_MODELO_DE_EFEITO = r"objects\items\Mesh_Meshes_021.pak"
PAK_ANIMACAO_DE_EFEITO = r"objects\items\Animation_Animations_007.pak"
PAK_TEXTURA_DE_EFEITO = r"objects\items\Mesh_Textures_043.pak"


def aplica_modelos_de_efeito(cgfs):
    """Traz do 5.8 os modelos de item `cgfs` (nomes de .cgf) com tudo o que eles usam.

    Devolve os nomes (minusculos) dos arquivos trazidos.
    """
    import glob
    arquivos58 = {}
    for p in glob.glob(os.path.join(LIVE_CLIENTE, "Objects", "items", "*.pak")):
        d, idx = aion_pak.abre(p)
        for e in idx:
            arquivos58.setdefault(e.nome.lower(), (d, e))
    tem50 = set()  # o que objects\items do 5.0 ja tem (originais)
    for p in glob.glob(os.path.join(CLIENTE, "objects", "items", "*.pak")):
        q = p + SUFIXO_BACKUP if os.path.exists(p + SUFIXO_BACKUP) else p
        tem50.update(e.nome.lower() for e in aion_pak.abre(q)[1])
    malhas, animacoes, texturas = {}, {}, {}
    for cgf in cgfs:
        base = cgf.rsplit(".", 1)[0].lower()
        for ext in (".cgf", ".cal", ".saf"):
            if base + ext in arquivos58:
                d, e = arquivos58[base + ext]
                malhas[e.nome] = aion_pak.le(d, e)
        cal = next((v for k, v in malhas.items() if k.lower() == base + ".cal"), None)
        if cal:
            for caf in re.findall(r"=\s*\S*?([^\\/\s]+\.caf)", cal.decode("latin-1"), re.I):
                d, e = arquivos58[caf.lower()]
                animacoes[e.nome] = aion_pak.le(d, e)
        for k, (d, e) in arquivos58.items():
            if k.endswith(".dds") and (k == base + ".dds" or k.startswith(base + "_")):
                texturas[e.nome] = aion_pak.le(d, e)
        # E as que o .cgf cita pelo caminho com outro nome (cello_FX.cgf -> objects\items\cello*.dds),
        # se o 5.0 ainda nao as tem em objects\items.
        cgf = next((v for k, v in malhas.items() if k.lower() == base + ".cgf"), b"")
        for s in re.findall(rb"[\x20-\x7e]{4,}\.dds", cgf, re.I):
            k = s.decode("latin-1").replace("/", "\\").lower()
            if k.startswith("objects\\items\\"):
                k = k.rsplit("\\", 1)[-1]
                if k in arquivos58 and k not in tem50:
                    d, e = arquivos58[k]
                    texturas[e.nome] = aion_pak.le(d, e)
    trazidos = set()
    for rel, novos in ((PAK_MODELO_DE_EFEITO, malhas), (PAK_ANIMACAO_DE_EFEITO, animacoes),
                       (PAK_TEXTURA_DE_EFEITO, texturas)):
        if not novos:
            continue
        caminho = os.path.join(CLIENTE, rel)
        origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
        _d, idx = aion_pak.abre(origem)
        if {e.nome.lower() for e in idx} & {n.lower() for n in novos}:
            raise ValueError(f"{rel} ja tem parte de {sorted(novos)}")
        _backup(caminho)
        if origem != caminho:
            shutil.copy2(origem, caminho)
        regrava_pak(caminho, acrescenta=novos)
        _confere_pak(caminho, len(idx), {n: "novo" for n in novos})
        print(f"OK  {rel}: +{len(novos)} ({', '.join(sorted(novos))})")
        trazidos |= {n.lower() for n in novos}
    return trazidos


def aplica_marcadores(racas=("lm",)):
    """Copia do cliente 5.8 os marcadores das animacoes de harpa, e os sons que eles tocam.

    O `AnimationMarkers\\<raca>.xml` diz, por animacao, em que instante cada coisa acontece:
    quando a arma passa do osso das costas para o da mao (`equip_weapon`), o ponto de acerto
    (`hitpoint`), sons, efeitos e rastros. Sem a entrada, a animacao toca mas a arma so troca de
    osso no fim. As quatro racas estao no mesmo pak, e o pak e sempre regravado a partir do
    original: por isso todas as racas pedidas vao numa gravacao so.
    """
    import xml.etree.ElementTree as ET
    import aion_bxml
    sys.setrecursionlimit(10000)

    d58, idx58 = aion_pak.abre(os.path.join(LIVE_CLIENTE, PAK_MARCADORES))
    caminho = os.path.join(CLIENTE, PAK_MARCADORES)
    origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
    d, idx = aion_pak.abre(origem)
    troca, todos_novos = {}, []
    for raca in racas:
        xml58 = aion_bxml.decodifica(aion_pak.le(d58, next(e for e in idx58 if e.nome.lower() == f"{raca}.xml")))
        raiz58 = ET.fromstring(xml58.split("?>", 1)[1])
        entrada = next(e for e in idx if e.nome.lower() == f"{raca}.xml")
        bxml = aion_pak.le(d, entrada)
        existentes = set(re.findall(r'<animation [^>]*name="([^"]*)"', aion_bxml.decodifica(bxml).lower()))
        # Harpa e as animacoes com o nome da classe Bard (selecao, criacao, idle).
        novos = [a for a in raiz58 if ("harp" in a.get("name", "").lower()
                                       or (_TOKEN_DE_CLASSE.search(a.get("name", ""))
                                           and not _ARMAS_DO_LOBBY.search(a.get("name", ""))))
                 and a.get("name").lower() not in existentes]
        novo, quantos = acrescenta_filhos(bxml, novos)
        conferido = aion_bxml.decodifica(novo)
        assert conferido.count("<animation ") == quantos + len(novos)
        assert 'name="cdraw_harp_001"' in conferido.lower()
        troca[entrada.nome] = novo
        todos_novos += novos
        print(f"    {raca}.xml: +{len(novos)} animacoes de harpa ({quantos + len(novos)} no total)")
    _backup(caminho)
    if origem != caminho:
        shutil.copy2(origem, caminho)
    regrava_pak(caminho, troca=troca)
    _confere_pak(caminho, len(idx), {n: "troca" for n in troca})
    print(f"OK  {PAK_MARCADORES}: {', '.join(r + '.xml' for r in racas)}")
    novos = todos_novos

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
    # Nome das classes do Bard (ids de classe 17 e 20, ver `harp_fix.h`). Ingles = o do Live:
    # STR_CLASS_NAME_ARTIST "Muse" (904317) e STR_CLASS_NAME_BARD "Songweaver" (904318).
    ("strings/client_strings_ui.xml", 1990003, "STR_CLASS_NAME_ARTIST",
     {"ENG": "Muse", "DEU": "Muse", "FRA": "Muse", "BRA": "Musa"}),
    ("strings/client_strings_ui.xml", 1990004, "STR_CLASS_NAME_BARD",
     {"ENG": "Songweaver", "DEU": "Barde", "FRA": "Barde", "BRA": "Bardo"}),
    # Descricao do painel da tela de criacao (`desc` do client_character_class_info). O Live 5.8 nao
    # tem essa tela nem esse texto: e nosso.
    ("strings/client_strings_ui.xml", 1990005, "STR_UI_Bard_DETAIL",
     {"ENG": "Songweavers fight with the harp: their enchanted melodies heal and empower allies "
             "and weaken enemies from mid range.",
      "DEU": "Barden kämpfen mit der Harfe: Ihre verzauberten Melodien heilen und stärken "
             "Verbündete und schwächen Feinde aus mittlerer Entfernung.",
      "FRA": "Les bardes combattent à la harpe : leurs mélodies enchantées soignent et renforcent "
             "les alliés et affaiblissent les ennemis à moyenne distance.",
      "BRA": "O Bardo luta com a harpa: suas melodias encantadas curam e fortalecem os aliados "
             "e enfraquecem os inimigos a média distância."}),
    # Estagio da skill Charge no nome da barra de cast ("Fiery Descant 1Stage"): o 5.8 usa
    # STR_CHARGE_STEP (904606, no 5.0 ja e outra string). O `charge_fix.h` pede o id 1990006.
    # Ingles = o do Live (video do 5.8); os outros sao traducao nossa.
    ("strings/client_strings_ui.xml", 1990006, "STR_CHARGE_STEP",
     {"ENG": "Stage", "DEU": "Stufe", "FRA": "Étape", "BRA": "Estágio"}),
    ("strings/client_strings_item.xml", 1990002, "STR_TEST_HARP_58",
     {"ENG": "Test Harp 5.8", "DEU": "Testharfe 5.8", "FRA": "Harpe de test 5.8",
      "BRA": "Harpa de Teste 5.8"}),
)
DESC_DO_ITEM = "STR_TEST_HARP_58"
ID_DO_NOME_DO_ITEM = 1990002
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


#: Icone pequeno das classes do Bard. O cliente pega o icone da classe pelo nome de um Skin
#: (`v4_class_<classe>`, tabela por id no `Game.dll`); nos ids 17 e 20 a tabela esta vazia e o
#: `harp_fix.h` poe os nomes abaixo. Os Skins apontam para os emblemas do Live 5.8 (64x64), que
#: sao tambem o `getIconImage` do servidor.
PAK_EMBLEMAS = r"textures\ui\EMBLEM\EMBLEM.pak"
EMBLEMAS_DA_CLASSE = ("Icon_emblem_Artist.dds", "Icon_emblem_Bard.dds")
SKINS_DA_CLASSE = (
    '<Skin name="v4_class_artist" src_image="0,0,64,64" texture="textures/ui/emblem/icon_emblem_artist" />',
    '<Skin name="v4_class_bard" src_image="0,0,64,64" texture="textures/ui/emblem/icon_emblem_bard" />',
)
#: Preset de icone por id de classe (state = id): nos vagos o Classic deixou variantes de outras
#: classes (17 = battleMaster2, 20 = lumines2); passam a ser os Skins do Bard.
PRESET_DE_ICONE = "v4_class_icon"
ESTADOS_DO_ICONE = {"17": "v4_class_artist", "20": "v4_class_bard"}
#: Onde esta o `version4.xml` (os Skins da interface): o geral e as copias de cada lingua. O do
#: BRA esta no `Data.pak`, ZIP comum com XML em UTF-16.
PAKS_DE_SKINS = (
    (r"data\ui\preload\preload.pak", "version4.xml"),
    (r"l10n\ENG\Data\Data.pak", "ui/preload/version4.xml"),
    (r"l10n\DEU\Data\Data.pak", "ui/preload/version4.xml"),
    (r"l10n\FRA\data\data.pak", "ui/preload/version4.xml"),
    (r"l10n\BRA\Data\Data.pak", "ui/preload/version4.xml"),
)


def _regrava_zip(caminho, origem, muda):
    """Regrava um pak ZIP comum trocando entradas: `muda = {nome em minusculas: f(bytes) -> bytes}`."""
    import zipfile
    tmp = caminho + ".tmp_harpa58"
    feitas = set()
    with zipfile.ZipFile(origem) as zi, zipfile.ZipFile(tmp, "w") as zo:
        for info in zi.infolist():
            dados = zi.read(info)
            f = muda.get(info.filename.lower())
            if f:
                dados = f(dados)
                feitas.add(info.filename.lower())
            zo.writestr(info, dados, compress_type=info.compress_type)
    if feitas != set(muda):
        os.remove(tmp)
        raise ValueError(f"{caminho}: nao achei {sorted(set(muda) - feitas)}")
    os.replace(tmp, caminho)
    with zipfile.ZipFile(caminho) as z:
        if z.testzip() is not None:
            raise ValueError(f"{caminho}: ZIP gravado com erro")


def aplica_icone_classe():
    import xml.etree.ElementTree as ET
    import aion_bxml
    caminho = os.path.join(CLIENTE, PAK_EMBLEMAS)
    origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
    _d, idx = aion_pak.abre(origem)
    novos = do_58(os.path.dirname(PAK_EMBLEMAS), EMBLEMAS_DA_CLASSE)
    if len(novos) != len(EMBLEMAS_DA_CLASSE):
        raise ValueError(f"faltou no 5.8: {sorted(set(EMBLEMAS_DA_CLASSE) - set(novos))}")
    _backup(caminho)
    if origem != caminho:
        shutil.copy2(origem, caminho)
    regrava_pak(caminho, acrescenta=novos)
    _confere_pak(caminho, len(idx), {n: "novo" for n in novos})
    print(f"OK  {PAK_EMBLEMAS}: +{len(novos)} ({', '.join(novos)})")

    aplica_interface()


#: Botao do Bard na tela de criacao (UI_Create.xml, contêiner Class_slots): os 13 botoes ficam em
#: 1600 px, ~118 px um do outro; com o 14o (class_14, a direita do Orchestrator) o passo cai para
#: ~109 px. A arte e composta a partir do losango vazio que a propria UI_Create_02 traz (cores sem
#: alfa; o alfa e a intersecao do dos 13 botoes) com o emblema do Bard (emblem_Job_bard).
PAK_TEXTURA_DO_BOTAO = r"Textures\UI\UI.pak"
TEXTURA_DO_BOTAO = "UI_Create_Bard.dds"
SKINS_DO_BOTAO = (
    '<Skin name="Lobby_bard_class_button_up" src_image="0,0,150,114" texture="textures/ui/ui_create_bard" />',
    '<Skin name="Lobby_bard_class_button_over" src_image="0,128,150,114" texture="textures/ui/ui_create_bard" />',
)
PRESET_DO_BOTAO = (
    '<Preset name="Lobby_bard_class_button" type="button">'
    '<SkinRef main_state="0" name="Lobby_bard_class_button_up" sub_state="up" />'
    '<SkinRef main_state="0" name="Lobby_bard_class_button_over" sub_state="over" />'
    '<SkinRef main_state="0" name="Lobby_bard_class_button_over" sub_state="down" />'
    '<SkinRef main_state="1" name="Lobby_bard_class_button_over" sub_state="up" />'
    '<SkinRef main_state="1" name="Lobby_bard_class_button_over" sub_state="over" />'
    '<SkinRef main_state="1" name="Lobby_bard_class_button_over" sub_state="down" />'
    '</Preset>'
)
PAKS_DO_LOBBY = (  # v3_lobby.xml: Skins e Preset do botao
    (r"data\ui\preload\preload.pak", "v3_lobby.xml"),
    (r"l10n\ENG\Data\Data.pak", "ui/preload/v3_lobby.xml"),
    (r"l10n\DEU\Data\Data.pak", "ui/preload/v3_lobby.xml"),
    (r"l10n\FRA\data\data.pak", "ui/preload/v3_lobby.xml"),
    (r"l10n\BRA\Data\Data.pak", "ui/preload/v3_lobby.xml"),
)
PAKS_DA_CRIACAO = (  # UI_Create.xml: o botao
    (r"data\ui\ui.pak", "UI_Create.xml"),
    (r"l10n\ENG\Data\Data.pak", "ui/UI_Create.xml"),
    (r"l10n\DEU\Data\Data.pak", "ui/UI_Create.xml"),
    (r"l10n\FRA\data\data.pak", "ui/UI_Create.xml"),
    (r"l10n\BRA\Data\Data.pak", "ui/UI_Create.xml"),
)
#: Barra de cast das skills Charge (charge_fix.h). O skill_delay_dialog do 5.8 tem um grupo `charge`
#: com a barra `v5_gauge_charge` (cor por estagio) e as bolinhas `v5_gauge_charge_step` (estado 0 =
#: apagada, 1-4 = cores); o do 5.0 so tem a barra comum, mas o preload do 5.0 ja tem os dois presets
#: e a textura (v5_common, igual a do 5.8). A barra ganha um nome proprio: `delay1` o 5.0 ja usa
#: para itens 165000000-165009999. As tres bolinhas centradas (todas as Charge do Bard tem 3
#: estagios); a altura 55 e a do 5.8.
PAKS_DA_BARRA_DE_CAST = (
    (r"data\ui\game\game.pak", "skill_delay_dialog.xml"),
    (r"l10n\ENG\Data\Data.pak", "ui/game/skill_delay_dialog.xml"),
    (r"l10n\DEU\Data\Data.pak", "ui/game/skill_delay_dialog.xml"),
    (r"l10n\FRA\data\data.pak", "ui/game/skill_delay_dialog.xml"),
    # o do BRA e zip com XML de texto, e e o que o cliente em portugues le
    (r"l10n\BRA\Data\Data.pak", "ui/game/skill_delay_dialog.xml"),
)
ALTURA_DA_BARRA_DE_CAST = "55"
#: Os presets da barra e das bolinhas existem no `version5.xml` do 5.0, mas o `ui_preload.xml` do
#: 5.0 nao carrega esse arquivo (lista ver5, ver4, version3, version4, hud_s1...): sem eles os
#: widgets nao tem imagem. Vao para o `version4.xml` (carregado; PAKS_DE_SKINS), iguais ao 5.8.
PRESETS_DA_CARGA = tuple(
    [f'<Skin name="v5_gauge_charge_step{s}" src_image="{x},925,18,14" texture="Textures/ui/v5_common" />'
     for s, x in (("", 279), ("1", 298), ("2", 317), ("3", 336), ("4", 355))]
    + ['<Preset name="v5_gauge_charge_step" type="static">'
       + "".join(f'<SkinRef name="v5_gauge_charge_step{s}" state="{k}" />'
                 for k, s in enumerate(("", "1", "2", "3", "4"))) + "</Preset>"]
    + [f'<Skin name="v5_gauge_charge{k}" src_image="373,{968 + 14 * (k - 1)},230,12" texture="Textures/ui/v5_common" />'
       for k in range(1, 5)]
    + ['<Preset name="v5_gauge_charge" type="gauge">'
       + "".join(f'<SkinRef main_state="{k}" name="v5_gauge_charge{k}" sub_state="gauge" />' for k in range(1, 5))
       + "</Preset>"])
#: `state_depended` (Game.dll 0xAFCA50 grava +0x354) faz o UIGauge desenhar a imagem do estado (+0x30) e nao
#: a da fracao preenchida; e o que o 5.8 usa nos gauges com cor por estado (energia do familiar, HP do grupo).
#: `stage` (+0x328) e quantos retangulos o gauge calcula (0xAADBF0), um por estado: sem ele so o do estado 0
#: existe. Sem `gradient`, cada um ocupa a barra inteira. 5 = estados 0 a 4.
BOLINHAS_DA_CARGA = (("charge_step1", 108), ("charge_step2", 127), ("charge_step3", 146))


def barra_de_carga_bxml(bxml):
    def editor(raiz):
        if raiz.procura(name="charge_gauge"):
            raise ValueError("skill_delay_dialog ja tem a charge_gauge")
        x, y, w, _h = raiz.get("frame").split(",")
        raiz.set("frame", f"{x},{y},{w},{ALTURA_DA_BARRA_DE_CAST}")
        barra = raiz.procura(name="delay")
        raiz.filhos.append(raiz.novo("Widget", flag="not_visible", frame=barra.get("frame"), name="charge_gauge",
                                     preset="v5_gauge_charge", stage="5", state_depended="True", type="gauge",
                                     value_type="float"))
        for nome, x_bolinha in BOLINHAS_DA_CARGA:
            raiz.filhos.append(raiz.novo("Widget", flag="not_visible", frame=f"{x_bolinha},34,18,14", name=nome,
                                         preset="v5_gauge_charge_step", type="static"))
    return edita_bxml(bxml, editor)


def barra_de_carga_texto(xml):
    """O mesmo de `barra_de_carga_bxml` num XML de texto (o zip do BRA)."""
    if 'name="charge_gauge"' in xml:
        raise ValueError("skill_delay_dialog ja tem a charge_gauge")
    dialogo = re.search(r'<Dialog [^>]*>', xml).group(0)
    novo = re.sub(r'\bframe="(\d+,\d+,\d+),\d+"', rf'frame="\1,{ALTURA_DA_BARRA_DE_CAST}"', dialogo, count=1)
    xml = xml.replace(dialogo, novo, 1)
    barra = re.search(r'<Widget [^>]*\bname="delay"[^>]*>', xml).group(0)
    frame = re.search(r'\bframe="([^"]+)"', barra).group(1)
    widgets = [f'  <Widget flag="not_visible" frame="{frame}" name="charge_gauge" preset="v5_gauge_charge" '
               f'stage="5" state_depended="True" type="gauge" value_type="float">\r\n  </Widget>\r\n']
    widgets += [f'  <Widget flag="not_visible" frame="{x},34,18,14" name="{nome}" preset="v5_gauge_charge_step" '
                f'type="static">\r\n  </Widget>\r\n' for nome, x in BOLINHAS_DA_CARGA]
    fim = xml.rindex("</Dialog>")
    inicio_da_linha = xml.rindex("\n", 0, fim) + 1
    return xml[:inicio_da_linha] + "".join(widgets) + xml[inicio_da_linha:]


#: Ordem dos botoes da esquerda para a direita, e onde o do Bard entra.
ORDEM_DOS_BOTOES = ("Class13", "Class12", "Class01", "Class02", "Class03", "Class04", "Class05",
                    "Class06", "Class07", "Class08", "Class09", "Class10", "Class11", "Class14")
X_DOS_BOTOES = (19, 1439)  # primeiro e ultimo, como no original


def _x_do_botao(i):
    a, b = X_DOS_BOTOES
    return round(a + i * (b - a) / (len(ORDEM_DOS_BOTOES) - 1))


def botao_na_criacao_bxml(bxml):
    def editor(raiz):
        slots = raiz.procura(name="Class_slots")
        por_nome = {f.get("name"): f for f in slots.filhos}
        if "Class14" in por_nome:
            raise ValueError("UI_Create ja tem o Class14")
        modelo = por_nome["Class11"]
        botao_modelo = modelo.filhos[0]
        novo = modelo.novo("Widget", frame=modelo.get("frame"), name="Class14", type="container")
        botao = botao_modelo.novo("Widget")
        for k, v in botao_modelo._attrs:
            botao._attrs.append((k, v))
        botao.set("name", "class_14")
        botao.set("preset", "Lobby_bard_class_button")
        novo.filhos.append(botao)
        slots.filhos.append(novo)
        por_nome["Class14"] = novo
        for i, nome in enumerate(ORDEM_DOS_BOTOES):
            f = por_nome[nome]
            _x, y, w, h = f.get("frame").split(",")
            f.set("frame", f"{_x_do_botao(i)},{y},{w},{h}")
    return edita_bxml(bxml, editor)


def botao_na_criacao_texto(xml):
    a = re.search(r'<Widget [^>]*\bname="Class_slots"[^>]*>', xml)
    if not a:
        raise ValueError("UI_Create sem Class_slots")
    if 'name="Class14"' in xml:
        raise ValueError("UI_Create ja tem o Class14")
    # Bloco do Class11 (contêiner + botao), copiado como Class14.
    m = re.search(r'([ \t]*)<Widget [^>]*\bname="Class11"[^>]*>.*?</Widget>\s*</Widget>', xml[a.end():], re.S)
    bloco = m.group(0)
    novo = bloco.replace('name="Class11"', 'name="Class14"').replace('name="class_11"', 'name="class_14"')
    novo = re.sub(r'preset="Lobby_orchestrator_class_button"', 'preset="Lobby_bard_class_button"', novo)
    fim_slots = a.end() + m.end()
    xml = xml[:fim_slots] + "\r\n" + novo + xml[fim_slots:]
    for i, nome in enumerate(ORDEM_DOS_BOTOES):
        m = re.search(r'<Widget [^>]*\bname="%s"[^>]*>' % nome, xml)
        tag = re.sub(r'\bframe="\d+,', f'frame="{_x_do_botao(i)},', m.group(0), count=1)
        xml = xml[:m.start()] + tag + xml[m.end():]
    return xml


def aplica_textura_do_botao():
    import io
    from PIL import Image, ImageFilter, ImageChops
    caminho = os.path.join(CLIENTE, PAK_TEXTURA_DO_BOTAO)
    origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
    d, idx = aion_pak.abre(origem)
    atlas = Image.open(io.BytesIO(aion_pak.le(d, next(e for e in idx if e.nome.lower() == "ui_create_02.dds")))).convert("RGBA")
    d2, idx2 = aion_pak.abre(os.path.join(CLIENTE, r"textures\ui\Job_image\Job_image.pak"))
    simb = Image.open(io.BytesIO(aion_pak.le(d2, next(e for e in idx2 if e.nome.lower() == "emblem_job_bard.dds")))).convert("RGBA")

    def crop(x, y):
        return atlas.crop((x, y, x + 150, y + 114))
    ups = [(8, 4), (364, 4), (364, 120), (364, 234), (364, 466), (695, 11), (695, 126), (695, 240),
           (695, 355), (695, 469), (695, 584), (695, 699), (695, 814)]
    overs = [(173, 4), (529, 4), (529, 119), (529, 234), (529, 466), (860, 11), (860, 126), (860, 240),
             (860, 356), (860, 469), (860, 584), (860, 699), (860, 814)]

    def intersecao(lista):
        a = crop(*lista[0]).split()[3]
        for p in lista[1:]:
            a = ImageChops.darker(a, crop(*p).split()[3])
        return a
    vazio_up, vazio_over = crop(364, 350), crop(529, 350)
    vazio_up.putalpha(intersecao(ups))
    vazio_over.putalpha(intersecao(overs))
    m = simb.split()[3]
    m = m.crop(m.getbbox()).point(lambda v: 0 if v < 20 else min(255, int(v * 2.2)))
    m = m.resize((int(m.size[0] * 76 / m.size[1]), 76), Image.LANCZOS)
    pos = (75 - m.size[0] // 2, 57 - 38)

    def compoe(base, cor, brilho):
        img = base.copy()
        if brilho:
            g = Image.new("RGBA", img.size, (0, 0, 0, 0))
            g.paste(Image.new("RGBA", m.size, brilho), pos, m)
            for _ in range(2):
                img = Image.alpha_composite(img, g.filter(ImageFilter.GaussianBlur(4)))
        s = Image.new("RGBA", img.size, (0, 0, 0, 0))
        s.paste(Image.new("RGBA", m.size, cor), pos, m)
        return Image.alpha_composite(img, s)
    tex = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    tex.paste(compoe(vazio_up, (92, 104, 128, 255), None), (0, 0))
    tex.paste(compoe(vazio_over, (255, 255, 255, 255), (140, 200, 255, 255)), (0, 128))
    saida = io.BytesIO()
    tex.save(saida, format="DDS")
    dados = saida.getvalue()
    if TEXTURA_DO_BOTAO.lower() in {e.nome.lower() for e in idx}:
        raise ValueError(f"{PAK_TEXTURA_DO_BOTAO} ja tem {TEXTURA_DO_BOTAO}")
    _backup(caminho)
    if origem != caminho:
        shutil.copy2(origem, caminho)
    regrava_pak(caminho, acrescenta={TEXTURA_DO_BOTAO: dados})
    _confere_pak(caminho, len(idx), {TEXTURA_DO_BOTAO: "novo"})
    print(f"OK  {PAK_TEXTURA_DO_BOTAO}: +{TEXTURA_DO_BOTAO} (botao do Bard, 256x256)")


#: Painel da direita da tela de criacao (descricao, barras de atributo e as etiquetas):
#: `client_character_class_info.xml`, uma entrada por classe. O `Game.dll` converte o `class_name`
#: em id de classe (tabela nome -> id; "Lumines" -> 19) e o painel procura a entrada por esse id.
#: A entrada do Bard tem `class_name` "Bard", que o `harp_fix.h` faz valer 20. Atributos = os do
#: `PlayerClass.BARD` do servidor (as barras de todas as classes sao iguais aos do `PlayerClass`);
#: etiquetas: nossas (o 5.8 nao tem essa tela). Sem `skill_info_list`: nao ha videos do Bard.
PAKS_DO_PAINEL = (r"data\PC\PC.pak", r"data\PC\special\special.pak")
ARQUIVO_DO_PAINEL = "client_character_class_info.xml"
PAINEL_DO_BARD = (("id", "14"), ("class_name", "Bard"), ("desc", "STR_UI_Bard_DETAIL"),
                  ("str", "90"), ("vit", "90"), ("agi", "100"), ("dex", "100"), ("kno", "120"),
                  ("wil", "110"))
ETIQUETAS_DO_BARD = ("magical", "heal", "buff", "middledistance")


def painel_do_bard_bxml(bxml):
    def campo(no, nome):
        f = next((c for c in no.filhos if c.nome == nome), None)
        return f._tab.texto(f._texto) if f is not None and f._texto is not None else None

    def editor(raiz):
        if any(campo(f, "class_name") == "Bard" for f in raiz.filhos):
            raise ValueError(f"{ARQUIVO_DO_PAINEL} ja tem o Bard")
        tab = raiz._tab

        def no(nome, texto=None, filhos=()):
            return NoBxml(tab, tab.indice(nome), None if texto is None else tab.indice(texto),
                          None, list(filhos))
        modelo = raiz.filhos[-1]
        etiquetas = [no("data", filhos=[no("tag", t)]) for t in ETIQUETAS_DO_BARD]
        raiz.filhos.append(NoBxml(tab, modelo._nome, None, None,
                                  [no(k, v) for k, v in PAINEL_DO_BARD] +
                                  [no("tag_list", filhos=etiquetas), no("skill_info_list")]))
    return edita_bxml(bxml, editor)


def aplica_painel_da_classe():
    for rel in PAKS_DO_PAINEL:
        caminho = os.path.join(CLIENTE, rel)
        origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
        d, idx = aion_pak.abre(origem)
        entrada = next(e for e in idx if e.nome.lower() == ARQUIVO_DO_PAINEL)
        original = aion_pak.le(d, entrada)
        novo = painel_do_bard_bxml(original)
        _backup(caminho)
        if origem != caminho:
            shutil.copy2(origem, caminho)
        regrava_pak(caminho, troca={entrada.nome: novo})
        _confere_pak(caminho, len(idx), {entrada.nome: "troca"})
        d2, idx2 = aion_pak.abre(caminho)
        lido = aion_pak.le(d2, next(e for e in idx2 if e.nome.lower() == ARQUIVO_DO_PAINEL))
        # As 13 entradas originais intactas e a do Bard no fim.
        resumo = []

        def confere(raiz):
            for f in raiz.filhos:
                resumo.append({c.nome: (c._tab.texto(c._texto) if c._texto is not None else None)
                               for c in f.filhos})
        edita_bxml(lido, confere)
        antes = []
        edita_bxml(original, lambda r: antes.extend(
            {c.nome: (c._tab.texto(c._texto) if c._texto is not None else None) for c in f.filhos}
            for f in r.filhos))
        assert resumo[:-1] == antes, rel
        bard = resumo[-1]
        assert all(bard[k] == v for k, v in PAINEL_DO_BARD), (rel, bard)
        print(f"OK  {rel}: {ARQUIVO_DO_PAINEL} com o Bard ({len(antes)} + 1 entradas)")


#: Plataforma do Bard no mapa da tela de criacao (`levels\login`). No 5.0 cada classe tem, por raca,
#: um ponto `CLASS_Position_<L|D>nn` (os dois sexos no mesmo ponto: a animacao de criacao os separa),
#: duas cameras `Camera_<Light|Dark>_<Classe>_<M|F>`, dois efeitos de particula e uma luz, em
#: fileiras com um passo de ~8 m; a de baixo termina no Soul Reaper (L24 / D24). No 5.8 cada sexo
#: tem o seu ponto e as animacoes de criacao do Bard sao feitas para isso: o casal do Artist
#: (masculino / feminino: D11 / D12 e Camera_DarkArtistM/F; o Elyos repete o Asmodiano) vem
#: inteiro, com os angulos do 5.8, transladado para um passo depois do Soul Reaper (o meio dos dois
#: pontos no lugar; o passo e L24 - L22 / D24 - D22, medido no proprio mapa). Os efeitos sao os do
#: Soul Reaper, um passo adiante. As entidades novas copiam as do Soul Reaper (atributos, Properties,
#: entitycontexts) trocando nome, ids, posicao e angulos. O `harp_fix.h` le os pontos e cameras do
#: Bard pelos nomes novos. A luz (`DeferredLight`, guardada em outro arquivo) nao e copiada.
PAK_DO_MAPA_LOGIN = r"levels\login\Level.pak"
PAK_DO_MAPA_LOGIN_58 = r"Levels\login\Level.pak"
PLATAFORMA_DO_BARD = (  # (raca, modelo do Soul Reaper, nome novo, entidade do 5.8 ou None = passo)
    ("L", "CLASS_Position_L24", "CLASS_Position_L26", "CLASS_Position_D11"),
    ("L", "CLASS_Position_L24", "CLASS_Position_L27", "CLASS_Position_D12"),
    ("L", "ParticleEffect_login_magic138", "ParticleEffect_login_magic_bard_L", None),
    ("L", "ParticleEffect313784", "ParticleEffect_bard_L", None),
    ("L", "Camera_Light_RuneBlade_M", "Camera_Light_Bard_M", "Camera_DarkArtistM"),
    ("L", "Camera_Light_RuneBlade_F", "Camera_Light_Bard_F", "Camera_DarkArtistF"),
    ("D", "CLASS_Position_D24", "CLASS_Position_D26", "CLASS_Position_D11"),
    ("D", "CLASS_Position_D24", "CLASS_Position_D27", "CLASS_Position_D12"),
    ("D", "ParticleEffect_login_magic143", "ParticleEffect_login_magic_bard_D", None),
    ("D", "ParticleEffect313789", "ParticleEffect_bard_D", None),
    ("D", "Camera_Dark_RuneBlade_M", "Camera_Dark_Bard_M", "Camera_DarkArtistM"),
    ("D", "Camera_Dark_RuneBlade_F", "Camera_Dark_Bard_F", "Camera_DarkArtistF"),
)
PASSO_DA_FILEIRA = {"L": ("CLASS_Position_L22", "CLASS_Position_L24"),
                    "D": ("CLASS_Position_D22", "CLASS_Position_D24")}
#: Elyos: as animacoes de criacao LM/LF do 5.8 tem outra pose que as DM/DF (braco direito 76 e 81
#: graus diferente; a dos Asmodianos e a certa, conferida em jogo). O Elyos usa as DM/DF
#: (`CRIACAO_DOS_ELYOS`) e, com elas, o mesmo arranjo do casal Asmodiano, so transladado.
COPIA_DA_SOMBRA = {"CLASS_Position_L26": "CLASS_Position_D26", "CLASS_Position_L27": "CLASS_Position_D27",
                   "Camera_Light_Bard_M": "Camera_Dark_Bard_M", "Camera_Light_Bard_F": "Camera_Dark_Bard_F"}
CASAL_DO_58 = {"L": ("CLASS_Position_L11", "CLASS_Position_L12"),
               "D": ("CLASS_Position_D11", "CLASS_Position_D12")}


def _elemento_entity(xml, nome):
    """(inicio, fim) do `<Entity ... Name="nome">` inteiro, com os filhos."""
    m = re.search(r'<Entity [^>]*\bName="%s"[^>]*?(/?)>' % re.escape(nome), xml)
    if not m:
        raise ValueError(f"mapa sem a entidade {nome}")
    if m.group(1):
        return m.start(), m.end()
    profundidade, p = 1, m.end()
    marca = re.compile(r'<(/?)Entity\b[^>]*?(/?)>')
    while profundidade:
        t = marca.search(xml, p)
        if t.group(1):
            profundidade -= 1
        elif not t.group(2):
            profundidade += 1
        p = t.end()
    return m.start(), p


def _attr(tag, chave):
    return re.search(r'\b%s="([^"]*)"' % chave, tag).group(1)


def _troca_attr(tag, chave, valor):
    return re.sub(r'\b(%s)="[^"]*"' % chave, lambda m: f'{m.group(1)}="{valor}"', tag, count=1)


def _vetor(xml, nome, chave):
    return tuple(float(v) for v in _attr(xml[slice(*_elemento_entity(xml, nome))], chave).split(","))


def _numero(v):
    return f"{v:.5f}".rstrip("0").rstrip(".")


def _destinos(xml, xml58):
    """{nome novo: (posicao, angulos ou None)} de cada entidade da plataforma."""
    destinos, lugares = {}, {}
    for raca in ("D", "L"):
        a, b = PASSO_DA_FILEIRA[raca]
        pa, pb = _vetor(xml, a, "Pos"), _vetor(xml, b, "Pos")
        passo = (pb[0] - pa[0], pb[1] - pa[1], 0.0)
        lugar = (pb[0] + passo[0], pb[1] + passo[1], pb[2])
        lugares[raca] = lugar
        m, f = (_vetor(xml58, n, "Pos") for n in CASAL_DO_58[raca])
        meio = tuple((x + y) / 2 for x, y in zip(m, f))
        translacao = tuple(l - c for l, c in zip(lugar, meio))
        for r, modelo, novo, do58 in PLATAFORMA_DO_BARD:
            if r != raca:
                continue
            if raca == "L" and do58:
                # Elyos: o casal Asmodiano inteiro (pontos, rotacoes, cameras), so transladado.
                sombra = COPIA_DA_SOMBRA[novo]
                pos = tuple(p + l - d for p, l, d in zip(destinos[sombra][0], lugar, lugares["D"]))
                destinos[novo] = (pos, destinos[sombra][1])
            elif do58 and novo.startswith("Camera_"):
                # A tela do 5.8 enquadra mais de perto: a camera recua pela propria linha de visao
                # (mira o mesmo ponto) ate ficar, no plano, a distancia que a camera do Soul Reaper do
                # mesmo sexo tem do ponto dele no 5.0. Angulos do 5.8. A camera olha para
                # (sen yaw, -cos yaw) -- conferido nas do 5.0 (Camera_Light_RuneBlade_M -> L24).
                c58 = tuple(p + t for p, t in zip(_vetor(xml58, do58, "Pos"), translacao))
                angulos = _vetor(xml58, do58, "Angles")
                ref = _vetor(xml, modelo, "Pos")
                dist50 = math.hypot(ref[0] - pb[0], ref[1] - pb[1])
                dist58 = math.hypot(c58[0] - lugar[0], c58[1] - lugar[1])
                yaw = math.radians(angulos[2])
                fx, fy = math.sin(yaw), -math.cos(yaw)
                recuo = dist50 - dist58
                destinos[novo] = ((c58[0] - fx * recuo, c58[1] - fy * recuo, c58[2]), angulos)
            elif do58:
                pos = tuple(p + t for p, t in zip(_vetor(xml58, do58, "Pos"), translacao))
                destinos[novo] = (pos, _vetor(xml58, do58, "Angles"))
            else:
                destinos[novo] = (tuple(p + d for p, d in zip(_vetor(xml, modelo, "Pos"), passo)), None)
    return destinos


def _ids_novos(xml):
    """GUID (com sinal, como no XML) e EntityId para cada entidade nova, sem repetir os do mapa."""
    guids = {int(g) for g in re.findall(r'EntityGUID="(-?\d+)"', xml)}
    proximo = max(int(i) for i in re.findall(r'EntityId="(\d+)"', xml)) + 1
    ids = {}
    for _raca, _modelo, novo, _do58 in PLATAFORMA_DO_BARD:
        guid = zlib.crc32(novo.encode()) - (1 << 31)
        while guid in guids:
            guid += 1
        guids.add(guid)
        ids[novo] = (guid, proximo)
        proximo += 1
    return ids


def plataforma_xml(xml, xml58):
    if 'Name="CLASS_Position_L26"' in xml:
        raise ValueError("o mapa ja tem a plataforma do Bard")
    destinos, ids = _destinos(xml, xml58), _ids_novos(xml)
    for _raca, modelo, novo, _do58 in PLATAFORMA_DO_BARD:
        ini, fim = _elemento_entity(xml, modelo)
        bloco = xml[ini:fim]
        tag_fim = bloco.index(">") + 1
        tag = bloco[:tag_fim]
        pos, angulos = destinos[novo]
        guid, eid = ids[novo]
        tag = _troca_attr(tag, "Name", novo)
        tag = _troca_attr(tag, "EntityGUID", str(guid))
        tag = _troca_attr(tag, "EntityId", str(eid))
        tag = _troca_attr(tag, "Pos", ",".join(_numero(v) for v in pos))
        if angulos:
            tag = _troca_attr(tag, "Angles", ",".join(_numero(v) for v in angulos))
        recuo = xml[xml.rindex("\n", 0, ini) + 1:ini]
        xml = xml[:fim] + "\n" + recuo + tag + bloco[tag_fim:] + xml[fim:]
    return xml, destinos, ids


def _entidades_lst(b):
    """[(nome, inicio, fim, corpo 0x1110, corpo 0x1120, corpo 0x1130)] do entitycontexts.lst."""
    n = struct.unpack_from("<I", b, 16)[0]
    o = struct.unpack_from("<I", b, 12)[0]
    saida = []
    while o < len(b):
        _nv, tag, ini, fim = struct.unpack_from("<4I", b, o)
        if tag != 0x1100:
            raise ValueError(f"entitycontexts: bloco {tag:#x} em {o}")
        partes, p = {}, ini
        while p < fim:
            _n2, t2, i2, f2 = struct.unpack_from("<4I", b, p)
            partes[t2] = b[i2:f2]
            p = f2
        corpo = partes[0x1110]
        tam = struct.unpack_from("<H", corpo, 0)[0]
        q = 3 + tam
        tam = struct.unpack_from("<H", corpo, q)[0]
        nome = corpo[q + 2:q + 2 + tam].decode("latin-1")
        saida.append((nome, o, fim, corpo, partes[0x1120], partes[0x1130]))
        o = fim
    if len(saida) != n:
        raise ValueError(f"entitycontexts: {len(saida)} entidades, cabecalho diz {n}")
    return saida


def _corpo_1110(corpo, nome, guid, eid, pos_nova, angulos):
    tam = struct.unpack_from("<H", corpo, 0)[0]
    classe = corpo[:3 + tam]
    q = 3 + tam
    tam = struct.unpack_from("<H", corpo, q)[0]
    q += 3 + tam
    zero, _g, _e, zero2 = struct.unpack_from("<4I", corpo, q)
    q += 16
    pos = struct.unpack_from("<3f", corpo, q)
    q += 12
    resto = bytearray(corpo[q:])
    if angulos:
        if not resto[0]:
            raise ValueError("entitycontexts: modelo sem rotacao")
        struct.pack_into("<3f", resto, 1, *angulos)
    r = 1 + (12 if resto[0] else 0)
    r += 1 + (12 if resto[r] else 0)
    desloca = [n - p for n, p in zip(pos_nova, pos)]
    caixa = struct.unpack_from("<6f", resto, r)
    struct.pack_into("<6f", resto, r, *(c + desloca[i % 3] for i, c in enumerate(caixa)))
    if r + 24 != len(resto):
        raise ValueError("entitycontexts: campos alem da caixa")
    novo_nome = nome.encode("latin-1")
    return (bytes(classe) + struct.pack("<H", len(novo_nome)) + novo_nome + b"\0" +
            struct.pack("<4I", zero, guid & 0xffffffff, eid, zero2) +
            struct.pack("<3f", *pos_nova) + bytes(resto))


def plataforma_lst(b, destinos, ids):
    entidades = {e[0]: e for e in _entidades_lst(b)}
    saida = bytearray(b)
    novos = 0
    for _raca, modelo, novo, _do58 in PLATAFORMA_DO_BARD:
        if modelo not in entidades:  # cameras so existem no XML
            continue
        if novo in entidades:
            raise ValueError(f"entitycontexts ja tem {novo}")
        _n, _i, _f, c1110, c1120, c1130 = entidades[modelo]
        guid, eid = ids[novo]
        pos, angulos = destinos[novo]
        partes = ((0x1110, _corpo_1110(c1110, novo, guid, eid, pos, angulos)), (0x1120, c1120), (0x1130, c1130))
        o = len(saida)
        corpo = bytearray()
        p = o + 16
        for tag, dados in partes:
            corpo += struct.pack("<4I", 2, tag, p + 16, p + 16 + len(dados)) + dados
            p += 16 + len(dados)
        saida += struct.pack("<4I", 1, 0x1100, o + 16, o + 16 + len(corpo)) + corpo
        novos += 1
    struct.pack_into("<I", saida, 16, struct.unpack_from("<I", b, 16)[0] + novos)
    return bytes(saida), novos


def aplica_plataforma_criacao():
    caminho = os.path.join(CLIENTE, PAK_DO_MAPA_LOGIN)
    origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
    d, idx = aion_pak.abre(origem)
    por_nome = {e.nome.lower(): e for e in idx}
    xml = aion_pak.le(d, por_nome["mission_mission0.xml"]).decode("utf-8")
    d58, idx58 = aion_pak.abre(os.path.join(LIVE_CLIENTE, PAK_DO_MAPA_LOGIN_58))
    xml58 = aion_pak.le(d58, next(e for e in idx58 if e.nome.lower() == "mission_mission0.xml")).decode("utf-8")
    novo_xml, destinos, ids = plataforma_xml(xml, xml58)
    lst = aion_pak.le(d, por_nome["entitycontexts.lst"])
    if aion_pak.le(d, por_nome["entitycontexts2.lst"]) != lst:
        raise ValueError("entitycontexts.lst e entitycontexts2.lst diferem")
    novo_lst, novos = plataforma_lst(lst, destinos, ids)
    troca = {por_nome["mission_mission0.xml"].nome: novo_xml.encode("utf-8"),
             por_nome["entitycontexts.lst"].nome: novo_lst,
             por_nome["entitycontexts2.lst"].nome: novo_lst}
    _backup(caminho)
    if origem != caminho:
        shutil.copy2(origem, caminho)
    regrava_pak(caminho, troca=troca)
    _confere_pak(caminho, len(idx), {n: "troca" for n in troca})
    # Confere: as entidades antigas intactas, as novas no lugar.
    d2, idx2 = aion_pak.abre(caminho)
    por_nome2 = {e.nome.lower(): e for e in idx2}
    lido = aion_pak.le(d2, por_nome2["entitycontexts.lst"])
    antes, depois = _entidades_lst(lst), _entidades_lst(lido)
    assert [e[3:] for e in depois[:len(antes)]] == [e[3:] for e in antes]
    assert len(depois) == len(antes) + novos
    lido_xml = aion_pak.le(d2, por_nome2["mission_mission0.xml"]).decode("utf-8")
    for _raca, _modelo, novo, do58 in PLATAFORMA_DO_BARD:
        tag = lido_xml[slice(*_elemento_entity(lido_xml, novo))]
        angulos = re.search(r'\bAngles="([^"]*)"', tag[:tag.index(">")])
        print(f"OK  {novo}: Pos {_attr(tag, 'Pos')}" + (f" Angles {angulos.group(1)}" if angulos else "") +
              (f" (de {do58})" if do58 else ""))
    print(f"OK  {PAK_DO_MAPA_LOGIN}: +{len(PLATAFORMA_DO_BARD)} entidades no XML, +{novos} no entitycontexts")


def _strings_por_arquivo(lingua):
    import bard_skills_58  # textos das skills do Bard (lote atual), no mesmo pak das outras strings
    por_arquivo = {}
    for arquivo, id_string, nome, textos in STRINGS + tuple(bard_skills_58.STRINGS_DAS_SKILLS()) \
            + tuple(bard_skills_58.STRINGS_DOS_NPCS()) + STRINGS_DO_SET():
        por_arquivo.setdefault(arquivo, []).append((id_string, nome, textos[lingua]))
    return por_arquivo


def _alteracoes_de_interface():
    """`{pak: {arquivo: [(tipo, dados)]}}` com as strings e os Skins do Bard, pak por pak.

    O `Data.pak` de ENG/DEU/FRA recebe os dois: cada pak e regravado uma vez so, a partir do
    original, com tudo o que vai nele (dois passos separados apagariam um ao outro).
    """
    alteracoes = {}
    for lingua, rel in PAKS_DE_STRINGS.items():
        for arquivo, novas in _strings_por_arquivo(lingua).items():
            alteracoes.setdefault(rel, {}).setdefault(arquivo, []).append(("strings", novas))
    for rel, arquivo in PAKS_DE_SKINS:
        alteracoes.setdefault(rel, {}).setdefault(arquivo.lower(), []).append(("skins", SKINS_DA_CLASSE))
        alteracoes[rel][arquivo.lower()].append(("presets_carga", PRESETS_DA_CARGA))
    for rel, arquivo in PAKS_DO_LOBBY:
        alteracoes.setdefault(rel, {}).setdefault(arquivo.lower(), []).append(("lobby", None))
    for rel, arquivo in PAKS_DA_CRIACAO:
        alteracoes.setdefault(rel, {}).setdefault(arquivo.lower(), []).append(("criacao", None))
    for rel, arquivo in PAKS_DA_BARRA_DE_CAST:
        alteracoes.setdefault(rel, {}).setdefault(arquivo.lower(), []).append(("carga", None))
    return alteracoes


def _preset_de_icone(xml):
    """Inicio e fim do `<Preset ... name="v4_class_icon">` num XML de texto, qualquer ordem de atributos."""
    m = re.search(r'<Preset [^>]*\bname="%s"[^>]*>' % PRESET_DE_ICONE, xml)
    if not m:
        raise ValueError(f"sem o Preset {PRESET_DE_ICONE}")
    return m.start(), xml.index("</Preset>", m.end())


def _confere_interface(rel, arquivo, lido, pedidos):
    for tipo, itens in pedidos:
        if tipo == "strings":
            for id_string, nome, texto in itens:
                bloco = re.search(r"<string>\s*<id>%d</id>.*?</string>" % id_string, lido, re.S)
                assert bloco and f"<body>{texto}</body>" in bloco.group(0), (rel, id_string)
                assert lido.count(f"<id>{id_string}</id>") == 1
                print(f"OK  {rel}: {nome} = {id_string} '{texto}'")
        elif tipo == "lobby":
            assert lido.count('<Skin name="Lobby_bard_class_button_up"') == 1, rel
            assert lido.count('<Skin name="Lobby_bard_class_button_over"') == 1, rel
            assert re.search(r'<Preset [^>]*name="Lobby_bard_class_button"', lido), rel
            print(f"OK  {rel}: {arquivo} com o Preset do botao do Bard")
        elif tipo == "criacao":
            xs = []
            for nome in ORDEM_DOS_BOTOES:
                tag = re.search(r'<Widget [^>]*\bname="%s"[^>]*>' % nome, lido).group(0)
                xs.append(int(re.search(r'\bframe="(\d+),', tag).group(1)))
            assert xs == sorted(xs) and len(set(xs)) == len(xs), (rel, xs)
            botao = re.search(r'<Widget [^>]*\bname="class_14"[^>]*>', lido).group(0)
            assert 'preset="Lobby_bard_class_button"' in botao and 'action="sel_class 1"' in botao, rel
            print(f"OK  {rel}: {arquivo} com o class_14 (x = {xs[0]}..{xs[-1]})")
        elif tipo == "presets_carga":
            for s in itens:
                tag, n = re.match(r'<(\w+) name="([^"]+)"', s).groups()
                assert len(re.findall(r'<%s name="%s"' % (tag, n), lido)) == 1, (rel, tag, n)
            print(f"OK  {rel}: {arquivo} com os presets da barra de carga ({len(itens)})")
        elif tipo == "carga":
            for nome in ("charge_gauge",) + tuple(n for n, _x in BOLINHAS_DA_CARGA):
                assert lido.count(f'name="{nome}"') == 1, (rel, nome)
            print(f"OK  {rel}: {arquivo} com a charge_gauge e {len(BOLINHAS_DA_CARGA)} bolinhas")
        else:
            for s in itens:
                n = re.search(r'name="([^"]+)"', s).group(1)
                assert lido.count(f'<Skin name="{n}"') == 1, (rel, n)
            a, b = _preset_de_icone(lido)
            refs = {re.search(r'\bstate="(\d+)"', r).group(1): re.search(r'\bname="([^"]*)"', r).group(1)
                    for r in re.findall(r"<SkinRef ([^>]*)>", lido[a:b])}
            for estado, nome in ESTADOS_DO_ICONE.items():
                assert refs.get(estado) == nome, (rel, estado, refs.get(estado))
            print(f"OK  {rel}: {arquivo} com os Skins de classe e o {PRESET_DE_ICONE} 17/20")


def aplica_interface():
    """Strings (nomes do tipo de arma, das classes e do item) e Skins do icone de classe."""
    import zipfile
    import xml.etree.ElementTree as ET
    import aion_bxml
    for rel, arquivos in _alteracoes_de_interface().items():
        caminho = os.path.join(CLIENTE, rel)
        # Sempre a partir do original: reaplicar nao duplica.
        origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
        if rel.startswith("l10n\\BRA"):
            def muda(dados, pedidos=None):
                xml = dados.decode("utf-16")
                for tipo, itens in pedidos:
                    if tipo == "strings":
                        for id_string, _n, _t in itens:
                            if f"<id>{id_string}</id>" in xml:
                                raise ValueError(f"{rel}: o id {id_string} ja existe")
                        fim = xml.rindex("</strings>")
                        xml = xml[:fim] + "".join(_string_xml(*n) for n in itens) + xml[fim:]
                    elif tipo == "lobby":
                        fim = xml.rindex("</Preload>")
                        xml = xml[:fim] + "".join(f"  {s}\n" for s in SKINS_DO_BOTAO) + \
                            f"  {PRESET_DO_BOTAO}\n" + xml[fim:]
                    elif tipo == "criacao":
                        xml = botao_na_criacao_texto(xml)
                    elif tipo == "carga":
                        xml = barra_de_carga_texto(xml)
                    elif tipo == "presets_carga":
                        fim = xml.rindex("</Preload>")
                        xml = xml[:fim] + "".join(f"  {s}\n" for s in itens) + xml[fim:]
                    else:
                        fim = xml.rindex("</Preload>")
                        xml = xml[:fim] + "".join(f"  {s}\n" for s in itens) + xml[fim:]
                        a, b = _preset_de_icone(xml)
                        bloco = xml[a:b]
                        for estado, nome in ESTADOS_DO_ICONE.items():
                            # A ordem dos atributos muda de um XML para outro.
                            bloco, n = re.subn(
                                r'<SkinRef ([^>]*\bstate="%s"[^>]*)>' % estado,
                                lambda m, nome=nome: "<SkinRef " + re.sub(
                                    r'\bname="[^"]*"', f'name="{nome}"', m.group(1)) + ">", bloco)
                            if n != 1:
                                raise ValueError(f"{rel}: {PRESET_DE_ICONE} sem o estado {estado}")
                        xml = xml[:a] + bloco + xml[b:]
                return xml.encode("utf-16")
            _backup(caminho)
            _regrava_zip(caminho, origem, {a: (lambda d, p=p: muda(d, p)) for a, p in arquivos.items()})
            with zipfile.ZipFile(caminho) as z:
                por_nome = {n.lower(): n for n in z.namelist()}
                for arquivo, pedidos in arquivos.items():
                    _confere_interface(rel, arquivo, z.read(por_nome[arquivo]).decode("utf-16"), pedidos)
            continue
        d, idx = aion_pak.abre(origem)
        troca = {}
        for arquivo, pedidos in arquivos.items():
            entrada = next(e for e in idx if e.nome.lower() == arquivo)
            bxml = aion_pak.le(d, entrada)
            texto_xml = aion_bxml.decodifica(bxml)
            novos, presets, criacao, carga = [], False, False, False
            for tipo, itens in pedidos:
                if tipo == "lobby":
                    novos += [ET.fromstring(x) for x in SKINS_DO_BOTAO + (PRESET_DO_BOTAO,)]
                elif tipo == "criacao":
                    criacao = True
                elif tipo == "carga":
                    carga = True
                elif tipo == "presets_carga":
                    novos += [ET.fromstring(s) for s in itens]
                elif tipo == "strings":
                    for id_string, _n, _t in itens:
                        if f"<id>{id_string}</id>" in texto_xml:
                            raise ValueError(f"{rel}: o id {id_string} ja existe")
                    novos += [ET.fromstring(_string_xml(*n)) for n in itens]
                else:
                    novos += [ET.fromstring(s) for s in itens]
                    presets = True
            troca[entrada.nome], _ = acrescenta_filhos(bxml, novos)
            if presets:
                troca[entrada.nome] = troca_skinrefs(troca[entrada.nome], PRESET_DE_ICONE, ESTADOS_DO_ICONE)
            if criacao:
                troca[entrada.nome] = botao_na_criacao_bxml(troca[entrada.nome])
            if carga:
                troca[entrada.nome] = barra_de_carga_bxml(troca[entrada.nome])
        _backup(caminho)
        if origem != caminho:
            shutil.copy2(origem, caminho)
        regrava_pak(caminho, troca=troca)
        _confere_pak(caminho, len(idx), {n: "troca" for n in troca})
        d2, idx2 = aion_pak.abre(caminho)
        por_nome = {e.nome.lower(): e for e in idx2}
        for arquivo, pedidos in arquivos.items():
            _confere_interface(rel, arquivo, aion_bxml.decodifica(aion_pak.le(d2, por_nome[arquivo])), pedidos)


def aplica_strings():
    aplica_interface()


#: Voz da selecao (marcador `login2`): vlogin2_<classe>_<sexo><raca><voz>.ogg, com a classe que o
#: `harp_fix.h` responde ("bard", "artist"). O 5.0 tem essas vozes no pak geral e no de cada
#: lingua; as do Live 5.8 sao em ingles, e vao para todos.
PAKS_DE_VOZ = (
    r"Sounds\voice\login\login.pak",
    r"l10n\ENG\sounds\voice\login\login.pak",
    r"l10n\DEU\sounds\voice\login\login.pak",
    r"l10n\FRA\sounds\voice\login\login.pak",
)
PAK_DE_VOZ_58 = r"Sounds\voice\login\login.pak"


def aplica_vozes():
    d58, idx58 = aion_pak.abre(os.path.join(LIVE_CLIENTE, PAK_DE_VOZ_58))
    vozes = {e.nome: aion_pak.le(d58, e) for e in idx58
             if re.match(r"(?i)vlogin\d_(bard|artist)_", e.nome)}
    if len(vozes) != 32:
        raise ValueError(f"esperava 32 vozes do Bard/Artist no 5.8, vieram {len(vozes)}")
    for rel in PAKS_DE_VOZ:
        caminho = os.path.join(CLIENTE, rel)
        origem = caminho + SUFIXO_BACKUP if os.path.exists(caminho + SUFIXO_BACKUP) else caminho
        _d, idx = aion_pak.abre(origem)
        ja = {e.nome.lower() for e in idx}
        novos = {n: b for n, b in vozes.items() if n.lower() not in ja}
        _backup(caminho)
        if origem != caminho:
            shutil.copy2(origem, caminho)
        regrava_pak(caminho, acrescenta=novos)
        _confere_pak(caminho, len(idx), {n: "novo" for n in novos})
        print(f"OK  {rel}: +{len(novos)} vozes (vlogin2_bard_*, vlogin2_artist_*)")


def _paks_com_backup():
    raizes = [os.path.join(CLIENTE, "objects"), os.path.join(CLIENTE, "sounds"),
              os.path.join(CLIENTE, "Effects"),
              os.path.dirname(os.path.join(CLIENTE, PAK_MARCADORES))]
    raizes += [os.path.dirname(os.path.join(CLIENTE, rel)) for rel in PAKS_DE_ITENS]
    raizes += [os.path.dirname(os.path.join(CLIENTE, rel)) for rel in PAKS_DE_STRINGS.values()]
    raizes += [os.path.dirname(os.path.join(CLIENTE, rel)) for rel, _a in PAKS_DE_SKINS]
    raizes.append(os.path.dirname(os.path.join(CLIENTE, PAK_EMBLEMAS)))
    raizes += [os.path.dirname(os.path.join(CLIENTE, rel)) for rel in PAKS_DE_VOZ]
    raizes += [os.path.dirname(os.path.join(CLIENTE, rel)) for rel, _a in PAKS_DA_CRIACAO + PAKS_DO_LOBBY]
    raizes.append(os.path.dirname(os.path.join(CLIENTE, PAK_TEXTURA_DO_BOTAO)))
    raizes.append(os.path.join(CLIENTE, r"data\PC"))  # PAKS_DO_PAINEL (e o special\ dentro)
    raizes.append(os.path.dirname(os.path.join(CLIENTE, PAK_DO_MAPA_LOGIN)))
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
    _invalida_cache_de_tabelas()
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
    elif "--corrige-harpa-previa" in sys.argv:
        aplica_correcao_harpa_previa()
    elif "--ajusta-harpa-previa" in sys.argv:
        ajusta_altura_harpa_previa()
    elif "--animacao" in sys.argv:
        aplica_animacao()
    elif "--barra-inicial" in sys.argv:
        aplica_barra_inicial()
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
    elif "--icone-classe" in sys.argv:
        aplica_icone_classe()
    elif "--botao-criacao" in sys.argv:
        aplica_textura_do_botao()
        aplica_interface()
    elif "--plataforma-criacao" in sys.argv:
        aplica_plataforma_criacao()
    elif "--painel-criacao" in sys.argv:
        aplica_painel_da_classe()
        aplica_interface()
    elif "--vozes" in sys.argv:
        aplica_vozes()
    elif "--classe-animacoes" in sys.argv:
        aplica_animacoes_de_classe()
    elif "--racas" in sys.argv:
        aplica_racas()
    else:
        aplica()

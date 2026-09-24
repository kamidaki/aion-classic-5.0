"""Tira do cliente os dialogos de missao (`quest_qNNNNN.html`) e as tabelas de progresso do Quest.pak.

Os `quest.xml` extraidos so trazem o cabecalho da missao (nivel, pre-requisito, recompensa). Quem diz
qual NPC atende cada etapa, com que pagina e com que acao, e o HTML de dialogo da missao, que fica
em `data/dialogs/10000_19999/10000_19999.pak` e `data/dialogs/20000_29999/20000_29999.pak`. A var de
cada etapa que nao e dialogo (abate, uso de item em area, area sensorial) vem de
`quest_script_monster.csv` e `quest_monster.csv`, dentro de `data/Quest/Quest.pak`.

**O HTML vem cifrado.** Magic `0x81`, um byte de semente e o resto XOR com uma chave de 256 bytes que
muda por arquivo (nao e rotacao nem soma de uma tabela fixa). O texto e XML em UTF-16LE com BOM, entao:

- nos bytes altos (posicao par depois do magic) o texto e quase sempre zero: a moda da coluna e a chave;
- nos bytes baixos a chave sai por modelo de bigramas de unidades UTF-16 treinado nos maiores
  arquivos do mesmo pak (tem hangul, entao contar so ASCII erra em arquivo pequeno).

Conferido em 2026-09-23: as 52 campanhas ativas saem sem nenhum U+FFFD; as 5 que nao fecham como XML
tem erro no proprio HTML oficial (`<font>` sem fechar, `</body>` faltando).

Uso:

    python "Ferramentas e Documentos/Ferramentas Python e PowerShell/Ferramentas Python/aion_dialogo_quest.py" <pasta data do cliente>              campanhas ativas
    python "Ferramentas e Documentos/Ferramentas Python e PowerShell/Ferramentas Python/aion_dialogo_quest.py" <pasta data do cliente> --missoes    todas as category1=mission
    python "Ferramentas e Documentos/Ferramentas Python e PowerShell/Ferramentas Python/aion_dialogo_quest.py" <pasta data do cliente> --ids 10160,20160

Grava em `Ferramentas e Documentos/Client e Coletas/Client 5.0 - Dados Extraidos/data/dialogs/quest/`
(UTF-8) e `.../data/Quest/quest_monster.csv`, `quest_script_monster.csv`.
"""
import collections
import math
import os
import re
import sys
import xml.etree.ElementTree as ET

FERRAMENTAS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, FERRAMENTAS)
import aion_pak  # noqa: E402

RAIZ = os.path.dirname(FERRAMENTAS)
DADOS = os.path.join(RAIZ, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos", "data")
DESTINO_DIALOGOS = os.path.join(DADOS, "dialogs", "quest")
PAKS_DE_DIALOGO = ("10000_19999", "20000_29999")
CSVS_DO_QUEST_PAK = ("quest_monster.csv", "quest_script_monster.csv")

MAGIC = 0x81
_ASCII_DE_XML = set(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 <>/=\"'._-\r\n\t:,!?()%&;[]#")
_PESO = {c: 1 for c in _ASCII_DE_XML}
_PESO.update({c: 2 for c in b"etaoinsrhl <>/=\""})


def _chave_inicial(d):
    """Primeira aproximacao: byte alto = moda (texto zero); byte baixo = mais caracteres de XML."""
    k = [0] * 256
    for j in range(256):
        col = d[j::256]
        if not col:
            continue
        if j % 2 == 0:
            k[j] = collections.Counter(col).most_common(1)[0][0]
        else:
            k[j] = max(range(256), key=lambda x: sum(_PESO.get(b ^ x, 0) for b in col))
    return k


def _unidades(d, k):
    t = bytes(b ^ k[i % 256] for i, b in enumerate(d))[1:]
    return [t[i] | t[i + 1] << 8 for i in range(0, len(t) - 1, 2)]


class Modelo:
    """Bigramas de unidades UTF-16 dos dialogos ja decifrados."""

    def __init__(self, corpos):
        self.uni = collections.Counter()
        self.bi = collections.Counter()
        for d in corpos:
            u = _unidades(d, _chave_inicial(d))
            self.uni.update(u)
            self.bi.update(zip(u, u[1:]))
        self.n = sum(self.uni.values())

    def lp(self, a, b):
        ca = self.uni.get(a, 0)
        pu = (self.uni.get(b, 0) + 0.01) / (self.n + 0.01 * 65536)
        if not ca:
            return math.log(pu)
        return math.log((self.bi.get((a, b), 0) + 0.5 * pu * ca + 1e-9) / (ca + 1e-9))


def decifra(bruto, modelo, voltas=4):
    """Bytes do `quest_q*.html` cifrado -> texto do XML."""
    if not bruto or bruto[0] != MAGIC:
        raise ValueError(f"magic 0x{bruto[0]:02X}, esperava 0x{MAGIC:02X}")
    d = bruto[1:]
    k = _chave_inicial(d)
    n = len(d)
    for _ in range(voltas):
        mudou = False
        for j in list(range(1, 256, 2)) + list(range(0, 256, 2)):
            melhor = None
            for cand in range(256):
                s = 0.0
                for i in range(j, n, 256):
                    unidade = (i - 1) // 2
                    lo_i = 1 + 2 * unidade
                    hi_i = lo_i + 1
                    if i < 1 or hi_i >= n:
                        continue
                    lo = d[lo_i] ^ (cand if lo_i % 256 == j else k[lo_i % 256])
                    hi = d[hi_i] ^ (cand if hi_i % 256 == j else k[hi_i % 256])
                    u = lo | hi << 8
                    if unidade > 0:
                        s += modelo.lp((d[lo_i - 2] ^ k[(lo_i - 2) % 256]) | (d[hi_i - 2] ^ k[(hi_i - 2) % 256]) << 8, u)
                    if hi_i + 2 < n:
                        s += modelo.lp(u, (d[lo_i + 2] ^ k[(lo_i + 2) % 256]) | (d[hi_i + 2] ^ k[(hi_i + 2) % 256]) << 8)
                if melhor is None or s > melhor[0]:
                    melhor = (s, cand)
            if melhor[1] != k[j]:
                k[j] = melhor[1]
                mudou = True
        if not mudou:
            break
    texto = bytes(b ^ k[i % 256] for i, b in enumerate(d))[1:]
    return texto.decode("utf-16-le", errors="replace").lstrip("﻿")


def ids_de_missao(so_ativas):
    """IDs `category1=mission` do quest.xml europeu; com `so_ativas`, sem as de minlevel 99."""
    raiz = ET.parse(os.path.join(DADOS, "europe", "Quest", "quest.xml")).getroot()
    ids = set()
    for q in raiz.findall("quest"):
        if q.findtext("category1") != "mission":
            continue
        if so_ativas and q.findtext("minlevel_permitted") == "99":
            continue
        ids.add(int(q.findtext("id")))
    return ids


def extrai_csvs(pasta_cliente):
    d, entradas = aion_pak.abre(os.path.join(pasta_cliente, "Quest", "Quest.pak"))
    for e in entradas:
        if e.nome.lower() in CSVS_DO_QUEST_PAK:
            with open(os.path.join(DADOS, "Quest", e.nome.lower()), "wb") as f:
                f.write(aion_pak.le(d, e))
            print(f"  data/Quest/{e.nome.lower()}")


def extrai_dialogos(pasta_cliente, ids):
    os.makedirs(DESTINO_DIALOGOS, exist_ok=True)
    feitos, falhas = 0, []
    for nome_pak in PAKS_DE_DIALOGO:
        d, entradas = aion_pak.abre(os.path.join(pasta_cliente, "dialogs", nome_pak, nome_pak + ".pak"))
        por_nome = {e.nome: e for e in entradas}
        maiores = sorted(entradas, key=lambda e: e.tam_original, reverse=True)[:40]
        modelo = Modelo([aion_pak.le(d, e)[1:] for e in maiores])
        for nome, e in sorted(por_nome.items()):
            m = re.fullmatch(r"(?i)quest_q(\d+)\.html", nome)
            if not m or int(m.group(1)) not in ids:
                continue
            try:
                texto = decifra(aion_pak.le(d, e), modelo)
            except ValueError as erro:
                falhas.append(f"{nome}: {erro}")
                continue
            if "�" in texto:
                falhas.append(f"{nome}: sobrou caractere invalido")
            with open(os.path.join(DESTINO_DIALOGOS, nome.lower()), "w", encoding="utf-8", newline="\n") as f:
                f.write(texto)
            feitos += 1
            print(f"  {nome.lower()}", flush=True)
    return feitos, falhas


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    pasta = argv[0]
    if "--ids" in argv:
        ids = {int(x) for x in argv[argv.index("--ids") + 1].split(",")}
    else:
        ids = ids_de_missao(so_ativas="--missoes" not in argv)
    print("Quest.pak:")
    extrai_csvs(pasta)
    print(f"Dialogos ({len(ids)} missoes):")
    feitos, falhas = extrai_dialogos(pasta, ids)
    print(f"total: {feitos} dialogos, {len(falhas)} problemas")
    for f in falhas:
        print("  " + f)
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

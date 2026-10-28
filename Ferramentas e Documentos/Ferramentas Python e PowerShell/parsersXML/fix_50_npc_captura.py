#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_50_npc_captura.py

Corrige npc_templates (mobs, guardas e NPCs) pelo que o servidor oficial 5.0 manda no S_PUT_NPC, lendo TODAS as
capturas de `Ferramentas e Documentos/Client e Coletas/Wireshark - Oficial Classic 5.0` -- inclusive as que comecaram com o
jogo ja logado, sem S_KEY (a chave sai do `aion_pcap.chave_sem_skey`).

O que vem de cada S_PUT_NPC (constante por npcId: 1.400 npcIds em 49 capturas, 0 variando em level/maxHp)
------------------------------------------------------------------------------------------------------------------
  level, maxHp      so existem na captura; nenhum arquivo do cliente tem esses campos
  title_id          D@32
  attack_speed      H da cauda (= attack_delay do cliente em 350/350)
  height            F da cauda (= upper x scale/100 do cliente em 350/350)
  equipment         ids da mascara, na ordem do pacote; mascara 0 = sem <equipment> (bate com visible_equipments)
  bound_radius      o pacote so traz max(front, side); front e side saem do cliente x scale/200, e so mudam quando o
                    max do cliente bate com o do pacote
  ai                byte de tipo 8 (AGGRESSIVE) em guarda de abismo cuja ai nao herda de AggressiveNpcAI nem de
                    AbyssGuardSimpleAI: o emulador so testa aggro nessas duas (CreatureEventHandler.checkAggro), entao
                    com `general` o guarda nunca ataca. Vira `simple_abyssguard`, a dos irmaos de torre.

Fica de fora (so relatorio): NPC invocado por jogador (criador != 0), npcId cujo valor muda entre capturas, tribo
diferente do cliente, mob agressivo com ai sem aggro (script proprio, como useSkillAndDie) e npcId sem template.

Cada arvore e lida e gravada separadamente: o npc_templates.xml da fonte e o do Produto Final sao arquivos diferentes
(o da fonte nao tem os NPCs de housing 810002-810056), entao nunca se copia um por cima do outro.

Uso:
    python fix_50_npc_captura.py              (mostra e grava o relatorio, sem mexer nos XMLs)
    python fix_50_npc_captura.py --aplicar    (grava as duas arvores, com backup)
"""

import argparse
import collections
import os
import re
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))   # parsersXML fica em Ferramentas e Documentos/Ferramentas Python e PowerShell (24/09)
sys.path.insert(0, os.path.join(RAIZ, "Ferramentas e Documentos", "Ferramentas Python e PowerShell", "Ferramentas Python"))
sys.path.insert(0, AQUI)
import aion_pcap  # noqa: E402
import backup_manager  # noqa: E402

CAPTURAS = os.path.join(RAIZ, "Ferramentas e Documentos", "Client e Coletas", "Wireshark - Oficial Classic 5.0")
CLIENT_NPCS = os.path.join(RAIZ, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos", "data", "npcs",
                           "client_npcs.xml")
GAME_SERVER = os.path.join(RAIZ, "Código Fonte - Emulador", "game-server")
ARVORES = (("fonte", os.path.join(GAME_SERVER, "data", "static_data")),
           ("produto", os.path.join(RAIZ, "Emulador - Produto Final", "GameServer", "data", "static_data")))
REL_XML = os.path.join("npcs", "npc_templates.xml")
RELATORIO = os.path.join(AQUI, "relatorio_npc_captura_50.txt")
AGRESSIVO = 8
AI_COM_AGGRO = ("AggressiveNpcAI", "AbyssGuardSimpleAI")
AI_GUARDA_ABISMO = "simple_abyssguard"
TOLERANCIA = 0.011
CAMPOS = ("lvl", "maxhp", "titulo", "atk", "alt", "raio", "itens")


# ---------------------------------------------------------------- capturas
def le_put(p):
    """S_PUT_NPC (0x0E) oficial; None se o layout nao fecha nos 48 bytes da cauda."""
    if len(p) < 107:
        return None
    npc = struct.unpack_from("<I", p, 16)[0]
    criador = struct.unpack_from("<I", p, 43)[0]
    off = 47                                   # nome do dono: UTF-16 terminado em 00 00 (vazio fora de invocacao)
    while p[off:off + 2] != b"\0\0":
        off += 2
        if off + 2 > len(p):
            return None
    invocado = criador != 0 or off > 47
    off += 2
    maxhp, lvl = struct.unpack_from("<I", p, off + 1)[0], p[off + 5]
    n = bin(struct.unpack_from("<I", p, off + 6)[0]).count("1")
    cauda = off + 10 + 20 * n                  # cada item: [D id][16 bytes 0]
    if len(p) - cauda != 48:
        return None
    raio, alt, _vel, atk = struct.unpack_from("<fffH", p, cauda)
    return dict(npc=npc, invocado=invocado, tipo=p[24], titulo=struct.unpack_from("<I", p, 32)[0], lvl=lvl, maxhp=maxhp,
                itens=tuple(struct.unpack_from("<I", p, off + 10 + 20 * i)[0] for i in range(n)),
                raio=round(raio, 4), alt=round(alt, 4), atk=atk)


def colhe():
    """npcId -> {campo: Counter de valores, 'tipos': set, 'capturas': set}."""
    medidas = collections.defaultdict(lambda: dict({c: collections.Counter() for c in CAMPOS}, tipos=set(), capturas=set()))
    resumo = []
    for pasta, _, arquivos in sorted(os.walk(CAPTURAS)):
        for arq in sorted(a for a in arquivos if a.endswith(".pcapng")):
            sessoes = aion_pcap.abre_todas(os.path.join(pasta, arq), sem_skey=True)
            puts = 0
            for s in sessoes:
                for op, p, fecha in s["servidor"]:
                    if not fecha or op != 0x0E:
                        continue
                    d = le_put(p)
                    if d is None or d["invocado"]:
                        continue
                    m = medidas[d["npc"]]
                    for c in CAMPOS:
                        m[c][d[c]] += 1
                    m["tipos"].add(d["tipo"])
                    m["capturas"].add(arq)
                    puts += 1
            resumo.append((arq, len(sessoes), sum(1 for s in sessoes if s["seed"] is None), puts))
    return medidas, resumo


# ---------------------------------------------------------------- cliente e codigo
def le_cliente(ids):
    """npcId -> dict(name, npc_type, tribe, front, side, scale) so dos ids pedidos."""
    out, buf, dentro = {}, [], False
    for linha in open(CLIENT_NPCS, encoding="utf-8", errors="replace"):
        if "<npc_client>" in linha:
            buf, dentro = [], True
            continue
        if not dentro:
            continue
        if "</npc_client>" not in linha:
            buf.append(linha)
            continue
        dentro, b = False, "".join(buf)
        mi = re.search(r"<id>(\d+)</id>", b)
        if not mi or int(mi.group(1)) not in ids:
            continue
        g = lambda c: (re.search(r"<%s>([^<]*)</%s>" % (c, c), b) or [None, ""])[1].strip()
        br = re.search(r"<bound_radius>\s*<front>([\d.]+)</front>\s*<side>([\d.]+)</side>", b)
        out[int(mi.group(1))] = dict(name=g("name"), npc_type=g("npc_type").lower(), tribe=g("tribe").upper(),
                                     front=float(br.group(1)) if br else None, side=float(br.group(2)) if br else None,
                                     scale=int(g("scale") or 100))
    return out


def ais_com_aggro():
    """Nomes de ai (@AIName) cuja classe herda de uma das que testam aggro."""
    nome_classe, pai = {}, {}
    for base in (os.path.join(GAME_SERVER, "data", "handlers"), os.path.join(GAME_SERVER, "src")):
        for pasta, _, arquivos in os.walk(base):
            for arq in arquivos:
                if not arq.endswith(".java"):
                    continue
                texto = open(os.path.join(pasta, arq), encoding="utf-8", errors="replace").read()
                for m in re.finditer(r'(?:@AIName\("([^"]+)"\)\s*)?(?:public\s+|abstract\s+|final\s+)*class\s+(\w+)'
                                     r'(?:<[^>{]*>)?\s+extends\s+(\w+)', texto):
                    if m.group(1):
                        nome_classe[m.group(1)] = m.group(2)
                    pai.setdefault(m.group(2), m.group(3))
    com = set()
    for nome, classe in nome_classe.items():
        vistas = set()
        while classe and classe not in vistas:
            if classe in AI_COM_AGGRO:
                com.add(nome)
                break
            vistas.add(classe)
            classe = pai.get(classe)
    return com, set(nome_classe)


# ---------------------------------------------------------------- edicao
def num(v):
    s = ("%.4f" % v).rstrip("0").rstrip(".")
    return s if s else "0"


def unico(contador):
    return next(iter(contador)) if len(contador) == 1 else None


def ajusta(bloco, medida, cli, com_aggro):
    """Bloco corrigido e a lista de (campo, antes, depois)."""
    mudancas = []
    cab = re.match(r"\t?<npc_template\b[^>]*>", bloco).group(0)
    attrs = dict(re.findall(r'(\w+)="([^"]*)"', cab))

    def atr(nome, valor, padrao=None):
        nonlocal bloco, cab
        antes = attrs.get(nome, padrao)
        if antes == valor or (antes is not None and valor is not None and _igual(antes, valor)):
            return
        if nome in attrs:
            novo = re.sub(r'(\b%s=")[^"]*(")' % nome, lambda m: m.group(1) + valor + m.group(2), cab, count=1)
        else:
            novo = cab[:-1].rstrip() + ' %s="%s">' % (nome, valor)
        bloco = bloco.replace(cab, novo, 1)
        cab = novo
        attrs[nome] = valor
        mudancas.append((nome, antes, valor))

    lvl, maxhp, titulo, atk, alt = (unico(medida[c]) for c in ("lvl", "maxhp", "titulo", "atk", "alt"))
    if lvl is not None:
        atr("level", str(lvl))
    if titulo is not None:
        atr("title_id", str(titulo), "0")
    if atk is not None:
        atr("attack_speed", str(atk), "2000")
    if alt is not None:
        atr("height", num(alt), "0")

    ai = attrs.get("ai")
    if AGRESSIVO in medida["tipos"] and cli.get("npc_type") == "abyss_guard" and ai not in com_aggro:
        atr("ai", AI_GUARDA_ABISMO)

    if maxhp is not None:
        m = re.search(r'<stats maxHp="(\d+)"', bloco)
        if m and int(m.group(1)) != maxhp:
            bloco = bloco[:m.start(1)] + str(maxhp) + bloco[m.end(1):]
            mudancas.append(("maxHp", m.group(1), str(maxhp)))

    itens = unico(medida["itens"])
    if itens is not None:
        eq = re.search(r"(\n\t*)?<equipment>.*?</equipment>", bloco, re.S)
        atuais = tuple(int(x) for x in re.findall(r"<item>(\d+)</item>", eq.group(0))) if eq else ()
        if sorted(atuais) != sorted(itens):
            if eq:
                bloco = bloco[:eq.start()] + bloco[eq.end():]
            stats = re.search(r"\n(\t*)<stats\b", bloco)
            if itens and stats:                    # template em varias linhas
                ind = stats.group(1)
                novo = "\n%s<equipment>%s\n%s</equipment>" % (ind, "".join("\n%s\t<item>%d</item>" % (ind, i) for i in itens), ind)
            elif itens:                            # template numa linha so
                novo = "<equipment>%s</equipment>" % "".join("<item>%d</item>" % i for i in itens)
            if itens:
                fim_stats = re.search(r"<stats\b[^>]*/>|</stats>", bloco)
                bloco = bloco[:fim_stats.end()] + novo + bloco[fim_stats.end():]
            mudancas.append(("equipment", " ".join(map(str, atuais)) or "-", " ".join(map(str, itens)) or "-"))

    raio = unico(medida["raio"])
    br = re.search(r'<bound_radius front="([^"]*)" side="([^"]*)"', bloco)
    if raio is not None and cli.get("front") is not None:
        f, s = cli["front"] * cli["scale"] / 200, cli["side"] * cli["scale"] / 200
        confere = abs(max(f, s) - raio) <= TOLERANCIA
        if br and confere and abs(max(float(br.group(1)), float(br.group(2))) - raio) > TOLERANCIA:
            novo = '<bound_radius front="%s" side="%s"' % (num(f), num(s))
            bloco = bloco.replace(br.group(0), novo, 1)
            mudancas.append(("bound_radius", "%s/%s" % br.groups(), "%s/%s" % (num(f), num(s))))
        elif not br and confere and alt is not None:
            # sem o elemento o servidor usa raio padrao; upper = altura, que a captura mediu (= upper x scale/100)
            elemento = '<bound_radius front="%s" side="%s" upper="%s" />' % (num(f), num(s), num(alt))
            depois = re.search(r"(\n\t*)?<(?:talk_info|massive_loot)\b|(\n\t*)?</npc_template>", bloco)
            stats = re.search(r"\n(\t*)<stats\b", bloco)
            prefixo = "\n" + stats.group(1) if stats else ""
            bloco = bloco[:depois.start()] + prefixo + elemento + bloco[depois.start():]
            mudancas.append(("bound_radius", "-", "%s/%s" % (num(f), num(s))))
    return bloco, mudancas


def _igual(a, b):
    try:
        return abs(float(a) - float(b)) < 1e-6
    except ValueError:
        return False


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true", help="grava as duas arvores (com backup)")
    ap.add_argument("--ids", help="so estes npcIds (separados por virgula), p.ex. os de um mapa conferido com verifica_template_captura.py")
    args = ap.parse_args()
    filtro = {int(v) for v in args.ids.split(",")} if args.ids else None

    print("[1/4] Lendo S_PUT_NPC de todas as capturas oficiais...")
    medidas, resumo = colhe()
    rel = ["fix_50_npc_captura.py -- %s" % ("APLICADO" if args.aplicar else "simulacao"), "", "CAPTURAS"]
    for arq, n, sem, puts in resumo:
        rel.append("  %-100s sessoes %d (sem S_KEY %d)  S_PUT_NPC %d" % (arq, n, sem, puts))
    variando = {n: [c for c in CAMPOS if len(m[c]) > 1] for n, m in medidas.items() if any(len(m[c]) > 1 for c in CAMPOS)}
    print("      %d npcIds, %d com algum campo variando entre capturas" % (len(medidas), len(variando)))

    print("[2/4] Lendo client_npcs.xml e as ai do codigo...")
    cli = le_cliente(set(medidas))
    com_aggro, todas_ai = ais_com_aggro()

    def categoria(n):
        t = cli.get(n, {}).get("npc_type", "")
        return "mob" if t == "monster" else "guarda" if t in ("guard", "abyss_guard") else "npc"

    rel += ["", "NPCIDS COM CAMPO VARIANDO ENTRE CAPTURAS (esses campos nao mudam)"]
    rel += ["  %d %s: %s" % (n, cli.get(n, {}).get("name"), {c: dict(medidas[n][c]) for c in cs}) for n, cs in sorted(variando.items())]

    print("[3/4] Corrigindo cada arvore separadamente...")
    for nome_arv, base in ARVORES:
        caminho = os.path.join(base, REL_XML)
        texto = open(caminho, encoding="utf-8", newline="").read()
        contagem, sem_template, detalhes = collections.Counter(), collections.defaultdict(list), []
        avisos = collections.defaultdict(list)
        pedacos, ultimo, vistos = [], 0, set()
        for m in re.finditer(r'\t?<npc_template npc_id="(\d+)"[ >].*?</npc_template>', texto, re.S):
            n = int(m.group(1))
            if n not in medidas or (filtro is not None and n not in filtro):
                continue
            vistos.add(n)
            bloco = m.group(0)
            ajustado, mudancas = ajusta(bloco, medidas[n], cli.get(n, {}), com_aggro)
            pedacos += [texto[ultimo:m.start()], ajustado]
            ultimo = m.end()
            cab = dict(re.findall(r'(\w+)="([^"]*)"', re.match(r"\t?<npc_template\b[^>]*>", ajustado).group(0)))
            if AGRESSIVO in medidas[n]["tipos"] and cab.get("ai") not in com_aggro:
                avisos["agressivo no oficial com ai sem aggro (nao mexido)"].append("%d %s ai=%s" % (n, cli.get(n, {}).get("name"), cab.get("ai")))
            if cab.get("ai") and cab["ai"] not in todas_ai:
                avisos["ai que nao existe no codigo (cai no fallback do AIEngine)"].append("%d %s ai=%s" % (n, cli.get(n, {}).get("name"), cab["ai"]))
            tribo_cli = cli.get(n, {}).get("tribe")
            if tribo_cli and cab.get("tribe", "").upper() != tribo_cli:
                avisos["tribo diferente do cliente (nao mexido)"].append("%d %s servidor=%s cliente=%s tipo=%s" % (
                    n, cli.get(n, {}).get("name"), cab.get("tribe"), tribo_cli, sorted(medidas[n]["tipos"])))
            if not mudancas:
                continue
            contagem[categoria(n)] += 1
            for campo, antes, depois in mudancas:
                contagem["campo " + campo] += 1
                detalhes.append("  %d %-45s [%s] %s: %s -> %s" % (n, cli.get(n, {}).get("name", "")[:45], categoria(n), campo, antes, depois))
        novo = "".join(pedacos) + texto[ultimo:]
        for n in sorted((set(medidas) if filtro is None else set(medidas) & filtro) - vistos):
            sem_template[categoria(n)].append(n)

        antes, depois = texto.count("<npc_template "), novo.count("<npc_template ")
        if antes != depois or not novo.rstrip().endswith("</npc_templates>"):
            sys.exit("ABORTADO: %s ficaria com %d templates (tinha %d)" % (caminho, depois, antes))
        if novo != texto:
            from lxml import etree
            etree.fromstring(novo.encode("utf-8"))            # bem formado, ou aborta antes de gravar

        print("   %s: %d templates corrigidos (mob %d, guarda %d, npc %d)" % (
            nome_arv, contagem["mob"] + contagem["guarda"] + contagem["npc"], contagem["mob"], contagem["guarda"], contagem["npc"]))
        print("      por campo: %s" % ", ".join("%s %d" % (k[6:], v) for k, v in sorted(contagem.items()) if k.startswith("campo ")))
        print("      sem template: mob %d, guarda %d, npc %d" % tuple(len(sem_template[c]) for c in ("mob", "guarda", "npc")))

        rel += ["", "=" * 100, "ARVORE %s: %s" % (nome_arv.upper(), caminho),
                "  corrigidos: mob %d, guarda %d, npc %d" % (contagem["mob"], contagem["guarda"], contagem["npc"]),
                "  por campo: %s" % ", ".join("%s %d" % (k[6:], v) for k, v in sorted(contagem.items()) if k.startswith("campo "))]
        for c in ("mob", "guarda", "npc"):
            rel.append("  sem template (%s, %d): %s" % (c, len(sem_template[c]), " ".join(
                "%d(%s)" % (n, cli.get(n, {}).get("name")) for n in sem_template[c])))
        for titulo, linhas in avisos.items():
            rel += ["", "  %s: %d" % (titulo, len(linhas))] + ["    " + x for x in linhas]
        rel += ["", "  MUDANCAS"] + detalhes

        if args.aplicar and novo != texto:
            backup_manager.backup_file_before_modification(caminho)
            open(caminho, "w", encoding="utf-8", newline="").write(novo)

    print("[4/4] Relatorio: %s" % RELATORIO)
    open(RELATORIO, "w", encoding="utf-8", newline="\n").write("\n".join(rel) + "\n")
    if not args.aplicar:
        print("Simulacao: nada gravado nos XMLs. Rode com --aplicar para gravar.")


if __name__ == "__main__":
    main()

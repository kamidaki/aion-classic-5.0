"""<stigma> das pedras de estigma do item_templates.xml, a partir do client_items 5.0.

Medido nas capturas oficiais 06_Sistemas_Novos_Stigma e 06_Sistemas_Novos_Stigma2 (2026-09-14): o blob 0x07 de cada pedra
traz gain_skill1/2, require_shard, os ids de require_skill1/2 e os níveis, e bate com o client_items nas 24 pedras
capturadas. Ao equipar, o servidor ensina exatamente as skills gain_skillN (S 0x2C com o id do client_skills), e não o
grupo inteiro da skill como na 4.8.

kind: META quando o nome tem _meta (sem pré-requisito, entra em qualquer slot), GREATER quando o cliente tem stigma_type
(só entra em slot de great stigma), NORMAL no resto. O texto "상급 스티그마 슬롯 전용" do cliente não serve para isso: está
nas meta e falta em 211 great stigma.

Os nomes de skill viram ids pelo client_skills.xml. Uma gain skill que o cliente ou o skill_templates.xml do servidor não
tem sai do <stigma> e vai para o relatório; um require que o cliente não tem também.

O script é idempotente e grava no fonte e no Produto Final, com backup.

Uso: python fix_50_stigma.py [--dry]
"""
import collections
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import backup_manager  # noqa: E402
from fix_50_energia_sp_ep import XMLS  # noqa: E402

REL_XML = os.path.join("items", "item_templates.xml")
REL_XSD = os.path.join("items", "item_templates.xsd")
REL_SKILLS = os.path.join("skills", "skill_templates.xml")
RELATORIO = os.path.join(AQUI, "relatorio_stigma_50.txt")
MAX_REQUIRE = 10  # posições de cada grupo de require no blob 0x07
BLOCO = re.compile(r'(\t<item_template id="(\d+)"(?:[^>"]|"[^"]*")*?)(/>|>(.*?)</item_template>)', re.S)
ANTES_DO_STIGMA = re.compile(r"</(?:modifiers|actions|godstone)>|<godstone\b[^>]*/>")  # xs:sequence do ItemTemplate


def ids_do_cliente():
    t = open(os.path.join(XMLS, "skills", "client_skills.xml"), encoding="utf-8", errors="replace").read()
    return {m.group(2).strip().lower(): int(m.group(1)) for m in re.finditer(r"<id>(\d+)</id>\s*<name>([^<]+)</name>", t)}


def pedras_do_cliente():
    out, bloco = {}, {}
    with open(os.path.join(XMLS, "items", "client_items.xml"), encoding="utf-8", errors="replace") as f:
        for linha in f:
            if "<client_item>" in linha:
                bloco = {}
                continue
            m = re.match(r"\s*<([a-z_0-9]+)>(.*?)</\1>", linha)
            if m:
                bloco[m.group(1)] = m.group(2).strip()
            elif "</client_item>" in linha and "require_shard" in bloco and bloco.get("id"):
                out[int(bloco["id"])] = bloco
    return out


def stigma_de(d, nome_id, no_servidor, faltas):
    iid = int(d["id"])
    kind = "META" if "_meta" in d.get("name", "").lower() else ("GREATER" if d.get("stigma_type") else "NORMAL")
    attrs = collections.OrderedDict(kind=kind, shard=d["require_shard"])
    for n in (1, 2):
        nome = d.get("gain_skill%d" % n)
        if not nome:
            continue
        sid = nome_id.get(nome.lower())
        if sid is None:
            faltas["gain sem skill no client_skills"].append("%d %s" % (iid, nome))
        elif sid not in no_servidor:
            faltas["gain sem skill_template no servidor"].append("%d %s=%d" % (iid, nome, sid))
        else:
            attrs["gain_skill%d" % n] = str(sid)
            attrs["gain_level%d" % n] = d.get("gain_level%d" % n, "1")
    for n in (1, 2):
        lista = [x.strip() for x in d.get("require_skill%d" % n, "").split(",") if x.strip()]
        ids = []
        for nome in lista:
            sid = nome_id.get(nome.lower())
            if sid is None:
                faltas["require sem skill no client_skills"].append("%d %s" % (iid, nome))
            else:
                ids.append(str(sid))
        if len(ids) > MAX_REQUIRE:
            faltas["require com mais de %d skills (cortado)" % MAX_REQUIRE].append("%d grupo %d: %d" % (iid, n, len(ids)))
            ids = ids[:MAX_REQUIRE]
        if ids:
            attrs["require_skill%d" % n] = " ".join(ids)
            attrs["require_skill%d_lv" % n] = d.get("require_skill%d_lv" % n, "1")
    return attrs


def linha_stigma(attrs):
    return "<stigma %s />" % " ".join('%s="%s"' % kv for kv in attrs.items())


def main():
    seco = "--dry" in sys.argv
    print("1. Lendo client_skills, client_items e skill_templates...")
    nome_id = ids_do_cliente()
    pedras = pedras_do_cliente()
    no_servidor = {int(x) for x in re.findall(r'<skill_template skill_id="(\d+)"',
                                              open(os.path.join(backup_manager.SERVER_DATA_DIR, REL_SKILLS), encoding="utf-8").read())}
    caminho = os.path.join(backup_manager.SERVER_DATA_DIR, REL_XML)
    with open(caminho, encoding="utf-8", newline="") as f:
        raw = f.read()
    eol = "\r\n" if "\r\n" in raw[:5000] else "\n"
    print("   pedras no cliente: %d | skills no cliente: %d | skill_templates: %d" % (len(pedras), len(nome_id), len(no_servidor)))

    print("2. Gerando o <stigma>...")
    faltas = collections.defaultdict(list)
    contagem = collections.Counter()
    tipos = collections.Counter()
    estigma_sem_cliente = []
    vistos = set()

    def edita(m):
        iid = int(m.group(2))
        cabeca = m.group(1)
        if 'item_group="STIGMA"' not in cabeca:
            return m.group(0)
        vistos.add(iid)
        d = pedras.get(iid)
        if d is None:
            estigma_sem_cliente.append(iid)
            return m.group(0)
        attrs = stigma_de(d, nome_id, no_servidor, faltas)
        tipos[attrs["kind"]] += 1
        linha = linha_stigma(attrs)
        if m.group(3) == "/>":
            contagem["criado (template sem corpo)"] += 1
            return cabeca.rstrip() + ">" + eol + "\t\t" + linha + eol + "\t</item_template>"
        corpo = m.group(4)
        velho = re.search(r"<stigma\b[^>]*/>", corpo)
        if velho:
            if velho.group(0) == linha:
                return m.group(0)
            contagem["substituido"] += 1
            corpo = corpo[:velho.start()] + linha + corpo[velho.end():]
        else:
            ultimo = None
            for ultimo in ANTES_DO_STIGMA.finditer(corpo):
                pass
            pos = ultimo.end() if ultimo else 0
            contagem["criado (template com corpo)"] += 1
            corpo = corpo[:pos] + eol + "\t\t" + linha + corpo[pos:]
        return cabeca + ">" + corpo + "</item_template>"

    novo = BLOCO.sub(edita, raw)
    sem_template = sorted(set(pedras) - vistos)
    print("   por tipo: %s" % dict(tipos))
    print("   %s" % dict(contagem))
    for k, v in sorted(faltas.items()):
        print("   %s: %d %s" % (k, len(v), v[:6]))
    print("   STIGMA no servidor sem pedra no cliente: %d %s" % (len(estigma_sem_cliente), estigma_sem_cliente[:10]))
    print("   pedras do cliente sem template STIGMA no servidor: %d %s" % (len(sem_template), sem_template[:10]))

    legado = re.findall(r"<stigma\b[^>]*gain_skill_group[^>]*/>", novo)
    if legado:
        sys.exit("sobrou <stigma> no formato 4.8 (%d): %s -- nada foi gravado." % (len(legado), legado[:3]))

    print("3. Validando contra o XSD...")
    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, REL_XSD)))
    if not schema.validate(etree.fromstring(novo.encode("utf-8"))):
        for e in list(schema.error_log)[:20]:
            print("   XSD linha {}: {}".format(e.line, e.message))
        sys.exit("XSD invalido: nada foi gravado.")
    print("   XSD valido.")

    with open(RELATORIO, "w", encoding="utf-8") as f:
        f.write("<stigma> gerado do client_items 5.0 (fix_50_stigma.py)\n\n")
        f.write("por tipo: %s\n%s\n\n" % (dict(tipos), dict(contagem)))
        for k, v in sorted(faltas.items()):
            f.write("%s (%d):\n" % (k, len(v)))
            for x in v:
                f.write("  %s\n" % x)
            f.write("\n")
        f.write("STIGMA no servidor sem pedra no cliente (%d): %s\n\n" % (len(estigma_sem_cliente), " ".join(map(str, estigma_sem_cliente))))
        f.write("pedras do cliente sem template STIGMA no servidor (%d): %s\n" % (len(sem_template), " ".join(map(str, sem_template))))
    print("   relatorio: " + RELATORIO)

    if novo == raw:
        print("nada a mudar")
        return
    if seco:
        print("--dry: nada gravado")
        return
    backup_manager.backup_file_before_modification(REL_XML)
    for base in (backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR):
        p = os.path.join(base, REL_XML)
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(novo)
        print("gravado", p)


if __name__ == "__main__":
    main()

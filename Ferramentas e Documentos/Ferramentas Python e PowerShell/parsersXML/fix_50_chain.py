"""Cadeias (<chain> e chain_skill_prob) do skill_templates.xml alinhadas com o client_skills 5.0, para toda skill que o client_skill_learns ensina.

Em 2026-09-14, das 785 skills jogáveis com cadeia:
  115 sem <chain> (a skill que abre a cadeia resetava a cadeia no cast e a seguinte era recusada)
   16 com <chain> que o cliente não tem (a skill exigia uma anterior que não existe na 5.0)
  157 com time diferente: 128 com o 1000 que o gerador punha quando o cliente não tem chain_time
   69 sem selfcount/precount, 15 com chain_skill_prob 10 onde o cliente tem 100, 6 com categoria errada (CH_Sonic)

Mapeamento (ChainCondition/ChainSkills): category = chain_category_name, precategory = prechain_category_name, time = chain_time,
selfcount = self_chain_count, precount = prechain_count, todos em maiúsculas nas categorias. O time é a janela depois da skill usada:
nas capturas oficiais, 57 usos em cadeia vieram dentro do chain_time da anterior (1 passou 381 ms, depois de um dash). Sem chain_time no
cliente, o time sai do template (0 = a cadeia não expira sozinha).

O script, idempotente (rodar de novo não muda nada):
  1. cria o <chain> que falta, 2. corrige o que diverge (comparando os atributos, não a ordem), 3. tira o <chain> que o cliente não tem,
  4. chain_skill_prob = chain_skill_prob2 do cliente quando ele tem o campo

Uso: python fix_50_chain.py [--dry]
"""
import collections
import os
import re
import sys

from fix_50_energia_sp_ep import TEMPLATES, XMLS, Template, le_cliente


def aprendidas(cli):
    nome_id = {d["name"].lower(): i for i, d in cli.items()}
    t = open(os.path.join(XMLS, "skills", "client_skill_learns.xml"), encoding="utf-8", errors="replace").read()
    return {nome_id[s.lower()] for s in re.findall(r"<skill>([^<]+)</skill>", t) if s.lower() in nome_id}


def chain_do_cliente(c):
    cat = c.get("chain_category_name", "")
    if not cat:
        return None
    a = collections.OrderedDict()
    if c.get("alterchain_use") == "1":  # ver fix_50_alterchain.py
        a["alter"] = "true"
    a["category"] = cat.upper()
    if c.get("prechain_category_name"):
        a["precategory"] = c["prechain_category_name"].upper()
    if c.get("chain_time") and c["chain_time"] != "0":
        a["time"] = c["chain_time"]
    if c.get("self_chain_count") and c["self_chain_count"] != "1":
        a["selfcount"] = c["self_chain_count"]
    if c.get("prechain_count") and c["prechain_count"] != "1":
        a["precount"] = c["prechain_count"]
    return a


def normaliza(attrs):
    """Atributos com os defaults do ChainCondition (time 0, selfcount 1, precount 1) removidos, para comparar."""
    d = {k: v for k, v in attrs.items()}
    for k, padrao in (("time", "0"), ("selfcount", "1"), ("precount", "1"), ("alter", "false")):
        if d.get(k) == padrao:
            del d[k]
    if "category" in d:
        d["category"] = d["category"].upper()
    if "precategory" in d:
        d["precategory"] = d["precategory"].upper()
    return d


def main():
    seco = "--dry" in sys.argv
    cli = le_cliente()
    alvo = aprendidas(cli)
    raw = open(TEMPLATES, encoding="utf-8", newline="").read()
    eol = "\r\n" if "\r\n" in raw[:5000] else "\n"
    contagem = collections.Counter()
    exemplos = collections.defaultdict(list)

    def conta(k, sid):
        contagem[k] += 1
        exemplos[k].append(sid)

    def edita(m):
        sid = int(m.group(2))
        if sid not in alvo:
            return m.group(0)
        c = cli[sid]
        tp = Template(m.group(1), m.group(3), eol)
        original = tp.texto()
        quer = chain_do_cliente(c)
        tem = re.search(r"<chain\b([^>]*)/>", tp.corpo)
        if quer is None:
            if tem:
                tp.tira_linhas(r"<chain ")
                conta("3 <chain> retirado", sid)
        else:
            linha = "<chain %s />" % " ".join('%s="%s"' % kv for kv in quer.items())
            if not tem:
                tp.poe_no_bloco("startconditions", linha)
                conta("1 <chain> criado", sid)
            elif normaliza(dict(re.findall(r'(\w+)="([^"]*)"', tem.group(1)))) != normaliza(quer):
                tp.corpo = tp.corpo.replace(tem.group(0), linha, 1)
                conta("2 <chain> corrigido", sid)
        prob = c.get("chain_skill_prob2")
        if prob and (tp.get_attr("chain_skill_prob") or "100") != prob:
            tp.attr("chain_skill_prob", prob)
            conta("4 chain_skill_prob", sid)
        return tp.texto() + m.group(4) if tp.texto() != original else m.group(0)

    novo = re.sub(r'(<skill_template skill_id="(\d+)"[^>]*>)(.*?)(</skill_template>)', edita, raw, flags=re.S)
    for k in sorted(contagem):
        print("%-24s %4d   %s%s" % (k, contagem[k], exemplos[k][:15], " ..." if len(exemplos[k]) > 15 else ""))
    if novo == raw:
        print("nada a mudar")
        return
    if seco:
        print("--dry: nada gravado")
        return
    with open(TEMPLATES, "w", encoding="utf-8", newline="") as f:
        f.write(novo)
    print("gravado", TEMPLATES)


if __name__ == "__main__":
    main()

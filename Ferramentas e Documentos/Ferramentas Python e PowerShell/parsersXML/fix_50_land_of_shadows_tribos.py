#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_50_land_of_shadows_tribos.py

Cria as tribos da Land of Shadows (IDTutorialQ, 390000000) pelo npc_tribe_relation.xml do cliente 5.0.

No oficial os mobs da instancia (IDTutorialQ_Monster) atacam o jogador e os guardas das duas racas, e os guardas
(IDTutorialQ_Guard_L / _D) atacam os mobs sem atacar o jogador -- a captura subida-1-60 mostra guarda e mob brigando.
O servidor nao tinha nenhuma dessas tribos, entao os templates caiam em GUARD/MONSTER genericos.

O que muda (o mesmo nome em maiusculas, como o resto do enum):
  TribeClass.java          valores novos no FIM do enum (nao muda o ordinal de nenhum existente)
  global_types.xsd         <xs:enumeration> do TribeClass, nas duas arvores
  tribe_relations.xml      um <tribe> por tribo: base_tribe -> base, aggressive -> aggro, friendly -> friend,
                           neutral/support/hostile/none iguais. Nome que nao existe nem no cliente nem no servidor
                           (IDTutorialQ_LGuard/_DGuard no IDTutorialQ_Pet) fica de fora e sai na tela.

O TribeClass.java so existe na fonte: precisa recompilar e implantar o JAR junto com os XMLs (os dados sozinhos nao
carregam, o JAXB nao conhece o valor novo).

Uso:
    python fix_50_land_of_shadows_tribos.py              (mostra, valida, nao grava)
    python fix_50_land_of_shadows_tribos.py --aplicar    (grava com backup)
A pasta do cliente (a que contem data/) pode vir da variavel de ambiente AION_CLIENT_XML_DIR.
"""

import argparse
import os
import re
import sys

from lxml import etree

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import backup_manager  # noqa: E402

ARVORES = (("fonte", backup_manager.SERVER_DATA_DIR), ("produto", backup_manager.PRODUTO_FINAL_DATA_DIR))
CLIENTE = os.path.join(os.environ.get("AION_CLIENT_XML_DIR") or os.path.join(
    backup_manager.PROJECT_ROOT, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos"),
    "data", "npcs", "npc_tribe_relation.xml")
JAVA = os.path.join(backup_manager.PROJECT_ROOT, "Código Fonte - Emulador", "game-server", "src", "com", "aionemu",
                    "gameserver", "model", "TribeClass.java")
PREFIXO = "idtutorialq_"
RELACOES = (("aggressive", "aggro"), ("hostile", "hostile"), ("friendly", "friend"), ("neutral", "neutral"),
            ("support", "support"), ("none", "none"))


def le_cliente():
    tribos = {}
    for t in etree.parse(CLIENTE).getroot().iter("tribe"):
        nome = t.get("Tribe") or ""
        if nome.lower().startswith(PREFIXO):
            tribos[nome.upper()] = {e.tag: [x.strip().upper() for x in (e.text or "").split(",") if x.strip()] for e in t}
    return tribos


def quebra(texto):
    return "\r\n" if "\r\n" in texto else "\n"


def java(texto, novos):
    faltam = [n for n in novos if not re.search(r"^\t%s[,;]?\r?$" % n, texto, re.M)]
    if not faltam:
        return texto
    m = re.search(r"(\t\w+);", texto)
    if not m:
        sys.exit("fim do enum TribeClass nao encontrado")
    nl = quebra(texto)
    return texto[:m.end(1)] + "," + nl + ("," + nl).join("\t" + n for n in faltam) + texto[m.end(1):]


def xsd(texto, novos):
    faltam = [n for n in novos if '<xs:enumeration value="%s" />' % n not in texto]
    if not faltam:
        return texto
    ini = texto.index('<xs:simpleType name="TribeClass">')
    fim = texto.index("</xs:restriction>", ini)
    nl = quebra(texto)
    linha = texto.rfind(nl, ini, fim) + len(nl)
    bloco = "".join('\t\t\t<xs:enumeration value="%s" />%s' % (n, nl) for n in faltam)
    return texto[:linha] + bloco + texto[linha:]


def relacoes(texto, tribos, conhecidas):
    nl = quebra(texto)
    bloco, ignorados = "", set()
    for nome, rel in sorted(tribos.items()):
        if re.search(r'<tribe name="%s"' % nome, texto):
            continue
        base = (rel.get("base_tribe") or [None])[0]
        attrs = ' name="%s"' % nome + (' base="%s"' % base if base else "")
        filhos = []
        for tag_cli, tag_srv in RELACOES:
            lista = []
            for alvo in rel.get(tag_cli, []):
                if alvo not in conhecidas:
                    ignorados.add(alvo)
                elif alvo not in lista:
                    lista.append(alvo)
            if lista:
                filhos.append("        <%s>%s</%s>" % (tag_srv, " ".join(lista), tag_srv))
        bloco += "    <tribe%s>%s%s%s    </tribe>%s" % (attrs, nl, nl.join(filhos), nl, nl) if filhos else \
            "    <tribe%s/>%s" % (attrs, nl)
    if not bloco:
        return texto, ignorados
    fim = texto.rindex("</tribe_relations>")
    return texto[:fim] + bloco + texto[fim:], ignorados


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    tribos = le_cliente()
    novos = sorted(tribos)
    print("cliente: %d tribos %s" % (len(novos), ", ".join(novos)))

    gravar = []
    with open(JAVA, encoding="utf-8", newline="") as f:
        t = f.read()
    nt = java(t, novos)
    print("TribeClass.java: %s" % ("+%d valores" % (nt.count("\n") - t.count("\n")) if nt != t else "nada a mudar"))
    if nt != t:
        gravar.append((JAVA, nt))
    conhecidas = set(re.findall(r"^\t(\w+)[,;]?\r?$", nt, re.M))

    ok = True
    for nome, base in ARVORES:
        print("[%s]" % nome)
        cam_xsd = os.path.join(base, "global_types.xsd")
        with open(cam_xsd, encoding="utf-8", newline="") as f:
            gx = f.read()
        ngx = xsd(gx, novos)
        etree.XMLSchema(etree.fromstring(ngx.encode("utf-8"), base_url=cam_xsd))  # o xsd em si continua valido
        print("  global_types.xsd: %s" % ("+%d enumeracoes" % len(novos) if ngx != gx else "nada a mudar"))
        cam_rel = os.path.join(base, "tribe", "tribe_relations.xml")
        with open(cam_rel, encoding="utf-8", newline="") as f:
            tr = f.read()
        ntr, ignorados = relacoes(tr, tribos, conhecidas)
        if ignorados:
            print("  ignorado (tribo inexistente): %s" % ", ".join(sorted(ignorados)))
        print("  tribe_relations.xml: %s" % ("+%d tribos" % (ntr.count("<tribe ") - tr.count("<tribe ")) if ntr != tr else "nada a mudar"))
        if ntr != tr:
            print("   " + ntr[tr.rindex("</tribe_relations>"):ntr.rindex("</tribe_relations>")].strip().replace("\n", "\n   "))
        if not valida_com_xsd_novo(base, ntr, ngx):
            ok = False
        if ngx != gx:
            gravar.append((cam_xsd, ngx))
        if ntr != tr:
            gravar.append((cam_rel, ntr))

    if not ok:
        sys.exit("Erro de validacao: nada foi gravado.")
    if not args.aplicar:
        print("Sem --aplicar: nada foi gravado.")
        return
    for caminho, novo in gravar:
        backup_manager.backup_file_before_modification(caminho)
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(novo)
        print("Gravado: " + caminho)


def valida_com_xsd_novo(base, tribe_xml, global_xsd):
    """Valida o tribe_relations.xml novo contra o global_types.xsd novo sem gravar nada: resolve o include pela memoria."""
    class Resolver(etree.Resolver):
        def resolve(self, url, pubid, context):
            if url.replace("\\", "/").endswith("global_types.xsd"):
                return self.resolve_string(global_xsd, context)
            return None
    parser = etree.XMLParser()
    parser.resolvers.add(Resolver())
    cam = os.path.join(base, "tribe", "tribe_relations.xsd")
    schema = etree.XMLSchema(etree.parse(cam, parser))
    doc = etree.fromstring(tribe_xml.encode("utf-8"), base_url=os.path.join(base, "tribe", "tribe_relations.xml"))
    if not schema.validate(doc):
        for e in list(schema.error_log)[:10]:
            print("   XSD linha {}: {}".format(e.line, e.message))
        return False
    print("  tribe_relations.xml valida contra o global_types.xsd novo")
    return True


if __name__ == "__main__":
    main()

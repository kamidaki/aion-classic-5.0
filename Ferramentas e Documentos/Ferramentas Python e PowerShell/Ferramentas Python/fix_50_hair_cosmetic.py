"""Liga os itens de penteado do Classic 5.0 aos cosmeticos do servidor.

No cliente 5.0 cada item de penteado (ex.: 169800480 cash_item_hair_type_da_w_211a) aponta para um
cosmetico pelo <cosmetic_name> do client_items, e o client_cosmetic_item_info da o <hair_type>, o
genero e a raca. Usar o item abre a confirmacao do Wardrobe (STR_EDIT_CHAR_ITEM_USE_CONFIRM_HAIR) e o
cliente manda o C 0xDE com o objeto do item; o servidor precisa saber que penteado o item e.

O emulador ja tem esse modelo nos itens antigos: <actions><cosmetic name="..."/></actions> no
item_template e a entrada type="hair_type" no cosmetic_items.xml. Faltavam os penteados novos: este
script acrescenta as entradas de cosmetic_items.xml que faltam e a acao (com <uselimits gender>) nos
templates que nao a tem, nas duas arvores (codigo-fonte e Produto Final), editando por id (as arvores
de item_templates divergem; nunca copiar o arquivo inteiro).

    python fix_50_hair_cosmetic.py [--aplica]
"""
import os
import re
import sys

RAIZ = r"G:\Projetos AION\Classic"
CLIENTE = os.path.join(RAIZ, r"Ferramentas e Documentos\Client e Coletas\Client 5.0 - Dados Extraidos\data")
ARVORES = (
    os.path.join(RAIZ, r"Código Fonte - Emulador\game-server\data\static_data"),
    os.path.join(RAIZ, r"Emulador - Produto Final\GameServer\data\static_data"),
)
RACA = {"pc_light": "ELYOS", "pc_dark": "ASMODIANS"}
GENERO = {"male": "MALE", "female": "FEMALE"}


def cosmeticos_de_cabelo():
    texto = open(os.path.join(CLIENTE, r"PC\client_cosmetic_item_info.xml"), encoding="utf-8", errors="replace").read()
    saida = {}
    for bloco in re.findall(r"<client_cosmeticiteminfo>(.*?)</client_cosmeticiteminfo>", texto, re.S):
        tipo = re.search(r"<hair_type>(\d+)</hair_type>", bloco)
        if not tipo:
            continue
        nome = re.search(r"<name>([^<]*)</name>", bloco).group(1).lower()
        raca = re.search(r"<race_permitted>([^<]*)</race_permitted>", bloco).group(1)
        genero = re.search(r"<gender_permitted>([^<]*)</gender_permitted>", bloco).group(1)
        saida[nome] = (int(tipo.group(1)), RACA[raca], GENERO[genero])
    return saida


def itens_de_penteado(cosmeticos):
    saida = {}
    for rel in (r"items\client_items.xml", r"europe\Items\client_items.xml"):
        texto = open(os.path.join(CLIENTE, rel), encoding="utf-8", errors="replace").read()
        for bloco in re.findall(r"<client_item>(.*?)</client_item>", texto, re.S):
            m = re.search(r"<cosmetic_name>([^<]*)</cosmetic_name>", bloco)
            if m and m.group(1).lower() in cosmeticos:
                saida[int(re.search(r"<id>(\d+)</id>", bloco).group(1))] = m.group(1).lower()
    return saida


def completa_cosmeticos(texto, cosmeticos, usados):
    tem = set(n.lower() for n in re.findall(r'cosmetic_name="([^"]+)"', texto))
    novos = []
    for nome in sorted(usados - tem):
        tipo, raca, genero = cosmeticos[nome]
        novos.append(f'\t<cosmetic_item type="hair_type" cosmetic_name="{nome}" id="{tipo}" race="{raca}" gender_permitted="{genero}"/>\n')
    if not novos:
        return texto, 0
    fim = texto.rindex("</cosmetic_items>")
    return texto[:fim] + "".join(novos) + texto[fim:], len(novos)


def completa_templates(texto, itens, cosmeticos):
    alterados = 0
    # Do fim para o comeco: inserir num template nao muda a posicao dos anteriores.
    for item_id, nome in sorted(itens.items(), key=lambda par: -texto.find('<item_template id="%d"' % par[0])):
        inicio = texto.find('<item_template id="%d"' % item_id)
        if inicio < 0:
            continue
        m = re.compile(r'<item_template [^>]*?(/?)>').match(texto, inicio)
        linha = texto.rfind("\n", 0, inicio) + 1
        recuo = texto[linha:inicio]
        if recuo.strip():
            raise ValueError(f"template {item_id} fora do comeco da linha")
        genero = cosmeticos[nome][2]
        acao = f'{recuo}\t<actions>\n{recuo}\t\t<cosmetic name="{nome}"/>\n{recuo}\t</actions>\n'
        if m.group(1) == "/":
            abertura = m.group(0)[:-2].rstrip() + ">"
            corpo = acao + f'{recuo}\t<uselimits gender="{genero}"/>\n{recuo}</item_template>'
            texto = texto[:m.start()] + abertura + "\n" + corpo + texto[m.end():]
            alterados += 1
            continue
        fim = texto.index("</item_template>", m.end())
        dentro = texto[m.end():fim]
        if "<cosmetic " in dentro:
            continue
        if "<actions>" in dentro:
            k = m.end() + dentro.index("<actions>") + len("<actions>")
            texto = texto[:k] + f'\n{recuo}\t\t<cosmetic name="{nome}"/>' + texto[k:]
        else:
            texto = texto[:m.end()] + "\n" + acao.rstrip("\n") + texto[m.end():]
        if "<uselimits" not in dentro:
            fim = texto.index("</item_template>", m.end())
            linha = texto.rindex("\n", 0, fim) + 1
            texto = texto[:linha] + f'{recuo}\t<uselimits gender="{genero}"/>\n' + texto[linha:]
        alterados += 1
    return texto, alterados


def main(argv):
    aplica = "--aplica" in argv
    cosmeticos = cosmeticos_de_cabelo()
    itens = itens_de_penteado(cosmeticos)
    print(f"{len(cosmeticos)} penteados no cliente, {len(itens)} itens apontam para eles")
    for arvore in ARVORES:
        caminho_cos = os.path.join(arvore, r"cosmetic_items\cosmetic_items.xml")
        caminho_itens = os.path.join(arvore, r"items\item_templates.xml")
        cos = open(caminho_cos, encoding="utf-8").read()
        tpl = open(caminho_itens, encoding="utf-8").read()
        cos2, n_cos = completa_cosmeticos(cos, cosmeticos, set(itens.values()))
        tpl2, n_tpl = completa_templates(tpl, itens, cosmeticos)
        print(f"{arvore}: +{n_cos} cosmeticos, {n_tpl} templates com a acao")
        if aplica:
            if n_cos:
                open(caminho_cos, "w", encoding="utf-8", newline="").write(cos2)
            if n_tpl:
                open(caminho_itens, "w", encoding="utf-8", newline="").write(tpl2)
    if not aplica:
        print("(ensaio; --aplica grava)")


if __name__ == "__main__":
    main(sys.argv[1:])

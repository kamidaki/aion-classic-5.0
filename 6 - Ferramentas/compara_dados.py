"""Compara os XMLs estaticos do servidor (formato Java EMU, dados 2.8) com os XMLs
extraidos do cliente 5.0.

O servidor guarda cada template numa tag com atributos (`<item_template id="..." level="...">`);
o cliente guarda o mesmo template numa tag com filhos (`<client_item><id>..</id><level>..</level>`).
Sao dois formatos para o mesmo dado, e o de la e a fonte -- o do servidor foi convertido dele.

O que a ferramenta responde, por dominio:

1. **Quantos ids cada lado tem** e qual a intersecao.
2. **O que o 5.0 tem e o servidor nao** -- e o que precisa ser acrescentado.
3. **O que o servidor tem e o 5.0 nao** -- template que saiu do jogo, ou conteudo proprio.
4. **Onde os dois discordam**, campo a campo, so nos campos que casam sem traducao.

O ponto 4 e conservador de proposito. Boa parte dos atributos do servidor e uma **traducao** do
valor do cliente (`1h_sword` virou `SWORD_1H`, `common` virou `COMMON`, o `STR_...` virou um id
numerico de string). Comparar esses exigiria reimplementar o conversor do Java, e um erro la
apareceria como divergencia de dado -- ruido que esconde a diferenca real. Entao so entram os
campos que sao o mesmo valor nos dois lados: numero igual a numero, nome igual a nome.

**Campos que ja foram testados e reprovados**, para ninguem tentar de novo:

- `npc_template/ai` x `ai_name` -- 30.881 de 31.702 "divergem". E o mapa do Java para os
  handlers dele: `SummonSkillArea` virou `skillarea`, `Summoned` virou `dummy`.
- `npc_template/tribe` x `tribe` -- 5.115 divergem, mesmo motivo: `Guard_Dark` virou
  `PROTECTGUARD_DARK`, `Monster` virou `AGGRESSIVESINGLEMONSTER`.
- `skill_template/name` x `name` -- 4.374 de 7.533. O do servidor as vezes e o nome de
  exibicao em ingles ("Shield of Hagen") e as vezes o nome interno ("Q_ShieldofHargen"). Nao
  serve de ancora. Os enums do lado dele (`skilltype`, `activation`) casam sem traducao.
- `quest/minlevel_permitted` e `maxlevel_permitted` -- no `Quest/quest.xml` do cliente sao
  99 e 0 em praticamente toda quest. Sao marcadores, nao o portao de nivel; o valor de
  verdade veio de outra fonte.

O `npc_template/name` fica, mas com 51 divergencias conhecidas: o Java corta o prefixo `OBJ_`
dos objetos de cenario.

Uso:

    python tools/compara_dados.py                      todos os dominios, resumo
    python tools/compara_dados.py itens                so um dominio
    python tools/compara_dados.py itens --faltando     lista os ids que faltam
    python tools/compara_dados.py itens --divergentes  lista as divergencias campo a campo
    python tools/compara_dados.py --limite 50          quantas linhas listar por secao
    python tools/compara_dados.py --csv <pasta>        grava o resultado completo em CSV

Com a extracao do cliente **2.8** em maos (o `--base`, ou a variavel `AION_CLIENTE_28`) a
ferramenta faz a pergunta que interessa: das divergencias, quais o patch 5.0 causou e quais o
proprio Java EMU inventou? Se o 2.8 e o 5.0 dizem a mesma coisa e so o servidor discorda, aquele
valor **nunca saiu do cliente** e sobrescreve-lo com o do 5.0 seria estragar dado bom.

    python tools/compara_dados.py --base <pasta-2.8>              classifica
    python tools/compara_dados.py --base <pasta-2.8> --aplicar    escreve so o que o patch mudou

O `--aplicar` so mexe nos campos que o patch mudou de verdade, e mexe num atributo de cada vez --
o resto do arquivo sai byte a byte igual.
"""
import csv
import io
import os
import re
import sys
from xml.etree import ElementTree as ET

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVIDOR = os.path.join(RAIZ, "Produto Final", "data", "server", "data")
CLIENTE = os.path.join(RAIZ, "Produto Final", "data", "client")


def _norm(v):
    """Deixa dois valores comparaveis: numero vira numero, nome vira minusculo sem espaco."""
    if v is None:
        return None
    v = v.strip()
    if not v:
        return None
    try:
        f = float(v)
        return int(f) if f == int(f) else round(f, 4)
    except ValueError:
        return v.lower()


def le_servidor(caminho, tag, campo_id, campos):
    """Le a tag do servidor, onde tudo mora em atributo."""
    saida = {}
    if not os.path.exists(caminho):
        return saida
    for _, el in ET.iterparse(caminho, events=("end",)):
        if el.tag != tag:
            continue
        bruto = el.get(campo_id)
        if bruto is not None:
            try:
                saida[int(bruto)] = {c: el.get(a) for c, a in campos.items()}
            except ValueError:
                pass
        el.clear()
    return saida


def le_cliente(caminho, tag, campos):
    """Le a tag do cliente, onde tudo mora em filho de primeiro nivel."""
    saida = {}
    if not os.path.exists(caminho):
        return saida
    for _, el in ET.iterparse(caminho, events=("end",)):
        if el.tag != tag:
            continue
        filhos = {f.tag: (f.text or "") for f in el}
        bruto = filhos.get("id")
        if bruto is not None:
            try:
                saida[int(bruto)] = {c: filhos.get(f) for c, f in campos.items()}
            except ValueError:
                pass
        el.clear()
    return saida


class Dominio:
    """Um par de arquivos que descrevem a mesma coisa nos dois formatos.

    `campos` mapeia um nome nosso para o par (atributo no servidor, filho no cliente). So entram
    os campos que valem o mesmo valor dos dois lados -- ver o cabecalho do modulo.
    """

    def __init__(self, nome, arq_srv, tag_srv, id_srv, arq_cli, tag_cli, campos):
        self.nome = nome
        self.arq_srv = os.path.join(SERVIDOR, arq_srv)
        self.tag_srv = tag_srv
        self.id_srv = id_srv
        self.rel_cli = arq_cli
        self.arq_cli = os.path.join(CLIENTE, arq_cli)
        self.tag_cli = tag_cli
        self.campos = campos

    def le_base(self, raiz):
        """O mesmo arquivo do cliente, mas da extracao antiga (2.8), se ela estiver ali."""
        caminho = os.path.join(raiz, self.rel_cli)
        if not os.path.exists(caminho):
            return None
        return le_cliente(caminho, self.tag_cli, {c: f for c, (_, f) in self.campos.items()})

    def compara(self):
        srv = le_servidor(
            self.arq_srv, self.tag_srv, self.id_srv,
            {c: a for c, (a, _) in self.campos.items()},
        )
        cli = le_cliente(
            self.arq_cli, self.tag_cli,
            {c: f for c, (_, f) in self.campos.items()},
        )
        so_cli = sorted(set(cli) - set(srv))
        so_srv = sorted(set(srv) - set(cli))
        comuns = sorted(set(srv) & set(cli))

        divergentes = []
        for i in comuns:
            for campo in self.campos:
                a, b = _norm(srv[i].get(campo)), _norm(cli[i].get(campo))
                # Campo ausente de um lado nao e mudanca de valor -- e um campo que aquele
                # formato nao carrega. Comparar isso enche o relatorio de "'' virou 0".
                if a is None or b is None:
                    continue
                if a != b:
                    divergentes.append((i, campo, srv[i].get(campo), cli[i].get(campo)))
        return srv, cli, so_cli, so_srv, comuns, divergentes


DOMINIOS = [
    Dominio(
        "itens",
        os.path.join("items", "item", "item_templates.xml"), "item_template", "id",
        os.path.join("items", "client_items.xml"), "client_item",
        {
            "nome": ("name", "name"),
            "nivel": ("level", "level"),
            "preco": ("price", "price"),
            "pilha": ("max_stack_count", "max_stack_count"),
        },
    ),
    Dominio(
        "npcs",
        os.path.join("npcs", "npc_templates.xml"), "npc_template", "npc_id",
        os.path.join("npcs", "client_npcs.xml"), "npc_client",
        {
            "nome": ("name", "name"),
            "alcance_sensorial": ("sensory_range", "sensory_range"),
            "atraso_de_ataque": ("attack_delay", "attack_delay"),
            "velocidade_do_projetil": ("ammo_speed", "ammo_speed"),
            "medidor_de_vida": ("hpgauge_level", "hpgauge_level"),
        },
    ),
    Dominio(
        "skills",
        os.path.join("skills", "template", "skill_templates.xml"), "skill_template", "skill_id",
        os.path.join("skills", "client_skills.xml"), "skill_base_client",
        {
            "tipo": ("skilltype", "type"),
            "subtipo": ("skillsubtype", "sub_type"),
            "ativacao": ("activation", "activation_attribute"),
            "slot_alvo": ("tslot", "target_slot"),
        },
    ),
    Dominio(
        "quests",
        os.path.join("quest_data", "quest_data.xml"), "quest", "id",
        os.path.join("Quest", "quest.xml"), "quest",
        {
            "nome": ("name", "name"),
            "repeticoes": ("max_repeat_count", "max_repeat_count"),
        },
    ),
]


def grava_csv(pasta, dom, so_cli, so_srv, divergentes, cli):
    os.makedirs(pasta, exist_ok=True)
    p1 = os.path.join(pasta, dom.nome + "_faltando.csv")
    with open(p1, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id"] + list(dom.campos))
        for i in so_cli:
            w.writerow([i] + [cli[i].get(c) or "" for c in dom.campos])
    p2 = os.path.join(pasta, dom.nome + "_so_no_servidor.csv")
    with open(p2, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id"])
        for i in so_srv:
            w.writerow([i])
    p3 = os.path.join(pasta, dom.nome + "_divergentes.csv")
    with open(p3, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "campo", "servidor_2_8", "cliente_5_0"])
        w.writerows(divergentes)
    return p1, p2, p3


def classifica(dom, base, srv, cli, so_cli, divergentes):
    """Separa o que o patch 5.0 mudou do que o Java EMU traduziu por conta propria.

    Sem a extracao do cliente 2.8 nao da para saber qual dos dois e: se o servidor discorda do
    5.0 num campo, ou o patch mudou o valor, ou aquele campo nunca saiu do cliente. Com o 2.8
    na mao a resposta e direta -- se o 2.8 e o 5.0 dizem a mesma coisa e so o servidor discorda,
    o valor do servidor veio de outra fonte e **nao deve ser sobrescrito**.
    """
    novos = [i for i in so_cli if i not in base]
    antigos_ausentes = [i for i in so_cli if i in base]

    do_patch, do_java = [], []
    for i, campo, v_srv, v_cli in divergentes:
        v_base = base.get(i, {}).get(campo)
        if _norm(v_base) == _norm(v_cli):
            do_java.append((i, campo, v_srv, v_cli))
        else:
            do_patch.append((i, campo, v_srv, v_cli, v_base))
    return novos, antigos_ausentes, do_patch, do_java


def aplica(dom, do_patch):
    """Escreve no XML do servidor so as mudancas que o patch 5.0 fez de verdade.

    Cirurgico de proposito: acha a tag de abertura daquele id e troca **um** atributo dentro
    dela. O resto do arquivo -- comentario, indentacao, ordem, filhos -- fica byte a byte igual,
    entao o `git diff` mostra exatamente o que mudou e nada mais.
    """
    if not do_patch:
        return 0
    texto = io.open(dom.arq_srv, encoding="utf-8").read()
    trocas = 0
    nao_achou = []
    for i, campo, v_srv, v_cli, _v_base in do_patch:
        attr = dom.campos[campo][0]
        # O arquivo do servidor escreve enum em caixa alta (`NONE`, `BUFF`) e o do cliente em
        # caixa mista (`None`, `Buff`). Sao o mesmo valor -- o que muda e a convencao do arquivo,
        # e o Java le esses campos como nome de enum, que e sensivel a caixa. Segue a do destino.
        if v_srv and not v_srv.replace(".", "").isdigit() and v_srv == v_srv.upper():
            v_cli = v_cli.upper()
        abre = re.compile(
            r'(<{tag}\b[^>]*?\s{idattr}="{id}"[^>]*?>)'.format(
                tag=re.escape(dom.tag_srv), idattr=re.escape(dom.id_srv), id=i
            )
        )
        m = abre.search(texto)
        if not m:
            nao_achou.append((i, campo))
            continue
        tag = m.group(1)
        novo = re.sub(
            r'\b{}="[^"]*"'.format(re.escape(attr)),
            '{}="{}"'.format(attr, v_cli),
            tag,
            count=1,
        )
        if novo == tag:
            nao_achou.append((i, campo))
            continue
        texto = texto[: m.start(1)] + novo + texto[m.end(1) :]
        trocas += 1
    if trocas:
        io.open(dom.arq_srv, "w", encoding="utf-8", newline="").write(texto)
    for i, campo in nao_achou:
        print("     [!] nao consegui trocar {} do id {}".format(campo, i))
    return trocas


def main(argv):
    limite = 20
    if "--limite" in argv:
        i = argv.index("--limite")
        limite = int(argv[i + 1])
        del argv[i:i + 2]
    csv_dir = None
    if "--csv" in argv:
        i = argv.index("--csv")
        csv_dir = argv[i + 1]
        del argv[i:i + 2]
    base_dir = os.environ.get("AION_CLIENTE_28")
    if "--base" in argv:
        i = argv.index("--base")
        base_dir = argv[i + 1]
        del argv[i:i + 2]
    lista_faltando = "--faltando" in argv
    lista_divergentes = "--divergentes" in argv
    aplicar = "--aplicar" in argv
    if aplicar and not base_dir:
        print("--aplicar precisa do --base: sem o cliente 2.8 nao da para separar o que o")
        print("patch mudou do que o Java EMU gerou, e nao se sobrescreve o que o Java gerou.")
        return 2
    pedidos = [a for a in argv if not a.startswith("-")]

    for dom in DOMINIOS:
        if pedidos and dom.nome not in pedidos:
            continue
        if not os.path.exists(dom.arq_srv):
            print("{}: NAO ACHEI {}".format(dom.nome, dom.arq_srv))
            continue
        if not os.path.exists(dom.arq_cli):
            print("{}: NAO ACHEI {}".format(dom.nome, dom.arq_cli))
            continue

        srv, cli, so_cli, so_srv, comuns, divergentes = dom.compara()
        por_campo = {}
        for _, campo, _, _ in divergentes:
            por_campo[campo] = por_campo.get(campo, 0) + 1

        print("\n=== {} ===".format(dom.nome.upper()))
        print("  servidor 2.8 : {:>7,}".format(len(srv)))
        print("  cliente  5.0 : {:>7,}".format(len(cli)))
        print("  em comum     : {:>7,}".format(len(comuns)))
        print("  so no 5.0    : {:>7,}   (acrescentar)".format(len(so_cli)))
        print("  so no 2.8    : {:>7,}   (sumiu do cliente ou e conteudo proprio)".format(len(so_srv)))
        if comuns:
            ids_div = len(set(i for i, _, _, _ in divergentes))
            print("  divergentes  : {:>7,} ids, {:,} campos".format(ids_div, len(divergentes)))
            for campo, n in sorted(por_campo.items(), key=lambda kv: -kv[1]):
                print("      {:<24} {:>7,}".format(campo, n))

        if base_dir:
            base = dom.le_base(base_dir)
            if base is None:
                print("  [2.8] nao achei {} em {}".format(dom.rel_cli, base_dir))
            else:
                novos, ja_existiam, do_patch, do_java = classifica(
                    dom, base, srv, cli, so_cli, divergentes
                )
                print("  -- contra o cliente 2.8 ({:,} ids) --".format(len(base)))
                print("     entraram no 5.0     : {:>7,}   (conteudo novo do patch)".format(len(novos)))
                print("     ja existiam no 2.8  : {:>7,}   (o servidor nunca converteu)".format(len(ja_existiam)))
                print("     campos que o patch mudou : {:>5,}".format(len(do_patch)))
                print("     campos que o Java gerou  : {:>5,}   (nao sobrescrever)".format(len(do_java)))
                pc = {}
                for _, campo, _, _, _ in do_patch:
                    pc[campo] = pc.get(campo, 0) + 1
                for campo, n in sorted(pc.items(), key=lambda kv: -kv[1]):
                    print("         {:<22} {:>7,}".format(campo, n))
                if aplicar:
                    n = aplica(dom, do_patch)
                    print("     APLICADO: {:,} campos escritos em {}".format(
                        n, os.path.relpath(dom.arq_srv, RAIZ)))
                if csv_dir:
                    os.makedirs(csv_dir, exist_ok=True)
                    pp = os.path.join(csv_dir, dom.nome + "_mudou_no_patch.csv")
                    with open(pp, "w", newline="", encoding="utf-8") as f:
                        w = csv.writer(f)
                        w.writerow(["id", "campo", "servidor_2_8", "cliente_5_0", "cliente_2_8"])
                        w.writerows(do_patch)
                    pn = os.path.join(csv_dir, dom.nome + "_novos_no_5_0.csv")
                    with open(pn, "w", newline="", encoding="utf-8") as f:
                        w = csv.writer(f)
                        w.writerow(["id"] + list(dom.campos))
                        for i in novos:
                            w.writerow([i] + [cli[i].get(c) or "" for c in dom.campos])
                    print("     gravado: {}".format(pp))
                    print("     gravado: {}".format(pn))
                if lista_divergentes and do_patch:
                    print("     -- as {} primeiras mudancas do patch --".format(min(limite, len(do_patch))))
                    for i, campo, v_srv, v_cli, v_base in do_patch[:limite]:
                        print("        {}  {}: 2.8={!r} -> 5.0={!r}   (servidor: {!r})".format(
                            i, campo, v_base, v_cli, v_srv))

        if lista_faltando and so_cli:
            print("  -- os {} primeiros que faltam --".format(min(limite, len(so_cli))))
            for i in so_cli[:limite]:
                campos = " ".join(
                    "{}={}".format(c, cli[i].get(c)) for c in dom.campos if cli[i].get(c)
                )
                print("      {}  {}".format(i, campos))
        if lista_divergentes and divergentes:
            print("  -- as {} primeiras divergencias --".format(min(limite, len(divergentes))))
            for i, campo, a, b in divergentes[:limite]:
                print("      {}  {}: 2.8={!r}  5.0={!r}".format(i, campo, a, b))

        if csv_dir:
            for p in grava_csv(csv_dir, dom, so_cli, so_srv, divergentes, cli):
                print("  gravado: {}".format(p))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

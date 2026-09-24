# -*- coding: utf-8 -*-
"""Completa os niveis 1..8 dos templates de atributos de jogador.

As oito classes classicas (assassin, chanter, cleric, gladiator, ranger, sorcerer, spiritmaster,
templar) so tem `<player_stats>` a partir do nivel 9. Personagem nivel 1 dessas classes nao acha
template, recebe **todos os atributos zerados** -- inclusive `run_speed` -- e o cliente 5.0, com
razao, nao o deixa andar. Foi assim que o defeito apareceu: so as cinco classes novas do 5.0, que
tem cobertura de 1 a 65, conseguiam se mover.

Nao existe fonte para esses valores: o cliente nao carrega tabela de atributos de servidor, o
projeto 4.8 de referencia tambem nao a tem, e o arquivo nunca teve nivel 1 em nenhum commit. Entao
eles sao **derivados da propria classe**, projetando para tras a curva que ela ja exibe do nivel 9
em diante -- nunca emprestando a curva de outra classe.

O metodo e verificavel, e o modo `validar` faz exatamente isso: nas cinco classes que **tem** os
niveis 1..8, esconde esses niveis, extrapola a partir do 9 e compara com o valor real.

    python "Ferramentas e Documentos/Ferramentas Python e PowerShell/parsersXML/completa_stats_niveis_baixos.py" validar
    python "Ferramentas e Documentos/Ferramentas Python e PowerShell/parsersXML/completa_stats_niveis_baixos.py" aplicar

Rode da raiz do projeto. Escreve nas duas arvores (fonte e produto).
"""
import os
import re
import sys

RAIZES = [os.path.join("Código Fonte - Emulador", "GameServer", "data", "static_data",
                       "stats", "player"),
          os.path.join("Emulador - Produto Final", "GameServer", "data", "static_data",
                       "stats", "player")]
CLASSICAS = ["assassin", "chanter", "cleric", "gladiator", "ranger", "sorcerer",
             "spiritmaster", "templar"]
COM_NIVEIS_BAIXOS = ["brawler", "luminess", "phoenix", "revenant", "soul-reaper"]
BLOCO = re.compile(r'<player_stats class="([A-Z_]+)" level="(\d+)">\s*<stats_template ([^/]*?)/>\s*</player_stats>')
ATRIBUTO = re.compile(r'(\w+)="([^"]*)"')
APOIO = 8   # quantos niveis conhecidos usar para achar a curva


def le(caminho):
    texto = open(caminho, encoding="utf-8").read()
    niveis, ordem = {}, None
    for m in BLOCO.finditer(texto):
        pares = ATRIBUTO.findall(m.group(3))
        if ordem is None:
            ordem = [k for k, _ in pares]
        niveis[int(m.group(2))] = dict(pares)
    return texto, m.group(1) if niveis else None, niveis, ordem


def numero(txt):
    """(valor, formatador) ou None se nao for numero."""
    try:
        if re.fullmatch(r"-?\d+", txt):
            return int(txt), lambda v: str(int(round(v)))
        f = float(txt)
        casas = len(txt.split(".")[1]) if "." in txt else 0
        return f, (lambda v, c=casas: ("%.*f" % (c, v)).rstrip("0").rstrip(".") or "0")
    except ValueError:
        return None


def extrapola(conhecidos, alvo):
    """Projeta um atributo para tras. `conhecidos` e [(nivel, valor)] ordenado."""
    if len({v for _l, v in conhecidos}) == 1:          # constante
        return conhecidos[0][1]
    xs = [l for l, _v in conhecidos]
    ys = [v for _l, v in conhecidos]
    # ajuste quadratico por minimos quadrados; degenera sozinho em linear e em constante
    n = len(xs)
    somas = [sum(x ** k for x in xs) for k in range(5)]
    b = [sum(y * x ** k for x, y in zip(xs, ys)) for k in range(3)]
    M = [[somas[i + j] for j in range(3)] for i in range(3)]
    for i in range(3):                                  # eliminacao de Gauss
        p = max(range(i, 3), key=lambda r: abs(M[r][i]))
        M[i], M[p] = M[p], M[i]
        b[i], b[p] = b[p], b[i]
        if abs(M[i][i]) < 1e-12:
            return ys[0]
        for r in range(i + 1, 3):
            f = M[r][i] / M[i][i]
            for c in range(i, 3):
                M[r][c] -= f * M[i][c]
            b[r] -= f * b[i]
    co = [0.0] * 3
    for i in (2, 1, 0):
        co[i] = (b[i] - sum(M[i][j] * co[j] for j in range(i + 1, 3))) / M[i][i]
    return co[0] + co[1] * alvo + co[2] * alvo * alvo


def projeta(niveis, alvos):
    """{nivel: {attr: texto}} para os niveis pedidos, a partir dos mais baixos conhecidos."""
    base = sorted(niveis)[:APOIO]
    saida = {}
    for alvo in alvos:
        linha = {}
        for attr in niveis[base[0]]:
            crus = [(l, niveis[l][attr]) for l in base]
            conv = numero(crus[0][1])
            if conv is None or any(numero(v) is None for _l, v in crus):
                linha[attr] = crus[0][1]
                continue
            fmt = conv[1]
            pontos = [(l, numero(v)[0]) for l, v in crus]
            v = extrapola(pontos, alvo)
            if isinstance(v, str):
                linha[attr] = v
            else:
                menor = min(y for _l, y in pontos)
                v = max(v, 1 if menor >= 1 else menor)     # nunca zerar o que nao era zero
                v = min(v, menor)                          # nivel baixo nao supera o nivel 9
                linha[attr] = fmt(v)
        saida[alvo] = linha
    return saida


def validar():
    print("Validacao: esconder os niveis 1..8 de quem os tem, extrapolar e comparar.\n")
    pior = 0.0
    for nome in COM_NIVEIS_BAIXOS:
        caminho = os.path.join(RAIZES[0], nome + "-templates.xml")
        _t, classe, niveis, _o = le(caminho)
        reais = {l: niveis[l] for l in range(1, 9) if l in niveis}
        altos = {l: v for l, v in niveis.items() if l >= 9}
        prev = projeta(altos, sorted(reais))
        erros = []
        for l in sorted(reais):
            for attr, real in reais[l].items():
                a, b = numero(real), numero(prev[l][attr])
                if a is None or b is None or a[0] == 0:
                    continue
                erros.append(abs(b[0] - a[0]) / abs(a[0]) * 100)
        med = sum(erros) / len(erros) if erros else 0
        mx = max(erros) if erros else 0
        pior = max(pior, med)
        print("  %-13s erro medio %5.1f%%   pior campo %5.1f%%" % (classe, med, mx))
    print("\npior erro medio entre as classes: %.1f%%" % pior)
    return 0


def aplicar():
    for nome in CLASSICAS:
        primeiro = os.path.join(RAIZES[0], nome + "-templates.xml")
        texto, classe, niveis, ordem = le(primeiro)
        faltando = [l for l in range(1, 9) if l not in niveis]
        if not faltando:
            print("  %-13s ja tem 1..8" % nome)
            continue
        novos = projeta(niveis, faltando)
        blocos = []
        for l in faltando:
            attrs = " ".join('%s="%s"' % (k, novos[l][k]) for k in ordem)
            blocos.append('\t<player_stats class="%s" level="%d">\n'
                          '\t\t<stats_template %s/>\n'
                          '\t</player_stats>' % (classe, l, attrs))
        marca = '\t<player_stats class="%s" level="9">' % classe
        for raiz in RAIZES:
            caminho = os.path.join(raiz, nome + "-templates.xml")
            if not os.path.exists(caminho):
                continue
            t = open(caminho, encoding="utf-8").read()
            if 'level="1">' in t:
                print("  %-13s ja tem nivel 1 em %s" % (nome, raiz))
                continue
            t = t.replace(marca, "\n".join(blocos) + "\n" + marca, 1)
            open(caminho, "w", encoding="utf-8", newline="").write(t)
        print("  %-13s niveis %s adicionados" % (nome, "".join(str(l) for l in faltando)))
    return 0


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "validar"
    sys.exit(validar() if modo == "validar" else aplicar())

"""
Extrai posicoes de NPC de uma captura, para popular o mundo.

O posicionamento de NPC nao esta em XML nenhum: mora nos arquivos de nivel do cliente e no
servidor. A captura e a unica fonte que temos para a 4.5 -- cada `S_PUT_NPC` que o servidor
oficial mandou traz a posicao real de um NPC no mapa em que a sessao aconteceu.

Layout do `S_PUT_NPC`, na parte que interessa:

    [f32 x][f32 y][f32 z][u32 id_entidade][u32 npc_id][u32 npc_id][u8 tipo][u8 estado][2b][u32 nome]

O payload inteiro e guardado, nao so os campos: o `S_PUT_NPC` tem tamanho variavel na captura --
107, 207, 227, 247, 267 bytes -- e reconstruir isso campo a campo e trabalho que ainda nao foi
feito. Guardando o que o servidor oficial mandou e trocando so o id de entidade, o NPC aparece
exatamente como aparecia la. O id de entidade tem o bit alto ligado (0x80......), como o cliente
4.5 espera.

O id do NPC foi identificado por cruzamento: dos offsets candidatos, 16 e 20 sao os unicos cujos
valores caem no catalogo `client_npcs.xml`, e os dois trazem o mesmo numero. O id de nome, em 28,
e o unico campo que cai na faixa dos ids de string em todos os pacotes -- e e o que o pacote leva,
nao o texto.

Um NPC e identificado pelo **id de entidade**, nao pela posicao: quem anda manda varios pacotes
com o mesmo id e coordenadas diferentes, e agrupar por distancia multiplicava esses. Guardamos o
primeiro pacote de cada id, que e onde ele estava quando entrou no alcance de visao.

O cliente so recebe o que esta no alcance de visao, entao isto cobre por onde o personagem passou,
nao o mapa inteiro.

Uso: python tools/extrai_spawns.py EmuRustDurak/replay.bin EmuRustDurak/data/spawns.csv
"""
import argparse
import struct

PUT_NPC = 0x00E
OFF_ENTIDADE = 12
OFF_ID = 16
OFF_NOME = 28


def entradas(caminho):
    dados = open(caminho, "rb").read()
    i = 0
    while i + 7 <= len(dados):
        direcao = dados[i]
        opcode = int.from_bytes(dados[i + 1:i + 3], "little")
        tamanho = int.from_bytes(dados[i + 3:i + 7], "little")
        i += 7
        if i + tamanho > len(dados):
            break
        yield direcao, opcode, dados[i:i + tamanho]
        i += tamanho


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("replay")
    ap.add_argument("saida")
    ap.add_argument("--mapa", type=int, default=120_010_000,
                    help="id do mapa em que a captura aconteceu")
    args = ap.parse_args()

    vistos = {}
    for direcao, opcode, p in entradas(args.replay):
        if direcao != 0 or opcode != PUT_NPC or len(p) < OFF_NOME + 4:
            continue
        x, y, z = struct.unpack_from("<fff", p, 0)
        # Coordenada valida e finita; o mundo tem 3072 de lado.
        if not all(0 < v < 4000 for v in (x, y)) or not -1000 < z < 4000:
            continue
        npc_id = int.from_bytes(p[OFF_ID:OFF_ID + 4], "little")
        nome_id = int.from_bytes(p[OFF_NOME:OFF_NOME + 4], "little")
        if npc_id == 0:
            continue
        entidade = int.from_bytes(p[OFF_ENTIDADE:OFF_ENTIDADE + 4], "little")
        # Um id de entidade e um NPC. O primeiro pacote dele e onde estava ao entrar em cena.
        vistos.setdefault(entidade, (npc_id, nome_id, round(x, 2), round(y, 2), round(z, 2), p))

    # NPC que anda manda posicao varias vezes, e sem agrupar isso vira um exercito de clones: na
    # captura um unico id aparece em 124 posicoes. Por id, guardamos uma posicao e descartamos as
    # que estiverem a menos de `--raio` dela.
    linhas = sorted((npc_id, nome_id, x, y, z, payload.hex())
                    for npc_id, nome_id, x, y, z, payload in vistos.values())
    print(f"{len(linhas)} NPCs, um por id de entidade")
    with open(args.saida, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# mapa,npc_id,nome_id,x,y,z,payload"
                 " -- extraido de uma captura por tools/extrai_spawns.py\n")
        for npc_id, nome_id, x, y, z, payload in linhas:
            fh.write(f"{args.mapa},{npc_id},{nome_id},{x},{y},{z},{payload}\n")

    ids = {l[0] for l in linhas}
    print(f"{len(linhas)} posicoes, {len(ids)} npc_ids distintos -> {args.saida}")


if __name__ == "__main__":
    main()

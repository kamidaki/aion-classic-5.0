"""Decodifica o XML binario da NCsoft (o que sai dos `.pak` do cliente).

Os XMLs do cliente nao sao texto: sao uma arvore tokenizada com uma tabela de strings na frente.
Depois de tirar o arquivo do pak com `tools/aion_pak.py`, ele ainda passa por aqui.

**Formato:**

```text
u8       magic, sempre 0x80
varint   tamanho da tabela, em bytes
tabela   strings UTF-16LE coladas, cada uma terminada em zero.
         Os indices do resto do arquivo contam UNIDADES de 16 bits, nao bytes.
arvore   um elemento, recursivo:
           varint  indice do nome na tabela
           varint  flags:  bit 0 = tem texto
                           bit 1 = tem atributos
                           bit 2 = tem filhos
           se tem atributos:  varint quantos, e depois pares (indice, indice)
           se tem texto:      varint indice do valor
           se tem filhos:     varint quantos, e depois cada um recursivamente
```

O varint e de 7 bits por byte, do menos significativo para o mais, com `0x80` marcando que
continua.

**Uma diferenca em relacao ao decodificador de referencia** (o `bxml/src/main.rs` do projeto
vizinho, ver [[aionemu-somente-leitura]]): la a tabela e lida pegando **so o byte baixo** de cada
unidade UTF-16, o que transforma qualquer caractere fora do ASCII em lixo. Aqui a string e
decodificada de verdade a partir das unidades de 16 bits, entao nome com acento sobrevive. A
indexacao continua sendo por unidade, que e o que os varints do arquivo esperam.

Uso:

    python tools/aion_bxml.py <arquivo.xml> <saida.xml>
    python tools/aion_bxml.py <pasta> <pasta_saida>      anda recursivo, so nos que tem magic 0x80
"""
import os
import sys

MAGIC = 0x80


class BxmlInvalido(Exception):
    pass


class _Leitor:
    __slots__ = ("b", "o")

    def __init__(self, b, o=0):
        self.b = b
        self.o = o

    def u8(self):
        v = self.b[self.o]
        self.o += 1
        return v

    def varint(self):
        """7 bits por byte, do menos significativo para o mais; 0x80 diz que continua."""
        valor = deslocamento = 0
        while True:
            byte = self.b[self.o]
            self.o += 1
            valor |= (byte & 0x7F) << deslocamento
            if not byte & 0x80:
                return valor
            deslocamento += 7


class Tabela:
    """A tabela de strings do cabecalho, indexada por unidade de 16 bits."""

    __slots__ = ("unidades", "cache")

    def __init__(self, bruto):
        # Uma unidade UTF-16LE por posicao. Os indices do arquivo contam estas unidades.
        self.unidades = memoryview(bruto).cast("H") if len(bruto) % 2 == 0 else None
        if self.unidades is None:
            # Tabela de tamanho impar nao deveria acontecer; cai para bytes crus.
            raise BxmlInvalido(f"tabela de strings com tamanho impar ({len(bruto)})")
        self.cache = {}

    def texto(self, i):
        s = self.cache.get(i)
        if s is not None:
            return s
        fim = i
        n = len(self.unidades)
        while fim < n and self.unidades[fim] != 0:
            fim += 1
        s = "".join(chr(u) for u in self.unidades[i:fim])
        self.cache[i] = s
        return s


def _escapa_texto(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _escapa_attr(s):
    return _escapa_texto(s).replace('"', "&quot;")


def _elemento(r, tab, saida, nivel):
    nome = tab.texto(r.varint())
    flags = r.varint()
    tem_texto = bool(flags & 1)
    tem_filhos = bool(flags & 4)

    # A ordem e texto primeiro, atributos depois. O decodificador de referencia le ao contrario,
    # o que passa despercebido enquanto so um dos dois bits estiver ligado -- e quebra nos
    # arquivos que tem os dois. Eram 526 dos 5.038 do cliente 5.0, todos em `index out of range`.
    texto = tab.texto(r.varint()) if tem_texto else None

    atributos = []
    if flags & 2:
        for _ in range(r.varint()):
            chave = tab.texto(r.varint())
            valor = tab.texto(r.varint())
            atributos.append(f' {chave}="{_escapa_attr(valor)}"')

    recuo = "  " * nivel
    abre = f"{recuo}<{nome}{''.join(atributos)}"

    if not tem_texto and not tem_filhos:
        saida.append(f"{abre} />\n")
        return

    if tem_texto and not tem_filhos:
        # Caso esmagadoramente mais comum: <id>100000001</id> numa linha so.
        saida.append(f"{abre}>{_escapa_texto(texto)}</{nome}>\n")
        return

    saida.append(f"{abre}>\n")
    if tem_texto:
        saida.append(f"{recuo}  {_escapa_texto(texto)}\n")
    if tem_filhos:
        for _ in range(r.varint()):
            _elemento(r, tab, saida, nivel + 1)
    saida.append(f"{recuo}</{nome}>\n")


def e_bxml(caminho):
    """Diz se o arquivo comeca com o magic do XML binario."""
    try:
        with open(caminho, "rb") as f:
            return f.read(1) == bytes([MAGIC])
    except OSError:
        return False


def decodifica(bruto):
    """Recebe os bytes do XML binario e devolve o XML em texto."""
    if not bruto:
        raise BxmlInvalido("arquivo vazio")
    r = _Leitor(bruto)
    if r.u8() != MAGIC:
        raise BxmlInvalido(f"magic errado (0x{bruto[0]:02X}, esperava 0x{MAGIC:02X})")
    tam = r.varint()
    tab = Tabela(bruto[r.o:r.o + tam])
    r.o += tam

    saida = ['<?xml version="1.0" encoding="utf-8"?>\n']
    _elemento(r, tab, saida, 0)
    return "".join(saida)


def converte(entrada, saida):
    with open(entrada, "rb") as f:
        bruto = f.read()
    xml = decodifica(bruto)
    os.makedirs(os.path.dirname(saida) or ".", exist_ok=True)
    with open(saida, "w", encoding="utf-8", newline="\n") as f:
        f.write(xml)
    return len(xml)


def _anda(entrada, saida):
    ok = falhas = 0
    if os.path.isfile(entrada):
        try:
            n = converte(entrada, saida)
            print(f"OK  {entrada} -> {saida} ({n:,} bytes)")
            return 1, 0
        except Exception as e:
            print(f"ERRO {entrada}: {e}")
            return 0, 1

    for base, _dirs, arqs in os.walk(entrada):
        for a in arqs:
            if not a.lower().endswith(".xml"):
                continue
            p = os.path.join(base, a)
            if not e_bxml(p):
                continue
            destino = os.path.join(saida, os.path.relpath(p, entrada))
            try:
                n = converte(p, destino)
                print(f"OK  {os.path.relpath(p, entrada)} ({n:,} bytes)")
                ok += 1
            except Exception as e:
                print(f"ERRO {p}: {e}")
                falhas += 1
    return ok, falhas


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    sys.setrecursionlimit(10000)
    ok, falhas = _anda(argv[0], argv[1])
    print(f"\ntotal: {ok} convertidos, {falhas} falharam")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

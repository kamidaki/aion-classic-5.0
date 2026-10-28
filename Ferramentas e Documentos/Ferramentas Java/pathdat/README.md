# Teste do PathDatMap / PathDatGrid (Java)

Classes do servidor: `game-server/src/com/lostacademy/nativepath/PathDatMap.java` (leitor do path.dat) e `PathDatGrid.java`
(A* + alisamento). Ainda **não estão ligadas** no servidor.

`voltas_oficiais.tsv`: 44 voltas oficiais de mobs (DF1 e 220040000), exportadas por
`Ferramentas Python/pathdat/voltas_captura.py <captura.pkl> <mapa> <saida.tsv>`.

```bash
S=/tmp/pathdat_cls
SRC="../../../Código Fonte - Emulador/game-server/src/com/lostacademy/nativepath"
javac -encoding UTF-8 -d $S "$SRC/PathDatMap.java" "$SRC/PathDatGrid.java" TesteVoltas.java
java -Xmx2g -cp $S TesteVoltas "../../../Código Fonte - Emulador/game-server/data" voltas_oficiais.tsv
```

Resultado em 27/10/2026: 43 de 44 voltas com afastamento <= 1,5 m (40 <= 1,0 m), busca média 6,2 ms, carga do mapa 80-210 ms.
Opção "seguir o piso" (`new PathDatGrid(mapa, true)`): 211 trechos contra 157 do comportamento oficial.

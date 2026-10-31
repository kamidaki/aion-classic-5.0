# Navmesh (.nav) a partir do geo do servidor

`GeraNav.java` gera o `data/nav/<mapa>.nav` que o `NavData` do emulador lê, usando o geo do próprio servidor
(`data/geo`: PNG do relevo, `models.mesh` e `<mapa>.geo`) e o Recast (`recast-1.5.12.jar`, Maven Central, sha1 ao lado).
O Recast só é usado para gerar o arquivo; não entra no JAR do servidor.

## Gerar

Na pasta `Emulador - Produto Final/GameServer`:

```
javac -cp "libs/*;<pasta>/recast-1.5.12.jar" -d <saida_classes> <pasta>/GeraNav.java
java -Xmx9g -Dnav.sementes=data/static_data/spawns/Npcs/120010000_Pandaemonium.xml -cp "libs/*;<pasta>/recast-1.5.12.jar;<saida_classes>" GeraNav 120010000 <saida>/120010000.nav 0 0 1850 1800
```

- Os 4 números finais recortam a área (x/y do Aion). Use a extensão do `.geo` do mapa; sem eles entra o relevo inteiro.
- `nav.sementes`: só fica a parte da malha ligada a algum spawn (tira telhados, encostas e montanhas sem NPC).
- Uma thread por padrão: o recast4j 1.5.12 tem estado compartilhado entre threads e, em paralelo, estraga blocos.

## Validar antes de instalar (pasta `testes/`)

- `NavTeste <npc_walker.xml> <dir_nav>`: pathfind do emulador entre os passos das rotas das capturas (`gera_50_capitais_movimento.py`).
  Meta: `fora_da_malha=0 sem_caminho=0 desvio=0`.
- `NavSpots <dir_nav> <mapa> <spawn.xml>`: quantos spawns caem na malha (compare com a `.nav` antiga).
- `GeoTeste <npc_walker.xml> <mapa>`: confirma que o geo tem chão nos passos oficiais (se falhar aqui, o problema é o geo).
- `NavDebug <dir_nav> <mapa> x1 y1 z1 x2 y2 z2`: imprime o caminho e os triângulos de início e fim.

## Pandaemonium (120010000), 25/10/2026

| | antiga (Lost Academy) | nova |
|---|---|---|
| triângulos | 43.273 | 53.514 |
| passos oficiais fora da malha (13 rotas) | 30 | 0 |
| trechos sem caminho / com desvio | 5 / 14 | 0 / 0 |
| spawns na malha | 261 de 447 | 343 de 447 |

A antiga está em `backup/120010000.nav.antiga_lostacademy`.

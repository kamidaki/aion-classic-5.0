# path.dat do cliente 5.0 (grade de navegação oficial)

Decodificado em 27/10/2026 a partir das capturas oficiais. O formato completo está no topo de `pathdat_50.py`.

| Arquivo | Para quê |
|---|---|
| `pathdat_50.py` | Leitor de qualquer mapa (`PathDat(worldId)`): camadas, alturas, bloqueio e grafo explícito (tipo 16) |
| `valida_capturas.py` | Compara com pontos oficiais de chão (S_MOVE/S_PUT_NPC) coletados das capturas |
| `astar_50.py` | A* na grade (8 direções, ligações do arquivo, preço da queda) + alisamento que segue as ligações |
| `voltas_captura.py` | Compara as voltas oficiais (depois do S 183) com o A*: `voltas_captura.py <captura.pkl> <mapa>` |
| `furos.py` | Lista passagens que o oficial fez e o grafo não tem |
| `compara_lost.py` | Mede o leitor do `com.lostacademy.nativepath` contra os pontos oficiais |
| `pathdat_leitor.py` + `pathdat_volta_df1.py` | Primeiro leitor (só tipo 16) e o A* que reproduz a volta e a queda oficiais do mob 210365 em DF1 |

## Resultado
- Os 118 `data/native-path/*/*.dat` fecham no fim do arquivo (310050000, 330040000 e 800050000 têm 512 m, não os 1024 do world_maps).
- 122.052 pontos oficiais de chão em 10 mapas: 99,10% com |dz| < 0,15 m, 0,45% < 0,5 m (rampa).
- 0 de 792 pontos oficiais em centro de célula caem em célula bloqueada.
- A busca na grade reproduz a volta oficial em DF1: mesma quina, queda 308,90 → 297,71, mesmo ponto final.

## Busca de caminho (captura de escada/rampa 27/10 03:01, mapa 220040000 + DF1)
- 43 de 44 voltas oficiais reproduzidas (afastamento <= 1,5 m; 41 <= 1,0 m), incluindo a reta de 79,4 m que corta a rampa.
- Regras que o oficial segue: nó tipo 16 só é entrado pelo lado em que tem ligação (a lateral da rampa não sobe);
  a divisa de setor vale nos dois sentidos; a reta do alisamento anda pelas ligações e ignora a altura interpolada
  (por isso o mob "atravessa" rampa e escada); queda quebra a reta e custa ~0,4 x a altura.
- Ligação entre setores (u32): bits 7-31 = offset absoluto do nó no bloco 1 (23.759/23.759); com offset 0/1 o destino
  é camada simples e os bits 0-6 ainda não estão entendidos (82-95% batem com o andar por altura) -> usa o piso mais perto.
- 1 caso não reproduzido: queda escolhida num empate de 0,7 m com a rampa.

## Spawns pelo cliente (27/10)
- `extrai_spawns_cliente.py <saida>`: lê os 137 `levels/*/mission_mission0.xml` do cliente 5.0 (objetos `SP` = NPC/mob, `HSP` = coleta),
  nome -> id pelo `client_npcs.xml`/`gather_src.xml`, mapa pelo `WorldId.xml`. Grava `<saida>/Npcs` e `<saida>/Gather` no formato do servidor.
  - z: `Ignore_heightcheck=0` (112.661 de 112.662 pontos) = o jogo cola no chão -> piso livre da grade mais perto do z do editor
    (o z do editor fica em média 3,7 m acima do chão). Tipos que voam no oficial mantêm o z do editor.
  - h: `floor((Angles z + 0,5) / 3) - 30` (mod 120). random_walk: `iidle_range` > 0. respawn: o do spawn atual (cliente não tem).
- `valida_spawns_cliente.py <capturas .pkl>`: contra 5.938 S_PUT_NPC de Tiamaranta Mesa e Gelkmaros: todos os tipos presentes;
  NPCs parados no ponto: z certo 93,6% (o z do editor acertaria 15,7%), heading exato 96,1% (os outros giraram depois de andar).
- Saída de todos os mapas: 93.104 NPCs + 18.468 coletas, 151 arquivos, todos válidos no `static_data.xsd`.
- Atenção ao aplicar: 119 tipos sem template no servidor; 15.700 pontos de 4.389 tipos existem só no servidor (quest, instância,
  evento, cerco, 4.x) e 11 mapas não têm mission no cliente -> mesclar por tipo, não trocar o arquivo.

## Pendente
- Os 512 bytes extras das camadas ímpares (4 bits por célula) ainda não têm significado conhecido.
- Respawn oficial por tipo (medir nas capturas: morte -> S_PUT_NPC com flag de nascimento no mesmo ponto).

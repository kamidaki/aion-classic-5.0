# Subsistema Native-Path CryEngine (`com.lostacademy.nativepath`) [DEPRECATED / INATIVO]

> [!WARNING]
> **ESTE MÓDULO ESTÁ DESATIVADO E DEPRECADO.**
> O servidor utiliza integralmente o sistema de navegação **NavMesh (`.nav`)** gerenciado por `com.lostacademy.nav.NavService` e `com.lostacademy.nav.NavData`.
> 
> O código contido neste pacote foi preservado exclusivamente para fins de histórico e consulta arquitetural, não possuindo referências ativas em tempo de execução no servidor.

## 1. Histórico e Propósito Original

O subsistema `native-path` foi uma implementação para consumir diretamente os arquivos compilados da CryEngine (`*-path.dat`) extraídos das pastas `Levels/` do cliente Aion Classic.

## 2. Substituição pelo NavMesh (.nav)

Todo o fluxo de navegação, evasão de obstáculos, escadas em caracol, desníveis de relevo, subidas íngremes e pontes estreitas é executado nativamente pela malha de polígonos 3D (`.nav`) carregada em `data/nav/`.

Configuração ativa em `geodata.properties`:
```properties
gameserver.geodata.nav.enable = true
gameserver.geodata.nav.dir = data/nav/
gameserver.geodata.forced_move.nav_fallback = true
```

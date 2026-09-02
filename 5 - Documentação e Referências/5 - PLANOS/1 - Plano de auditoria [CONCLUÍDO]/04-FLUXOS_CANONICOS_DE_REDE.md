# 04 - Fluxos Canônicos de Rede: Aion Classic 5.0 EU

## 1. Cadeia Causal Estrita
Todo ciclo de interação de rede deve respeitar a Regra Principal de Arquitetura:

$$\mathbf{Captura\ (PCAP)} \longrightarrow \mathbf{Protocolo\ (Wire)} \longrightarrow \mathbf{Evento} \longrightarrow \mathbf{Estado\ (World/Entity)} \longrightarrow \mathbf{Sistema\ (Gameplay\ Service)} \longrightarrow \mathbf{Resposta\ (Broadcast)}$$

---

## 2. Sequência de Entrada no Mundo (Level Ready) Baseada em PCAP Oficial

Nas capturas de Elyos e Asmodians, o cliente oficial finaliza o carregamento dos mapas e recursos e envia `C_LEVEL_READY`. A sequência estrita de resposta do servidor é:

1. `cliente -> C_LEVEL_READY (decOp 0x0019, wire 0x00EB, 0 bytes)`
2. `servidor -> S_INVINCIBLE_TIME (op 0x00FE, len 4 bytes)`: 60 segundos
3. `servidor -> S_PUT_USER (op 0x0020, len 333 bytes)`: Avatar 3D e entidade do jogador
4. `servidor -> S_INVINCIBLE_TIME (op 0x00FE, len 4 bytes)`: 60.000 ms
5. `servidor -> S_INVISIBLE_LEVEL (op 0x0043, len 7 bytes)`: Cessação de piscar / estado visual
6. `servidor -> S_BUILDER_LEVEL (op 0x00EE, len 29 bytes)`: Nível de permissão/builder
7. `servidor -> S_PATH_FLY (op 0x0031, len 15 bytes)`: Estado de voo inicial
8. `servidor -> S_SKILL_PENALTY_STATUS (op 0x00D7, len 11 bytes)`: Penalidade de morte/skills
9. `servidor -> S_CUSTOM_ANIM (op 0x0093, len 19 bytes)`: Animações de pose
10. `servidor -> S_WORLD_SCENE_STATUS (op 0x008B, len 9 bytes)`: Transição de cena e liberação do HUD
11. `servidor -> S_PUT_NPC (op 0x000E)`: Spawns de NPCs e monstros na área de visão
12. `servidor -> S_SERIAL_KILLER_LIST (op 0x0053, len 18 bytes)`
13. `servidor -> S_TARGET_INFO (op 0x0029, len 14 bytes)`
14. `servidor -> S_WORLD_INFO (op 0x00EC, len 11 bytes)`: Mapa e canais
15. `servidor -> S_WIELD (op 0x0024)`: Equipar armas nas mãos
16. `servidor -> S_EVENT (StorageType.CUBE)`: Tamanho de cubo/inventário
17. `servidor -> S_HIT_POINT & S_MANA_POINT`: Sincronização de HP/MP inicial

---

## 3. Desacoplamento e Proteção contra Reentrância
- **Guarda de Execução Única em `CM_LEVEL_READY`**: Se o jogador já estiver spawned no mundo, pacotes repetidos de Level Ready devem ser ignorados para impedir re-spawns fantasmas ou vazamento de tarefas periódicas.
- **Broadcast de Movimentação e Ações**: Pacotes de movimento (`C_MOVE_NEW`) e ataque (`C_ATTACK`) devem validar estado no `PlayerController` antes de acionar `World.getInstance().updatePosition(...)`.

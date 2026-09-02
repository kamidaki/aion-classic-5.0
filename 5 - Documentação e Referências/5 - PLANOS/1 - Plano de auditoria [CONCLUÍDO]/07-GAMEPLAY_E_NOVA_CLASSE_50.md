# 07 - Gameplay e Classes 5.0 (Soul Reaper, Luminess, Monk, etc.)

## 1. Tratamento Diferenciado de Classes e Isolamento de Capturas
- **Alerta Metodológico**: As capturas de Wireshark fornecidas foram executadas jogando com uma única classe por vez (ex: Soul Reaper nos tutoriais). O protocolo de rede global (handshake, entrada no mundo, login, inventário, movimentação, chat) é comum a todas as classes. Os identificadores de equipamento, árvores de skills e animações são específicos por classe.
- Não restringir o comportamento global às particularidades da classe gravada na captura.

---

## 2. A Classe Soul Reaper (Reaper / Foice)
- **Tipo de Arma**: Scythe (Foice de duas mãos).
- **Tipo de Armadura**: Tecido/Couro com atributos mágicos/físicos específicos da 5.0.
- **Animações e Efeitos**:
  - `S_WIELD`: Empunhadura da foice em posição de combate ao apertar a tecla `X`.
  - Habilidades com combos de foice e invocações de almas.

---

## 3. Progressão de Nível e Tutorial
- No mapa de tutorial do Classic 5.0:
  - Vida inflada conforme capturado no roteiro (`31.660 HP` durante o warmup inicial).
  - Voo ilimitado nas seções de voo do tutorial.
  - Sequência de diálogos com NPCs para transição ao mapa oficial principal (Pandaemonium / Sanctum).
- Desacoplamento de missões de tutorial e missões principais via `QuestEngine`.

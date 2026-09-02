# 03 - Estruturas e Offsets de Pacotes: Aion Classic 5.0 EU

## 1. Pacote `S_PUT_USER` (Opcode 0x0020)
- **Tamanho Oficial Capturado**: 333 bytes para personagem de nível 1 recém-criado.
- **Campos Críticos do Layout 5.0**:
  - `ObjectId` (4 bytes int)
  - Coordenadas de Mundo: `x` (float), `y` (float), `z` (float), `heading` (byte)
  - `TemplateId` / `PlayerClassId`: Deve mapear adequadamente para as classes novas (12: Luminess, 13: Phoenix, 14: Reaper, 15: Soul Reaper, etc.).
  - `Gender`, `Race`
  - Estrutura de Customização Visual (Face, Hair, Skin, Tattoos, Heights, Proportions): Alinhado rigorosamente sem desvios de offset para evitar deformação ou desconexão do cliente.
  - Slots de Equipamentos: Armas, Armaduras, Asas, Wardrobe (Cosméticos 5.0).
  - Flags de Estado: `visualState` (standing, invisible, blinking), `seeState`.

---

## 2. Pacote `S_CHARACTER_LIST` (Opcode 0x00C7)
- **Comportamento em PCAPs**:
  - Bloco inicial de metadados de conta e contagem de personagens (11 bytes).
  - Blocos de personagens: 777 bytes por personagem criado no lobby.
- **Campos Obrigatórios**:
  - Informações de nível, classe, EXP, mapa de logout.
  - Aparência física completa (layout binário idêntico ao do `S_PUT_USER`).
  - Lista de itens equipados para renderização no lobby de seleção.

---

## 3. Pacote `S_INVISIBLE_LEVEL` (Opcode 0x0043)
- **Tamanho Oficial Capturado**: 7 bytes.
- **Estrutura Binária Exata**:
  - `writeD(playerObjId)` (4 bytes)
  - `writeC(visualState)` (1 byte, ex: 64 = 0x40 piscando no spawn)
  - `writeC(seeState)` (1 byte)
  - `writeC(visualState == 64 ? 1 : 0)` (1 byte)
- **Observação**: Corrigir a chamada em `CM_LEVEL_READY`, que enviava incorretamente `S_CUSTOM_ANIM` para esse slot.

---

## 4. Pacote `S_CUSTOM_ANIM` (Opcode 0x0093)
- **Tamanho Oficial Capturado**: 19 bytes (para ação 7).
- **Estrutura Binária Exata**:
  - `writeC(action = 7)` (1 byte)
  - `writeD(playerObjId)` (4 bytes)
  - `writeH(motion1)` .. `writeH(motion5)` (5 shorts = 10 bytes)
  - Padding/Flags (4 bytes)
  - Total = 19 bytes.

# 06 - Dados Estáticos e XMLs: Aion Classic 5.0 EU

## 1. Diretrizes Rígidas de Integridade de Dados
Conforme mandatado no `CONTEXT.md`:
- **Proibição Absoluta de Bypass no Java**: Nenhum dado estático ausente pode ser substituído por valores mágicos ou lógica hardcoded.
- **Fonte da Verdade Oficial 5.0**:
  - `D:\AION CLASSIC 5.0 - EMULADOR\5 - Documentação e Referências\4 - Client 5.0 - Dados Extraidos\data`
- **Ferramentas Oficiais de Extração e Sincronização**:
  - `D:\AION CLASSIC 5.0 - EMULADOR\6 - Ferramentas\parsersXML`
- **Destino dos Dados Estáticos do GameServer**:
  - `D:\AION CLASSIC 5.0 - EMULADOR\1 - Código Fonte [Emulador]\GameServer\data\static_data`

---

## 2. Validação e Cobertura dos Templates

1. **Itens (`items/`)**:
   - Confirmar se todos os itens de Soul Reaper, Luminess, Monk e classes originais estão gerados e com atributos, slots de gemas e modelos 3D corretos.
2. **Kits Iniciais (`player_initial_data.xml`)**:
   - Conferir se todas as armas (Foice / Scythe, Luvas, Clavas, etc.) e vestimentas iniciais de cada classe e raça estão devidamente cadastradas e validadas contra `items.xml`.
3. **Spawns e Coordenadas de Entrada (`spawns/`, `world_maps.xml`)**:
   - Spawn inicial em Sanctum para Elyos: `mapId = 110010000`, coordenadas oficiais.
   - Spawn inicial em Pandaemonium para Asmodians: `mapId = 120010000`, coordenadas oficiais.
4. **Habilidades (`skills/`, `skill_tree/`)**:
   - Todas as skills da 5.0 mapeadas sem lançar exceções de template desconhecido na inicialização do servidor.

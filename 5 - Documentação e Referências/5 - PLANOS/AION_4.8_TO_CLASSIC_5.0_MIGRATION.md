# AION 4.8 RETAIL → AION CLASSIC 5.0 EU — ROADMAP MESTRE DE MIGRAÇÃO

> **Status Geral**: `FASES 1 A 8 CONCLUÍDAS | AGUARDANDO FASE 9 (TASKMANAGER)`  
> **Ambiente**: Java 25 LTS (Oracle JDK 25.0.2) | Maven 3.9.9 | MySQL 9.5.0  
> **Referência Estrutural**: AION 4.8 Retail (`5 - Documentação e Referências/3 - JAVA EMU - 4.8 RETAIL`)  
> **Implementação Alvo**: AION Classic 5.0 EU (`1 - Código Fonte [Emulador]`)  
> **Fonte da Verdade de Rede / Protocolo**: Wireshark Oficial Classic 5.0 (`5 - Documentação e Referências/2 - Wireshark - Oficial Classic 5.0`)  

---

## 1. Princípios Inegociáveis de Migração

1. **Prioridade Absoluta do Classic 5.0**:
   - Pacotes de rede, opcodes, offsets, estruturas de pacotes e comportamentos específicos do Classic 5.0 **SEMPRE PREVALECEM**.
   - O 4.8 é exclusivamente uma referência de robustez arquitetural, concorrência e lógica madura de gameplay.
2. **Substituição Total, Sem Mesclagem**:
   - Ao migrar um módulo, a pasta de destino é completamente purgada antes de receber o conteúdo do 4.8.
   - Nenhum arquivo obsoleto ou descontinuado deve ser mantido sem motivo técnico explícito.
3. **Migração Sequencial Incremental (Uma Pasta de Cada Vez)**:
   - Nenhuma pasta subsequente é iniciada até que a anterior esteja totalmente compilada, adaptada, validada, testada, commitada e documentada.
4. **Sem Mascaramento de Erros**:
   - Proibido esvaziar métodos, retornar `null`/`false` dummy ou desativar lógica apenas para forçar compilação.
5. **Compatibilidade Rigorosa com Java 25**:
   - Utilização de coleções modernas, `ConcurrentHashMap`, `StampedLock`, Project Loom onde aplicável, sem resíduos legados.

---

## 2. Relação e Sequência de Módulos a Migrar

| Ordem | Módulo / Diretório | Documento de Rastreamento | Status | Commit |
| :---: | :--- | :--- | :---: | :---: |
| **01** | `controllers` | [`MIGRATION_CONTROLLERS.md`](file:///D:/AION%20CLASSIC%205.0%20-%20EMULADOR/5%20-%20Documenta%C3%A7%C3%A3o%20e%20Refer%C3%AAncias/5%20-%20PLANOS/MIGRATION_CONTROLLERS.md) | `[CONCLUÍDO]` | `5d8d0b764` |
| **02** | `ai` | [`MIGRATION_AI.md`](file:///D:/AION%20CLASSIC%205.0%20-%20EMULADOR/5%20-%20Documenta%C3%A7%C3%A3o%20e%20Refer%C3%AAncias/5%20-%20PLANOS/MIGRATION_AI.md) | `[CONCLUÍDO]` | `2d5b7c352` |
| **03** | `geoEngine` | [`MIGRATION_GEOENGINE.md`](file:///D:/AION%20CLASSIC%205.0%20-%20EMULADOR/5%20-%20Documenta%C3%A7%C3%A3o%20e%20Refer%C3%AAncias/5%20-%20PLANOS/MIGRATION_GEOENGINE.md) | `[CONCLUÍDO]` | `a84231733` |
| **04** | `model` | [`MIGRATION_MODEL.md`](file:///D:/AION%20CLASSIC%205.0%20-%20EMULADOR/5%20-%20Documenta%C3%A7%C3%A3o%20e%20Refer%C3%AAncias/5%20-%20PLANOS/MIGRATION_MODEL.md) | `[CONCLUÍDO]` | `d817758a2` |
| **05** | `questEngine` | [`MIGRATION_QUESTENGINE.md`](file:///D:/AION%20CLASSIC%205.0%20-%20EMULADOR/5%20-%20Documenta%C3%A7%C3%A3o%20e%20Refer%C3%AAncias/5%20-%20PLANOS/MIGRATION_QUESTENGINE.md) | `[CONCLUÍDO]` | `659045089` |
| **06** | `restrictions` | [`MIGRATION_RESTRICTIONS.md`](file:///D:/AION%20CLASSIC%205.0%20-%20EMULADOR/5%20-%20Documenta%C3%A7%C3%A3o%20e%20Refer%C3%AAncias/5%20-%20PLANOS/MIGRATION_RESTRICTIONS.md) | `[CONCLUÍDO]` | `235f0b27a` |
| **07** | `skillengine` | [`MIGRATION_SKILLENGINE.md`](file:///D:/AION%20CLASSIC%205.0%20-%20EMULADOR/5%20-%20Documenta%C3%A7%C3%A3o%20e%20Refer%C3%AAncias/5%20-%20PLANOS/MIGRATION_SKILLENGINE.md) | `[CONCLUÍDO]` | `10911a78a` |
| **08** | `spawnengine` | [`MIGRATION_SPAWNENGINE.md`](file:///D:/AION%20CLASSIC%205.0%20-%20EMULADOR/5%20-%20Documenta%C3%A7%C3%A3o%20e%20Refer%C3%AAncias/5%20-%20PLANOS/MIGRATION_SPAWNENGINE.md) | `[CONCLUÍDO]` | `616225614` |
| **09** | `taskmanager` | `MIGRATION_TASKMANAGER.md` | `[PENDENTE]` | - |
| **10** | `world` | `MIGRATION_WORLD.md` | `[PENDENTE]` | - |
| **11** | `utils` | `MIGRATION_UTILS.md` | `[PENDENTE]` | - |
| **12** | `services` | `MIGRATION_SERVICES.md` | `[PENDENTE]` | - |
| **13** | `data/handlers/ai/quests` e `data/handlers/ai/worlds` | `MIGRATION_DATA_HANDLERS.md` | `[PENDENTE]` | - |

---

## 3. Critério de Conclusão (Definition of Done) por Fase

- [x] Destino anterior completamente removido.
- [x] Implementação de referência 4.8 migrada.
- [x] Todas as dependências e tipos adaptados à API 5.0.
- [x] Projeto compilado com sucesso (`BUILD SUCCESS`) no Java 25.
- [x] Protocolo e pacotes oficiais 5.0 validados com capturas Wireshark.
- [x] Servidores construídos e publicados pelo pipeline (`build-server.bat`).
- [x] Diff do Git revisado e limpo de resíduos.
- [x] Commit e Push realizados com mensagem em Português.
- [x] Documento individual da fase e Roadmap Mestre atualizados.

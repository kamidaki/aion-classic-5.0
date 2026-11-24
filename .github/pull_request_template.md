## Resumo das Alterações

<!-- Descreva de forma objetiva qual problema PvE ou melhoria de compatibilidade com o Aion Classic 5.0 Oficial EU (Gameforge — GSID 1) este Pull Request implementa. -->

Fixes #(issue)

---

## Componente Afetado (Escopo Estrito — GameForge GSID 1)

> **Atenção:** Pull Requests que mencionem ou modifiquem servidores secundários (GSID 2 / GSID 3) ou alterem o idioma padrão do projeto para inglês **não serão aceitos**. A única exceção referente a idioma é a implementação de sistema **multilínguas** com escolha de idioma pelo usuário.

- [ ] `GameServer GameForge` (`game-server-gameforge` — GSID 1 | Referência Oficial EU)
- [ ] `LoginServer` (`login-server` — compatibilidade GameForge GSID 1)
- [ ] `ChatServer` (`chat-server` — compatibilidade GameForge GSID 1)
- [ ] `Commons` (`commons` — núcleo compartilhado)
- [ ] `Client Hook` (`version.dll` — conectividade e fixes de cliente)
- [ ] `Sistema Multilínguas (l10n)` (sem alterar idioma padrão Português)
- [ ] `Documentação / Build / CI` (`README.md`, `Ferramentas e Documentos/docs/`, Maven, `.github/`)

---

## Tipo de Mudança

- [ ] Correção de Bug (*bug fix*)
- [ ] Fidelidade PvE Gameforge EU (skills, quests, NPCs, drops, instâncias, eventos, combate)
- [ ] Otimização de Performance (*perf*)
- [ ] Melhoria de Segurança (*security*)
- [ ] Sistema Multilínguas (*i18n / l10n*)
- [ ] Documentação / Build / CI (*docs / build / ci*)

---

## Checklist Obrigatória de Validação

- [ ] **Escopo Exclusivo GameForge GSID 1:** Confirmo que este PR contribui exclusivamente para o objetivo oficial EU no **GameServer 1 (GameForge GSID 1)** e NÃO contém alterações nem referências ao GSID 2 ou GSID 3.
- [ ] **Preservação do Idioma Padrão:** Confirmo que o idioma padrão do projeto (**Português / PT-BR**) foi preservado (alterações de idioma restringem-se ao suporte multilíngue selecionável).
- [ ] **Compilação Limpa e Testes (JDK 25):** `mvn clean package --file "Código Fonte - Emulador/pom.xml"` executado com sucesso e sem regressões nos testes.
- [ ] **Evidências Oficiais Gameforge:** Comportamentos, fórmulas, dados estáticos e pacotes foram comparados contra a referência oficial do Aion Classic 5.0 EU (incluindo Ghidra/Wireshark e capturas/logs reais quando aplicável).
- [ ] **Zero Dados Fictícios / Bypass:** Correções em dados estáticos foram aplicadas nos XMLs canônicos sem gambiarras em Java.
- [ ] **Higienização e Portabilidade:** Nenhuma credencial real, IP privado, token secreto ou caminho fixo local (`C:\`, `D:\`) foi adicionado.

---

## Evidências e Registros de Teste

<!-- Inclua aqui os resultados da compilação/testes, comparações oficiais e imagens ou registros de execução. -->

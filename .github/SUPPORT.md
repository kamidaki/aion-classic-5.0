# Guia de Suporte, Diagnóstico e Escopo — AION CLASSIC 5.0 EMULADOR

## 1. Declaração Oficial de Fornecimento (AS-IS)

O **Aion Classic 5.0 — Emulador Oficial** é disponibilizado estritamente **"COMO É" (*AS-IS*)**, exclusivamente para **testes, preservação histórica e estudos de engenharia de software e sistemas distribuídos**.  
**Este repositório NÃO é um produto comercial e NÃO oferece suporte técnico para instalação, operação ou configuração de ambientes de terceiros.**

---

## 2. Lista Rápida de Diagnóstico

Antes de submeter um relatório de falha (*issue*), execute o seguinte roteiro de verificação:

1. **Supervisor Nativo em Rust (`Aion Classic - EMULADOR.exe`):**
   - Certifique-se de que o supervisor está ativo em `Emulador - Produto Final\`.
   - Painel web administrativo acessível em `http://127.0.0.1:18080/`.
2. **Sequência Obrigatória de Boot:**
   - O `ChatServer` (porta `10241`) deve estar 100% online antes do LoginServer.
   - O `LoginServer` (porta `2106`) deve estar online antes de qualquer GameServer.
   - Cada `GameServer` ativo (`GameForge` na `7777`, `Remake` na `7778`, `BattleRoyale` na `7779`) deve estar conectado ao LoginServer e ChatServer.
3. **Schemas do Banco de Dados no MySQL:**
   - Verifique a existência dos schemas segregados: `aionclassic_ls`, `aionclassic_cs`, `aionclassic_gs`, `aionclassic_gs2`, `aionclassic_gs3`.
4. **Módulo Injetado no Cliente (`version.dll`):**
   - Certifique-se de que a `version.dll` mais recente foi compilada e está presente em `D:\GameForge\aionclassic\bin64\version.dll`.

---

## 3. Problemas Comuns e Soluções Rápidas

* **"Não tem servidor de autenticação disponível" no cliente**:
  Compile a `version.dll` executando `Ferramentas e Documentos/Códigos bin64/Código Fonte - Version.dll/build.bat` para garantir que o bypass e a resolução dinâmica de IPs estejam ativos, e verifique se o LoginServer está online na porta 2106.
* **Conexão Rejeitada pelo GeoIP**:
  Adicione o código do país ou o IP local em `Config/network/geo_firewall.properties` (`geo.firewall.allowed_countries` ou `geo.firewall.manual_whitelist_ips`).
* **GameServer não visível na lista**:
  Verifique se o identificador GSID (1, 2 ou 3) está registrado e se a senha em `network.properties` coincide com o cadastro na tabela `aionclassic_ls.gameservers`.

---

## 4. Comunidade no Discord e Desbloqueio

O servidor oficial no Discord (**[https://discord.gg/Sjdrsg3gcb](https://discord.gg/Sjdrsg3gcb)**) não é um canal de suporte técnico. O acesso de escrita aos canais é liberado exclusivamente após a aprovação (*merge*) de um Pull Request técnico real neste repositório contendo `Discord-User: @seu_usuario` e acompanhado de evidências oficiais com testes e imagens.


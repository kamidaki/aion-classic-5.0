# Código de Conduta da Comunidade Técnica — AION CLASSIC 5.0 EMULADOR

<p align="center">
  <a href="./CODE_OF_CONDUCT.md"><img src="https://img.shields.io/badge/Idioma-Portugu%C3%AAs_Brasil_(Padr%C3%A3o)-10b981?style=for-the-badge&logo=markdown&logoColor=white" alt="PT-BR Padrão" /></a>
  <a href="./README.md"><img src="https://img.shields.io/badge/Documenta%C3%A7%C3%A3o-README_%26_CONTEXT-3b82f6?style=for-the-badge&logo=markdown&logoColor=white" alt="Documentação" /></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Ambiente-Pesquisa_de_Engenharia-0ea5e9?style=flat-square&logo=github&logoColor=white" alt="Pesquisa" />
  <img src="https://img.shields.io/badge/Toler%C3%A2ncia_a_Pirataria-ZERO-ef4444?style=flat-square" alt="Zero Pirataria" />
  <img src="https://img.shields.io/badge/Suporte_T%C3%A9cnico-PROIBIDO_SOLICITAR-dc2626?style=flat-square" alt="Proibido Pedir Suporte" />
</p>

> [!IMPORTANT]
> **PROPÓSITO DESTE CÓDIGO DE CONDUTA:**  
> O **Aion Classic 5.0 — Emulador Oficial** é um ambiente estritamente técnico de estudo em engenharia de software, sistemas distribuídos em **Java 25 LTS**, supervisão nativa em **Rust** e física tridimensional **CryEngine Native-Path**. Este Código de Conduta aplica-se a todas as interações no GitHub (`Issues`, `Pull Requests`, `Commits`) e no servidor oficial do Discord (`https://discord.gg/Sjdrsg3gcb`).

---

## 1. Diretrizes de Postura Técnica Esperada

1. **Rigor Científico e Comprovação Empírica:** Toda discussão técnica ou submissão de código deve ser acompanhada de dados objetivos: versão do cliente (`Aion Classic 5.0 EU — PE32+ bin64`), evidências de pacotes de rede (`Wireshark - Oficial Classic 5.0`), validação de tabelas extraídas do cliente oficial (`Client 5.0 - Dados Extraidos`) e compilação limpa sem erros no Maven (`Java 25 LTS`) e Cargo (`Rust`).
2. **Respeito à Política de Zero Suporte (*AS-IS*):** Compreenda que os mantenedores não prestam consultoria nem auxílio de instalação, configuração de MySQL/MariaDB ou operação de servidores (consulte [`SUPPORT.md`](./SUPPORT.md)).
3. **Preservação do Padrão Arquitetural e Linguístico:** Mantenha toda a documentação técnica e mensagens de commit estritamente em Português Brasil, sem emojis, sem caminhos de disco fixos (*hardcoded*), utilizando diagramas Mermaid, alertas nativos do Markdown e mantendo a sincronização rigorosa entre `Código Fonte - Emulador` e `Emulador - Produto Final` (consulte [`CONTEXT.md`](./CONTEXT.md)).
4. **Respeito à Regra de Acesso ao Discord:** Aguarde a aprovação (*merge*) de uma contribuição real via Pull Request com `Discord-User: @seu_usuario` para ter acesso de escrita liberado no Discord.

---

## 2. Condutas Estritamente Proibidas e Sanções Aplicáveis

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#0f172a', 'primaryTextColor': '#f8fafc', 'primaryBorderColor': '#ef4444', 'lineColor': '#ef4444'}}}%%
flowchart TD
    Incident["Ocorrência Identificada no GitHub ou no Discord"]
    Incident --> Type{"Classificação da Violação"}
    Type -->|"Pedido de Suporte / Ajuda de Instalação"| S1["Fechamento Imediato da Issue/PR<br/>ou Remoção da Mensagem"]
    Type -->|"PR Sem Testes / Com Bypass XML / Caminhos Fixos"| S2["Rejeição Sumária do Pull Request<br/>Sem Análise de Código"]
    Type -->|"Links de Pirataria (Cliente Completo / Binários Proprietários)"| S3["Exclusão Imediata + Banimento Permanente<br/>do GitHub e do Discord"]
    Type -->|"Tentativa de Venda, Cash Shop ou Uso Comercial"| S4["Banimento Permanente + Registro<br/>de Violação de Licença"]
```

| Infração | Nível de Gravidade | Medida Administrativa |
| :--- | :---: | :--- |
| **Solicitar suporte técnico, ajuda para configurar banco MySQL, cliente ou compilar o emulador** | ![Média](https://img.shields.io/badge/M%C3%89DIA-f59e0b?style=flat-square) | Fechamento sumário da *Issue* ou exclusão da mensagem por violação da cláusula *AS-IS*. |
| **Submeter Pull Request sem validação, com caminhos fixos (`C:\`, `D:\`), bypass de XML ou sem atualizar `Emulador - Produto Final`** | ![Alta](https://img.shields.io/badge/ALTA-f97316?style=flat-square) | Fechamento imediato do Pull Request e manutenção do bloqueio no Discord. |
| **Publicar links para download de clientes completos, instaladores proprietários ou chaves privadas** | ![Crítica](https://img.shields.io/badge/CR%C3%8DTICA-ef4444?style=flat-square) | Remoção imediata do conteúdo e banimento definitivo do GitHub e do Discord. |
| **Oferecer serviços pagos, venda de emulador, assinaturas, Cash Shop ou uso comercial** | ![Crítica](https://img.shields.io/badge/CR%C3%8DTICA-dc2626?style=flat-square) | Banimento definitivo e revogação imediata da licença de pesquisa. |

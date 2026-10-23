# Guia de Contribuição e Regras Explícitas de Pull Request — AION CLASSIC 5.0 EMULADOR

<p align="center">
  <a href="./CONTRIBUTING.md"><img src="https://img.shields.io/badge/Idioma-Portugu%C3%AAs_Brasil_(Padr%C3%A3o)-10b981?style=for-the-badge&logo=markdown&logoColor=white" alt="PT-BR Padrão" /></a>
  <a href="./CONTEXT.md"><img src="https://img.shields.io/badge/Arquitetura-CONTEXT.md-3b82f6?style=for-the-badge&logo=markdown&logoColor=white" alt="CONTEXT.md" /></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Pull_Requests-10_Regras_Obrigat%C3%B3rias-0ea5e9?style=flat-square&logo=github&logoColor=white" alt="10 Regras" />
  <img src="https://img.shields.io/badge/Backend-Java_25_LTS_(Zero_Javolution)-10b981?style=flat-square&logo=openjdk&logoColor=white" alt="Java 25 LTS" />
  <img src="https://img.shields.io/badge/Supervisor-Rust_MSVC_x64-6366f1?style=flat-square&logo=rust&logoColor=white" alt="Rust x64" />
  <img src="https://img.shields.io/badge/Portabilidade-Zero_Caminhos_Fixos-ef4444?style=flat-square" alt="Zero Hardcoded Paths" />
</p>

> [!CAUTION]
> **LEITURA OBRIGATÓRIA ANTES DE SUBMETER QUALQUER CÓDIGO OU PULL REQUEST:**  
> 1. **NENHUM SUPORTE OU AJUDA SERÁ CONCEDIDA:** O projeto é disponibilizado como é (*AS-IS*), exclusivamente para testes, preservação histórica e estudos de engenharia (consulte [`SUPPORT.md`](./SUPPORT.md)).  
> 2. **REJEIÇÃO IMEDIATA DE PRs INCOMPLETOS:** Qualquer Pull Request enviado sem compilação limpa (`mvn clean package` + `cargo build --release`), sem sincronizar os artefatos em `Emulador - Produto Final`, contendo caminhos de disco fixos (`C:\`, `D:\`), utilizando *workarounds* em Java para suprir falta de dados nos XMLs, ou fora do padrão de commits em Português Brasil será **fechado e rejeitado imediatamente sem análise**.

---

## 1. Fluxo de Trabalho e Desbloqueio do Bate-Papo no Discord

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#0f172a', 'primaryTextColor': '#f8fafc', 'primaryBorderColor': '#38bdf8', 'lineColor': '#38bdf8'}}}%%
sequenceDiagram
    autonumber
    actor Dev as Colaborador
    participant Local as Ambiente Local (Java 25 + Rust)
    participant GH as GitHub (Pull Request)
    participant Maintainer as Mantenedor (@kamidaki)
    participant Discord as Servidor Discord Oficial

    Dev->>Local: Implementa melhoria seguindo a cadeia PCAP -> Wire -> Evento -> Estado -> Service -> Broadcast
    Dev->>Local: Compila Maven (Java 25 LTS) e Supervisor Rust + sincroniza Emulador - Produto Final
    Local-->>Dev: Resultado: Build 100% limpo e validado em execução real
    Dev->>Local: Atualiza README.md e CONTEXT.md (se aplicável)
    Dev->>GH: Envia Commit em Português (uma linha por alteração) + PR detalhado com Discord-User
    GH->>Maintainer: Aciona revisão técnica obrigatória
    alt PR Cumpre todas as 10 Regras Explícitas
        Maintainer->>GH: Aprova e realiza Merge na branch main
        Maintainer->>Discord: Libera permissão de escrita no chat para o Discord-User informado
    else PR Viola qualquer regra ou contém gambiarras/caminhos fixos
        Maintainer->>GH: Fecha e rejeita imediatamente o Pull Request
    end
```

---

## 2. As 10 Regras Explícitas de Pull Request

| # | Regra Obrigatória | Exigência Técnica de Auditoria |
| :---: | :--- | :--- |
| **01** | **Fidelidade à Cadeia Causal de Eventos** | Nenhum pacote (`CM_*` / `SM_*`) deve ser implementado isoladamente. Respeite o fluxo: `Captura (PCAP) -> Protocolo (Wire) -> Evento -> Estado (World/Entity) -> Sistema (Service) -> Resposta (Broadcast)`. |
| **02** | **Evidência Real Baseada em PCAPs e Cliente 5.0** | Toda implementação de protocolo ou mecânica deve basear-se nas capturas reais (`Ferramentas e Documentos/Client e Coletas/Wireshark - Oficial Classic 5.0/`) e nos dados extraídos (`Client 5.0 - Dados Extraidos/`). |
| **03** | **Proibição Absoluta de Bypass por Dados XML Faltantes** | É terminantemente proibido criar *fallbacks* ou valores mágicos no Java para suprir falta de templates. Corrija os XMLs via `parsersXML` e sincronize `Código Fonte - Emulador` e `Emulador - Produto Final`. |
| **04** | **Portabilidade Absoluta e Zero Caminhos Hardcoded** | É proibido fixar letras de unidade de disco (`C:\`, `D:\`, `E:\`) em qualquer arquivo (`.java`, `.rs`, `.cpp`, `.cs`, `.py`, `.bat`, `.json`, `.xml`, `.md`). Use sempre caminhos relativos e o runtime `java-deployment` integrado. |
| **05** | **Stack Java 25 LTS Pura (Zero Javolution)** | Utilize exclusivamente coleções e recursos nativos do Java 25 (`java.util`, `java.util.concurrent`, Virtual Threads). Nunca introduza dependências legadas como `javolution.*`. |
| **06** | **Sincronização Obrigatória com `Emulador - Produto Final`** | Toda modificação em `Código Fonte - Emulador`, no supervisor Rust ou em `version.dll` deve ser compilada e publicada em `Emulador - Produto Final` e `Patch final - Client 5.0`. |
| **07** | **Autoridade Exclusiva CryEngine Native-Path** | A navegação 3D utiliza exclusivamente `com.lostacademy.nativepath` (`*-path.dat` 0.5m com A* Zero-GC). Não reintroduza motores legados em tempo de execução. |
| **08** | **Padrão Estrito de Commits em Português** | Mensagens de commit devem ser escritas **estritamente em Português Brasil**, com **uma linha por alteração**, de forma concisa, técnica e sem emojis. |
| **09** | **Identificação do Usuário do Discord** | Inclua `Discord-User: @seu_usuario` na descrição do Pull Request para liberação de escrita no servidor oficial do Discord após o *merge*. |
| **10** | **Zero Segredos ou Arquivos Temporários de Execução** | Jamais versione `database.properties` com senhas pessoais de produção, diretórios `target/`, `logs/` ou caches `.WebView2/`. |

---

## 3. Padrão Obrigatório de Mensagem de Commit

> [!IMPORTANT]
> Conforme definido em [`CONTEXT.md`](./CONTEXT.md) e [`README.md`](./README.md), os commits devem estar estritamente em Português Brasil e descrever cada alteração relevante em uma linha individual e objetiva:

```gitcommit
Configura java-deployment com Java 25 LTS embarcado e referencia relativa no supervisor Rust
Move cache do WebView2 para AppData com limpeza e recriacao automatica a cada inicializacao
Adiciona documentacao padrao de governanca e seguranca na raiz do repositorio
```

---

## 4. Comparativo Rápido: O Que é Aceito vs. O Que é Rejeitado

| Submissão Aceitável (Aprovável) | Submissão Inaceitável (Fechamento Imediato) |
| :--- | :--- |
| Código Java 25 / Rust / C++ compilado e sincronizado com `Emulador - Produto Final`. | Alterar apenas o código-fonte sem atualizar os binários correspondentes ou enviar código que não compila. |
| Correção de dados estáticos diretamente nos XMLs via `parsersXML` a partir das extrações oficiais 5.0. | Criar `if (template == null)` com valores fictícios hardcoded no código Java. |
| Caminhos 100% relativos (`java-deployment/bin/java.exe`, `./libs/*`) e uso de `AppData` para cache temporário. | Inserir caminhos fixos como `C:\Program Files\Java\...` ou `D:\AION CLASSIC...` no código ou em arquivos `.json`. |
| Commits em Português Brasil no formato de uma linha técnica por alteração. | Commits em inglês, mensagens genéricas (`fix`, `update`) ou uso de emojis. |

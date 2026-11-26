# Aion Classic 5.0 — Lost Academy Group

<div align="center">

<img src="Ferramentas%20e%20Documentos/Banner/logo-512x512.png" alt="Aion Classic 5.0" width="180" height="180" />

</div>

<p align="center">
  <img src="https://img.shields.io/badge/Aion_Classic-5.0_EU-0ea5e9?style=for-the-badge" alt="Aion Classic 5.0" />
  <img src="https://img.shields.io/badge/Java-25_LTS-f97316?style=for-the-badge&logo=openjdk&logoColor=white" alt="Java 25 LTS" />
  <img src="https://img.shields.io/badge/Idioma_Padr%C3%A3o-Portugu%C3%AAs_(PT--BR)-10b981?style=for-the-badge" alt="Português Padrão" />
  <img src="https://img.shields.io/badge/Refer%C3%AAncia-GameForge_GSID_1-3b82f6?style=for-the-badge" alt="GameForge GSID 1" />
</p>

Emulador independente de **Aion Classic 5.0**, mantido em código aberto pela equipe **Lost Academy Group** para pesquisa, preservação técnica e reprodução fiel da versão oficial europeia publicada pela Gameforge.

> [!NOTE]
> Este repositório adota **Português (PT-BR)** como idioma padrão de desenvolvimento e documentação. Consulte [`CONTRIBUTING.md`](./CONTRIBUTING.md), [`SUPPORT.md`](./SUPPORT.md) e [`CONTEXT.md`](./CONTEXT.md) antes de utilizar ou contribuir.

---

## Estado Atual do Desenvolvimento

Os indicadores abaixo refletem o estágio atual conhecido do emulador em relação aos seus principais blocos funcionais:

| Frente de Desenvolvimento | Progresso Atual | Observações |
| :--- | :---: | :--- |
| **PvE** | **60% concluído** | Base de mundos, spawns, missões, drops e instâncias em evolução contínua rumo à paridade oficial. |
| **Full PvP** | **100% concluído** | Mecânicas e fluxos PvP operacionais dentro da arquitetura do servidor. |
| **Classe Bard** | **70% concluído** | Implementação avançada de habilidades e comportamentos da classe em refinamento progressivo. |

> [!WARNING]
> Esses percentuais representam **indicadores gerais do estado atual do projeto** e **não constituem garantia** de que todas as funcionalidades individuais estejam livres de bugs ou divergências.

---

## Objetivo Principal

O objetivo principal deste projeto é alcançar **100% de fidelidade PvE ao Aion Classic 5.0 Oficial EU, publicado pela Gameforge**.

O único servidor de referência adotado para o desenvolvimento Open Source é exclusivamente:

**GameServer 1 — GameForge (`GSID 1`)** (`Código Fonte - Emulador/game-server-gameforge`).

O emulador busca reproduzir com precisão o comportamento oficial da referência Gameforge GSID 1, abrangendo:

- Sistemas centrais de jogo e regras de servidor;
- Mecânicas de combate e atributos de personagens;
- Habilidades, cadeias e efeitos (`skills`);
- NPCs, diálogos e inteligência artificial;
- Quests e campanhas (`player_quests` / `questEngine`);
- Tabelas e regras de drops;
- Instâncias e eventos oficiais;
- Progressão de personagens, monstros e demais funcionalidades PvE.

Toda implementação deve ser **idêntica à referência oficial Gameforge**, sendo aceita alteração superior apenas quando se tratar de correção de bug comprovadamente existente no servidor oficial.

---

## Estrutura do Projeto e Módulos

```text
.
├── .github/                              # Templates de Issues/PRs, CODEOWNERS e pipelines CI
├── Código Fonte - Emulador/              # Projeto Maven Java 25 LTS
│   ├── commons/                          # Núcleo NIO, pools HikariCP, criptografia, GeoIP e utilitários
│   ├── login-server/                     # Servidor de autenticação (porta 2106) e gestão de contas
│   ├── chat-server/                      # Servidor de chat em tempo real (porta 10241)
│   ├── game-server-gameforge/            # GameServer 1 (GameForge GSID 1 | porta 7777) — ATIVO POR PADRÃO
│   ├── game-server-remake/               # Módulo auxiliar isolado (DESABILITADO por padrão no Open Source)
│   └── game-server-battleroyale/         # Módulo auxiliar isolado em perfil opcional (DESABILITADO por padrão)
├── Emulador - Produto Final/             # Distribuição pronta com configs locais de exemplo e libs sincronizadas
├── Ferramentas e Documentos/
│   ├── Auditorias e Relatórios/              # Relatórios e matrizes técnicas de auditoria
│   ├── Blender - Plugins/                    # Plugins de mapas e modelos 3D para Blender (pastas e .zip)
│   ├── Códigos bin64/                        # Módulos nativos C/C++ (incluindo version.dll e estudos RTTI)
│   ├── Geo and Nav Builder - Official Client/# Gerador nativo Java de Geodata (.geo/.mesh/.png) e NavMesh (.nav) sem Blender
│   ├── Opcodes Oficiais - Classic 5.0/        # Referências de opcodes do cliente oficial 5.0
│   ├── Patch final - Client 5.0/             # Patch do cliente e guia de versões em README.md
│   └── docs/                                 # Relatórios de auditoria, PRs, vulnerabilidades e validação final
```

Por padrão de distribuição e inicialização (`Emulador - Produto Final/Config/config.json`), **apenas o GameServer GameForge (`GSID 1`)** permanece habilitado em conjunto com `ChatServer` e `LoginServer`.

---

## Requisitos, Configuração Local e Compilação

### Pré-requisitos
- **Java Development Kit (JDK) 25 LTS** (compilação configurada com `<maven.compiler.release>25</maven.compiler.release>`).
- **Apache Maven 3.9+**.
- **MySQL 8.x** ou **MariaDB 10.x** em execução local.

### Configuração de Desenvolvimento Local (Exemplo Padrão)
Os arquivos `database.properties` e `Emulador - Produto Final/Config/config.json` utilizam exclusivamente valores de exemplo para ambiente local:

- **Host:** `127.0.0.1`
- **Porta:** `3306`
- **Usuário:** `LostAcademyGroup`
- **Senha:** `LostAcademyGroup`

> [!IMPORTANT]
> Essas credenciais destinam-se **unicamente ao ambiente local de exemplo e desenvolvimento** — nunca utilize usuário/senha padrão em ambientes expostos em rede ou produção.

### Compilação Maven
Defina `JAVA_HOME` apontando para o JDK 25 antes de executar o Maven:

```bash
mvn clean package --file "Código Fonte - Emulador/pom.xml"
```

Os artefatos principais gerados seguem a padronização `LostAcademyGroup`:
- `commons-LostAcademyGroup.jar`
- `login-server-LostAcademyGroup.jar`
- `chat-server-LostAcademyGroup.jar`
- `game-server-LostAcademyGroup.jar`

### Módulos OBRIGATÓRIOS para que o Cliente oficial funcione:
- A conexão do cliente ao emulador é feita de forma autônoma pela proxy `version.dll` localizada em [`Ferramentas e Documentos/Códigos bin64/Código Fonte - Version.dll/`](./Ferramentas%20e%20Documentos/C%C3%B3digos%20bin64/C%C3%B3digo%20Fonte%20-%20Version.dll/README.md).
- O pacote do Patch Client 5.0 e seu histórico de versões estão documentados em [`Ferramentas e Documentos/Patch final - Client 5.0/README.md`](./Ferramentas%20e%20Documentos/Patch%20final%20-%20Client%205.0/README.md).

Observação: Baixe o cliente oficial pelo site [https://gameforge.com/en-GB/play/aion_classic](https://gameforge.com/en-GB/play/aion_classic), depois acesse o Link do Patch acima e baixe-o também, depois COPIE TODAS PASTAS E ARQUIVOS PRA DENTRO DO CLIENT OFICIAL e SUBSTITUA.

Ainda está com problema ? Tente solicitar ajuda para algum modelo de IA (Por exemplo: Gemini, GPT ou Claude)

---

## Política de Pull Requests

**Somente serão aceitos Pull Requests que contribuam diretamente para o objetivo principal do projeto.**

Toda contribuição deve ser direcionada exclusivamente ao **GameServer 1 — GameForge (`GSID 1`)**, aos serviços compartilhados indispensáveis para sua operação (`commons`, `login-server`, `chat-server`, `version.dll`) ou à implementação de suporte multilíngue.

### Contribuições que NÃO serão aceitas
Pull Requests serão recusados caso:
- Alterem o escopo para outros GameServers;
- Introduzam ou mencionem referências ao **GSID 2**;
- Introduzam ou mencionem referências ao **GSID 3**;
- Modifiquem o comportamento de servidores secundários;
- Desviem da compatibilidade com o **GameForge GSID 1**;
- Alterem o idioma padrão do projeto para inglês;
- Introduzam funcionalidades incompatíveis com a proposta do projeto ou dependam de caminhos locais/credenciais privadas.

### Regra de Idioma e Multilínguas
- O projeto continuará sendo desenvolvido e documentado em **Português (PT-BR)**.
- **Única exceção referente a idioma:** serão aceitas contribuições relacionadas à implementação ou melhoria de um **sistema multilínguas**, permitindo ao usuário final escolher o idioma desejado sem alterar o idioma padrão existente.

Para detalhes completos sobre evidências exigidas, padrão de commits e critérios de revisão, leia [`CONTRIBUTING.md`](./CONTRIBUTING.md).

---

## Suporte e Governança

Este projeto é distribuído no modelo **AS-IS (como está)**, conforme os termos em [`LICENSE`](./LICENSE) e [`SUPPORT.md`](./SUPPORT.md). **Não há prestação de suporte técnico individual** para instalação, configuração de MySQL, obtenção de cliente ou ajustes personalizados.

Consulte também:
- [`CONTEXT.md`](./CONTEXT.md) — arquitetura técnica e fluxos principais;
- [`SECURITY.md`](./SECURITY.md) — modelo de segurança e divulgação responsável;
- [`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md) — código de conduta da comunidade.

---

## Website Aion Remake

**Website:** [https://aionlostacademy.com/](https://aionlostacademy.com/)

O **Aion Remake** é um projeto independente em desenvolvimento pela equipe **Lost Academy Group**.

Ele representa a junção de **Aion Retail** com **Aion Classic 5.0**, tendo recebido modificações e reestruturações para se tornar uma nova experiência de jogo, que será disponibilizada futuramente para que a comunidade possa conhecer e jogar.

> [!NOTE]
> O **Aion Remake é um projeto separado** deste repositório Open Source (**Aion Classic 5.0 — Lost Academy Group**). Pull Requests neste repositório devem permanecer exclusivamente alinhados ao objetivo oficial PvE do **GameServer 1 (GameForge GSID 1)**.

---


## Origem e Créditos

**POC Variant:** [https://github.com/acottis/aion](https://github.com/acottis/aion)
**Beyond Aion:** [https://github.com/beyond-aion/aion-server](https://github.com/beyond-aion/aion-server)

Este emulador possui origem técnica direta no código **Retail 4.8 da Beyond Aion**, conforme o fluxo de evolução abaixo:

```text
Versão POC em Rust
↓
Primeiro emulador em Rust funcional
↓
Emulador estável em Rust na 4.5 EU GameForge
↓
Atualização do Emulador em Rust para versão 5.0 EU GameForge
↓
Estabilização de OPCODES e OFFSETS, marcando emulador Rust totalmente compatível com o CLIENT 5.0 Oficial
↓ 
Portabilidade completa do emulador RUST 5.0 para dentro do JAVA Retail 4.8 da Beyond Aion
↓
Modificação pesada e reestruturação
↓
Aion Classic 5.0 — Lost Academy Group (Java 25 LTS)
```

O projeto nasceu a partir da POC escrita em Rust, foi onde nós adaptamos e corrigimos para ficar compatível inicialmente com a versão 4.5 Classic, conseguimos desenvolver toda base inicial de login, criação de personagens, entrar no jogo e conseguir executar funções básicas, em sequência a GameForge atualizou para 5.0, foi quando nós também atualizamos nosso emulador Rust para 5.0, realizamos toda adaptação necessária, depois nós baixamos o emulador base Retail 4.8 da Beyond Aion e portamos o emulador Rust para dentro dele, realizando modificações profundas, adaptações de protocolo e reestruturação estrutural para operar como o atual **Aion Classic 5.0**. Por esse motivo, diversos códigos, estruturas, definições e comportamentos ainda guardam herança da implementação Retail 4.8.

A identificação e a correção dessas heranças devem acontecer **individualmente, código por código, sem substituições indiscriminadas**.

### Créditos e Avisos Legais
- Créditos preservados aos autores originais da base **Rust POC - Acottis** e **Beyond Aion** e colaboradores da comunidade de emulação Aion (`LICENSE`).
- **Desenvolvimento Aion Classic 5.0:** Lost Academy Group.
- **Aviso de não afiliação:** Este projeto Open Source independente **não possui qualquer afiliação, endosso ou vínculo oficial com a Gameforge 4D GmbH, NCSOFT Corporation ou Beyond Aion**. Todas as marcas pertencem aos seus respectivos proprietários.

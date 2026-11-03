# Guia de Suporte, Diagnóstico e Escopo — AION CLASSIC 5.0 EMULADOR

<p align="center">
  <a href="./SUPPORT.md"><img src="https://img.shields.io/badge/Idioma-Portugu%C3%AAs_Brasil_(Padr%C3%A3o)-10b981?style=for-the-badge&logo=markdown&logoColor=white" alt="PT-BR Padrão" /></a>
  <a href="./README.md"><img src="https://img.shields.io/badge/Documenta%C3%A7%C3%A3o-README.md-3b82f6?style=for-the-badge&logo=markdown&logoColor=white" alt="README.md" /></a>
  <a href="./CONTEXT.md"><img src="https://img.shields.io/badge/Arquitetura-CONTEXT.md-0ea5e9?style=for-the-badge&logo=markdown&logoColor=white" alt="CONTEXT.md" /></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Suporte_T%C3%A9cnico-NENHUM_SUPORTE_CONCEDIDO-dc2626?style=flat-square" alt="Nenhum Suporte" />
  <img src="https://img.shields.io/badge/Fornecimento-COMO_%C3%89_(AS--IS)-f59e0b?style=flat-square" alt="Como É" />
  <img src="https://img.shields.io/badge/Finalidade-Pesquisa_e_Preserva%C3%A7%C3%A3o-10b981?style=flat-square" alt="Pesquisa" />
  <a href="https://discord.gg/Sjdrsg3gcb"><img src="https://img.shields.io/badge/Discord-Acesso_Restrito_por_PR-5865F2?style=flat-square&logo=discord&logoColor=white" alt="Discord" /></a>
</p>

> [!CAUTION]
> # DECLARAÇÃO OFICIAL: NENHUM SUPORTE OU AJUDA TÉCNICA SERÁ CONCEDIDA
> O **Aion Classic 5.0 — Emulador Oficial** é disponibilizado estritamente **"COMO É" (*AS-IS*)**, exclusivamente para **testes, preservação histórica e estudos de engenharia de software e sistemas distribuídos**.  
> **Este repositório NÃO é um produto comercial e NÃO oferece suporte técnico para instalação, operação ou configuração de ambientes de terceiros.**

---

## 1. Lista Rápida de Diagnóstico

Antes de submeter um relatório de falha (*issue*), execute o seguinte roteiro de verificação:

1. **Verificar a Execução do Supervisor Nativo em Rust (`Aion Classic - EMULADOR.exe`):**
   - Certifique-se de que o supervisor está em execução na pasta `Emulador - Produto Final\`.
   - O painel administrativo opera em `http://127.0.0.1:18080/`.
2. **Auditar a Sequência Obrigatória de Boot:**
   - O `ChatServer` (porta `10241`) deve estar 100% online antes do LoginServer.
   - O `LoginServer` (porta `2106`) deve estar online antes de qualquer GameServer.
   - Cada `GameServer` ativo (`GameForge` na `7777`, `Remake` na `7778`, `BattleRoyale` na `7779`) deve estar conectado ao LoginServer e ChatServer.
3. **Verificar os Schemas do Banco de Dados no MySQL:**
   - Certifique-se de que o MySQL está acessível e que os schemas segregados existem:
     - `aionclassic_ls` (LoginServer)
     - `aionclassic_cs` (ChatServer)
     - `aionclassic_gs` (GameServer GameForge)
     - `aionclassic_gs2` (GameServer Remake)
     - `aionclassic_gs3` (GameServer BattleRoyale)
4. **Validar a Injeção do Módulo no Cliente (`version.dll`):**
   - Certifique-se de que a `version.dll` mais recente foi compilada e colocada em `D:\GameForge\aionclassic\bin64\version.dll`.
   - Execute o cliente através de `Start x64 - INGLÊS.bat` ou `Start x64 - PORTUGUÊS BRASIL.bat`.

---

## 2. Problemas Comuns e Soluções

### P1: Mensagem "Não tem servidor de autenticação disponível" no cliente de jogo
* **Causa:** A `version.dll` do cliente não está instalada ou está desatualizada, ou o LoginServer não está escutando na porta `127.0.0.1:2106`.
* **Solução:**
  1. Compile a `version.dll` executando `Ferramentas e Documentos/Códigos bin64/Código Fonte - Version.dll/build.bat`. O script copia automaticamente a DLL compilada para `D:\GameForge\aionclassic\bin64\version.dll`.
  2. Verifique no painel do Supervisor se o card do **Login Server** exibe status `ONLINE`.

### P2: Conexão bloqueada imediatamente no socket TCP pelo Firewall GeoIP
* **Causa:** O IP do cliente de jogo não pertence a um dos países liberados em `geo_firewall.properties` (`geo.firewall.allowed_countries`).
* **Solução:**
  1. No arquivo `Config/network/geo_firewall.properties` do servidor correspondente, adicione o código do país à lista de permissões ou adicione o IP específico em `geo.firewall.manual_whitelist_ips`.

### P3: Falha ao carregar ou editar arquivos no Gerenciador de Propriedades (.properties)
* **Causa:** Tentativa de editar parâmetros com caminhos inválidos ou ausência de permissão de escrita.
* **Solução:** O Gerenciador de Propriedades do Supervisor Rust cria automaticamente cópias de segurança com extensão `.bak` antes de qualquer gravação. Caso ocorra erro de sintaxe, o arquivo original `.bak` pode ser restaurado.

### P4: O GameServer não aparece na lista de seleção de reinos do cliente
* **Causa:** O GameServer não conseguiu registrar seu GSID no LoginServer, ou o identificador não consta cadastrado na tabela `aionclassic_ls.gameservers`.
* **Solução:** O Supervisor nativo registra automaticamente os GSIDs configurados (`1` para GameForge, `2` para Remake, `3` para BattleRoyale). Certifique-se de que a senha do GameServer em `network.properties` corresponde à cadastrada na tabela `gameservers`.

### P5: Onde ficam armazenados os dados de personagens e progresso de cada modalidade?
* **Solução:** Cada servidor opera com banco de dados **estritamente isolado**:
  - Personagens do servidor GameForge: schema `aionclassic_gs`
  - Personagens do servidor Remake: schema `aionclassic_gs2`
  - Personagens do servidor BattleRoyale: schema `aionclassic_gs3`
  Os dados podem ser inspecionados diretamente na aba **Banco de Dados** (Database Studio integrado) do Supervisor nativo.

---

## 3. O Que NÃO Recebe Suporte (Sem Exceções)

Não abra chamados (*Issues*), tópicos em discussões ou mensagens solicitando ajuda sobre:

1. **Instalação e Configuração de Banco de Dados MySQL:** Dúvidas sobre como instalar MySQL 8.x / MariaDB, resetar senhas de root ou configurar redes locais.
2. **Download do Cliente de Jogo Oficial:** Não hospedamos nem distribuímos instaladores completos do cliente Aion Classic Gameforge. O projeto segue estritamente a filosofia *Bring Your Own Client* (BYOC).
3. **Erros de Sistema Operacional de Terceiros:** Falhas causadas por antivírus bloqueando hooks de DLL, falta de bibliotecas redistribuíveis do Visual C++ ou sistemas desatualizados.
4. **Demandas Comerciais ou Criação de Servidores Privados:** O emulador é um projeto estritamente educacional de preservação de software e engenharia reversa.

---

## 4. Regra de Desbloqueio da Comunidade no Discord

> [!IMPORTANT]
> O servidor oficial no Discord (**[https://discord.gg/Sjdrsg3gcb](https://discord.gg/Sjdrsg3gcb)**) **não é um canal de suporte técnico**.
> Todos os canais de bate-papo permanecem em modo somente leitura até que o desenvolvedor tenha pelo menos **um Pull Request técnico real aprovado (*merged*)** neste repositório, contendo `Discord-User: @seu_usuario` na descrição e cumprindo integralmente as exigências de testes e evidências visuais descritas em [`CONTRIBUTING.md`](./CONTRIBUTING.md).

---

## 5. Como Abrir um Relatório de Bug Válido

Caso encontre uma falha de emulação reproduzível:
1. Certifique-se de testar e comparar o comportamento contra o **servidor oficial Aion Classic Gameforge**.
2. Colete evidências no **Ghidra** (análise estática da lógica do cliente) e no **Wireshark** (captura PCAP oficial dos pacotes).
3. Abra um relatório através do [Template de Relato de Bug](.github/ISSUE_TEMPLATE/bug_report.yml), especificando obrigatoriamente **qual GameServer foi afetado** e anexando capturas de tela demonstrando o erro.

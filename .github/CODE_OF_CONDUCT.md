# Código de Conduta Contributor Covenant — AION CLASSIC 5.0 EMULADOR

## 1. Nosso Compromisso

Nós, como membros, colaboradores e mantenedores, assumimos o compromisso de tornar a participação na comunidade do **Aion Classic 5.0 — Emulador Oficial** uma experiência livre de assédio para todos, independentemente de idade, porte físico, deficiência visível ou invisível, etnia, características sexuais, identidade e expressão de gênero, nível de experiência, educação, condição socioeconômica, nacionalidade, aparência pessoal, raça, cor, religião ou orientação sexual.

Comprometemo-nos a agir e interagir de maneiras que contribuam para uma comunidade técnica aberta, acolhedora, diversa, inclusiva e com rigor científico incomparável, dedicada à **preservação histórica de sistemas distribuídos e à engenharia reversa limpa** de protocolos e binários oficiais do Aion Classic 5.0 Gameforge.

---

## 2. Nossos Padrões

Exemplos de comportamentos que contribuem para um ambiente positivo e de alto nível em nossa comunidade incluem:

* Demonstrar empatia e cordialidade técnica com outras pessoas.
* Respeitar opiniões, pontos de vista e discussões empíricas de engenharia.
* Oferecer e aceitar retornos técnicos construtivos baseados em evidências concretas.
* Manter padrões rigorosos de engenharia reversa:
  - **Fidelidade visual, mecânica e de protocolo 1:1** com o cliente e servidor oficial Aion Classic Gameforge.
  - **Validação obrigatória com ferramentas profissionais**: Descompilação e análise estática via **Ghidra** e captura e análise de tráfego de pacotes via **Wireshark**.
  - **Respeito absoluto ao isolamento dos GameServers**: Cada GameServer (`game-server-gameforge`, `game-server-remake`, `game-server-battleroyale`) é independente, com regras e mecânicas isoladas. É inaceitável aplicar alterações ou ler servidores indiscriminadamente.
  - **Zero dados fictícios (Zero Mock Data)**: NUNCA criar *fallbacks* estáticos ou *bypasses* em código Java para simular templates ausentes; a correção canônica é sempre nos dados XML oficiais.
  - **Portabilidade pura**: Zero caminhos fixos de disco (`C:\`, `D:\`) e padronização completa em Java 25 LTS e Rust.
* Focar no que é melhor para o projeto de preservação histórica, estabilidade técnica e para a comunidade.

Exemplos de comportamentos inaceitáveis incluem:

* Uso de linguagem ou imagens de conteúdo depreciativo, assédio, investidas inconvenientes ou comportamento predatório.
* Comentários insultuosos, ataques pessoais, discussões políticas e provocações destrutivas (*trolling*).
* Publicação de informações privadas de terceiros (*doxxing*), como endereços físicos ou eletrônicos, sem consentimento explícito.
* Solicitação ou oferecimento de downloads de clientes comerciais completos ou instaladores proprietários protegidos por direitos autorais (tolerância zero à pirataria).
* Tentativa de monetização, comércio de pacotes de dados, exploração comercial ou venda de acessos ao emulador.
* Envio de Pull Requests sem testes práticos, sem evidências oficiais, sem imagens comprobatórias, ou misturando múltiplos sistemas ou múltiplos GameServers em uma única submissão.
* Introdução intencional de código malicioso, portas dos fundos (*backdoors*), ganchos de trapaça (*cheats*) ou desvios de protocolo na base de código.

---

## 3. Responsabilidades de Aplicação

Os mantenedores do projeto são responsáveis por esclarecer e fazer cumprir nossos padrões de comportamento aceitável e tomarão ações corretivas apropriadas, justas e imediatas em resposta a qualquer comportamento que considerem inadequado, ameaçador, ofensivo ou tecnicamente danoso ao repositório.

Os mantenedores têm o direito e a responsabilidade de remover, editar ou rejeitar comentários, commits, código, edições de wiki, issues e Pull Requests que não estejam alinhados a este Código de Conduta ou às regras de engenharia descritas em [`CONTRIBUTING.md`](../CONTRIBUTING.md), comunicando os motivos das decisões técnicas quando apropriado.

---

## 4. Escopo

Este Código de Conduta aplica-se a todos os espaços do projeto, incluindo GitHub Issues, Pull Requests, Discussions, Revisões de Código, arquivos de documentação, bem como no servidor oficial do Discord e eventos em que um indivíduo esteja representando oficialmente o projeto em espaços públicos.

---

## 5. Aplicação e Denúncias

Casos de comportamento abusivo, assédio ou qualquer conduta inaceitável podem ser reportados diretamente ao mantenedor principal do projeto (`@kamidaki`) através dos canais de contato oficiais do repositório no GitHub. Todas as reclamações serão analisadas e investigadas com prontidão, imparcialidade e sigilo.

---

## 6. Atribuição

Este Código de Conduta é adaptado do [Contributor Covenant](https://www.contributor-covenant.org/pt-br/version/2/1/code_of_conduct/), versão 2.1, complementado com os requisitos técnicos específicos de engenharia reversa e isolamento arquitetural do projeto Aion Classic 5.0.

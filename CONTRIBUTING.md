# Guia de Contribuição e Diretrizes — Aion Classic 5.0 (Lost Academy Group)

<p align="center">
  <a href="./CONTRIBUTING.md"><img src="https://img.shields.io/badge/Idioma-Portugu%C3%AAs_(Padr%C3%A3o)-10b981?style=for-the-badge" alt="Português Padrão" /></a>
  <a href="./CONTEXT.md"><img src="https://img.shields.io/badge/Arquitetura-CONTEXT.md-3b82f6?style=for-the-badge" alt="CONTEXT.md" /></a>
  <a href="./SECURITY.md"><img src="https://img.shields.io/badge/Seguran%C3%A7a-SECURITY.md-ef4444?style=for-the-badge" alt="SECURITY.md" /></a>
</p>

Quer contribuir corrigindo uma palavra no `README.md`, atualizando guias, melhorando os plugins do Blender ou evoluindo o núcleo Java do emulador? Este repositório utiliza **regras proporcionais ao que foi alterado**: ninguém precisa rodar build Java 25 ou apresentar capturas binárias para enviar uma melhoria de documentação.

---

## 1. Via Rápida vs. Validação Completa

| Tipo de Alteração | O que é exigido | O que é dispensado | Bot & Aprovação |
| :--- | :--- | :--- | :--- |
| **Documentação (`docs-only`)**<br>Arquivos `.md`, `.txt`, imagens de docs | Apenas conteúdo limpo (sem tokens/caminhos locais) e sintaxe saudável | Build Maven/JDK 25, Ghidra/Wireshark e formato rígido de título | Recebe `documentation` + `docs-only`, título padronizado se precisar e **aprovação automática** |
| **Ferramentas / Blender / CI**<br>Scripts Python, `.yml`, `Geo & Nav Builder` | Sintaxe válida (`.py`, `.json`, `.yml`, `.xml`) e zero dados pessoais vazados | Compilação Maven/JDK 25 | Recebe `area/*` + `size/*` e **aprovação automática** se os checks passarem |
| **Backend Java**<br>Alterações em `Código Fonte - Emulador/` | Título Conventional Commit claro, build Maven JDK 25 verde e escopo GSID 1 | — | Só entra em **aprovação automática** após o `Build e Pacote GameForge GSID 1 (Java 25 LTS)` concluir com sucesso |

> [!IMPORTANT]
> **Diretrizes Essenciais do Projeto:**
> 1. **Escopo do Backend:** Contribuições no servidor Java devem focar no **GameServer 1 — GameForge (`GSID 1`)** (`game-server-gameforge`, `commons`, `login-server`, `chat-server`), mantendo intactos os módulos auxiliares desabilitados (`game-server-remake` e `game-server-battleroyale`).
> 2. **Idioma Padrão Português (PT-BR):** Não remova ou substitua o idioma padrão do projeto para inglês. Adições **multilíngues** com seleção de idioma são bem-vindas.
> 3. **Higienização Obrigatória:** Nunca inclua credenciais reais, tokens, IPs privados ou caminhos fixos da sua máquina (`C:\Users\<seu_usuario>\...`). Em templates de configuração local, utilize sempre exemplos neutros (`127.0.0.1`, porta `3306`, usuário `LostAcademyGroup`, senha `LostAcademyGroup`).

---

## 2. Automação do Repositório (Bot Revisor, Labels e `/autofix`)

Todos os Pull Requests contam com uma suíte automática composta por três fluxos integrados:

1. **Classificação e Labels Automáticas:**
   - O bot aplica automaticamente labels por **tipo** (`documentation`, `docs-only`, `kind/bug`, `kind/feature`, `kind/perf`, `kind/security`, `kind/refactor`, `kind/deps`), **área** (`area/gameforge`, `area/blender-plugins`, `area/geo-nav`, `area/version-dll`, `area/tools`, `area/ci`, etc.) e **tamanho** (`size/XS` a `size/XL`), preservando qualquer label manual adicionada pela equipe.
2. **Revisão e Aprovação Automática:**
   - Ao final das verificações (`Revisão Automática e Qualidade do PR`, `Validar Titulo do PR / Commit` e, quando aplicável, `Build e Pacote GameForge GSID 1`), o bot publica um comentário único consolidado com o diagnóstico, adiciona `bot/approved` e envia `APPROVE` oficial quando tudo está saudável (ou `REQUEST_CHANGES` + `bot/needs-attention` indicando arquivo e linha exatos caso exista erro).
   - Para PRs puramente de documentação (`docs-only`) abertos pela interface web do GitHub com títulos genéricos (como `Update README.md`), o próprio bot padroniza o título automaticamente (`docs: atualizar README.md`) em vez de bloquear a contribuição.
3. **Comando `/autofix` no PR:**
   - Se o bot sinalizar pequenos ajustes mecânicos (quebra `CRLF -> LF` em workflows, ausência de quebra de linha no fim do arquivo ou espaços sobrando ao fim de linhas de código), basta comentar `/autofix` no Pull Request (válido para branches do próprio repositório) para o bot corrigir e enviar o commit automaticamente.

---

## 3. Padrão Recomendado de Títulos e Commits

Para alterações de código, utilize o formato Conventional Commits com mensagens objetivas em Português (o escopo entre parênteses é opcional):

```text
fix(gameforge): corrigir dialogo e recompensa de quest em pandaemonium
feat(l10n): adicionar selecao de idioma nas mensagens do servidor
perf(blender): otimizar carregamento linear do importador de mapas
docs: corrigir link e instrucoes de uso no README.md
```

---

## 4. Validação Local (Quando Alterar Código Java)

Se você editou arquivos dentro de `Código Fonte - Emulador/`, valide localmente com JDK 25 antes do envio:

```bash
mvn clean package --file "Código Fonte - Emulador/pom.xml"
```

---

## 5. Formulário de Pull Request

Ao abrir um Pull Request, utilize o formulário [`.github/pull_request_template.md`](.github/pull_request_template.md) marcando apenas os itens aplicáveis ao tipo da sua mudança (para `docs-only`, os itens técnicos de Java são dispensados).

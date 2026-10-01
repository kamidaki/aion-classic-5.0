# Aion Classic 5.0 — Tradução e Localização Português do Brasil (PT-BR)

Bem-vindo ao repositório de dados de localização do **Aion Classic 5.0** para Português do Brasil.

Este projeto tem como meta a entrega de uma tradução de padrão profissional, imersiva, consistente e 100% contextualizada para o ecossistema Lost Academy.

---

## 1. Escopo e Diretórios do Projeto

* **Diretório Alvo (Tradução PT-BR)**:
  `D:\AION CLASSIC 5.0 - EMULADOR\Ferramentas e Documentos\Client e Coletas\Tradução - Português Brasil`
* **Diretório de Referência Contextual (Inglês Oficial)**:
  `D:\AION CLASSIC 5.0 - EMULADOR\Ferramentas e Documentos\Client e Coletas\Client 5.0 - Dados Extraidos\Idioma em Inglês`
* **Destino de Empacotamento para o Cliente**:
  `D:\AION CLASSIC 5.0 - EMULADOR\Ferramentas e Documentos\Patch final - Client 5.0\l10n\BRA\Data\data.pak`

---

## 2. Estrutura de Arquivos

| Pasta | Descrição | Formato Principal | Quantidade |
| :--- | :--- | :--- | :--- |
| `strings/` | Tabelas centrais de strings (UI, itens, quests, skills, mensagens, monstros, NPCs) | XML (UTF-16LE com BOM) | 26 arquivos |
| `cutscene/` | Legendas sincronizadas de animações e cinemáticas | XML (UTF-16LE com BOM) | 344 arquivos |
| `help/` | Manuais de ajuda in-game, comandos de chat, macros e tutoriais | HTML/XML (UTF-16LE) | 15 arquivos |
| `ui/` | Layouts XML de telas, janelas, botões e diálogos da interface | XML (UTF-16LE) | 494 arquivos |
| `dialogs/` | Roteiros e ramificações de diálogos de NPCs e missões | HTML codificado com XOR 0x81 | 11.597 arquivos |
| `housing/` | Interfaces e tabelas do sistema residencial | XML (UTF-16LE) | 6 arquivos |
| `Sounds/` | Mapeamento de efeitos sonoros e falas | XML (UTF-16LE) | 2 arquivos |
| `fonts/` | Tipografias do cliente e configurações de renderização de fontes | TTF / XML | 14 arquivos |

---

## 3. Requisitos Críticos de Formato e Codificação

1. **Codificação Estrita**:
   * Todos os arquivos de texto/XML devem ser codificados em **UTF-16 Little Endian com BOM (`\xFF\xFE`)**.
   * Não utilizar UTF-8 sem BOM ou CP1252 nos arquivos XML do cliente, sob risco de quebra de carregamento ou corrupção de acentos.
2. **Integridade de Estrutura XML**:
   * Não modificar tags delimitadoras: `<strings>`, `<string>`, `<id>`, `<name>`, `<body>`, `<CutSceneText>`, `<Text>`.
   * Manter os valores de `<id>` e `<name>` rigorosamente intactos.
3. **Preservação de Tokens e Placeholders**:
   * Argumentos de formatação dinâmica (`%0`, `%1`, `%d`, `%s`, `%num0`, `%addr0`, etc.) nunca devem ser alterados, removidos ou traduzidos.
   * Tags de estilo e formatação (`[font:...]`, `<font color="...">`, `\n`) devem permanecer válidas e bem fechadas.
4. **Política Rigorosa de URLs**:
   * 100% dos links da comunidade, loja, suporte e registro devem apontar exclusivamente para:
     * `https://aionlostacademy.com`
     * `https://www.aionlostacademy.com`
   * Todos os links para domínios legados (`gameforge.com`, `plaync.com`, etc.) e links corrompidos por dicionário são estritamente proibidos.

---

## 4. Fluxo de Trabalho e Metodologia de Qualidade

O ciclo de vida de localização segue o protocolo rigoroso:

$$\text{READ} \longrightarrow \text{INVENTORY} \longrightarrow \text{AUDIT} \longrightarrow \text{COMPARE} \longrightarrow \text{CLASSIFY} \longrightarrow \text{PLAN} \longrightarrow \text{TRANSLATE} \longrightarrow \text{VALIDATE} \longrightarrow \text{URL AUDIT} \longrightarrow \text{REGRESSION}$$

### Portões de Aceitação (Gates) — Status Final
* **GATE 1**: Concluído — Documentação técnica criada (`context.md` e `readme.md`).
* **GATE 2**: Concluído — Inventário completo de 100% dos arquivos com métricas quantitativas (12.498 arquivos).
* **GATE 3**: Concluído — Confronto contextual linha a linha contra a fonte autoritativa em inglês.
* **GATE 4**: Concluído — Execução da tradução com terminologia canônica de MMORPG em Português do Brasil.
* **GATE 5**: Concluído — Verificação estrutural e sintática de 100% dos 867 arquivos XML (0 erros de parse).
* **GATE 6**: Concluído — Auditoria e migração de 100% das URLs para o ecossistema `aionlostacademy.com`.
* **GATE 7**: Concluído — Varredura de regressão completa (0 artefatos de dicionário restantes).
* **GATE 8**: Concluído — Revisão linguística, ortográfica e restauração total de variáveis (%0, %num0).
* **GATE 9**: Concluído — Pacote `data.pak` compilado (84,8 MB) e Relatório Comparativo Final emitido.

---

## 5. Procedimento de Empacotamento e Instalação

O pacote final do cliente foi compilado com sucesso a partir dos arquivos auditados:
1. Os arquivos de `cutscene`, `dialogs`, `fonts`, `help`, `housing`, `Sounds`, `strings` e `ui` foram compactados no pacote nativo do cliente.
2. O arquivo gerado foi instalado em:
   `D:\AION CLASSIC 5.0 - EMULADOR\Ferramentas e Documentos\Patch final - Client 5.0\l10n\BRA\Data\data.pak`
3. O cliente pode ser executado diretamente através do iniciador oficial:
   `Start x64 - PORTUGUÊS BRASIL.bat` (que utiliza a flag de idioma oficial `-lang:BRA`).


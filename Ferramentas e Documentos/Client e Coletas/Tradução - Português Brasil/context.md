# Contexto Técnico da Localização: Aion Classic 5.0 (Português Brasil)

## 1. Visão Geral e Arquitetura do Cliente
O cliente do Aion Classic 5.0 utiliza uma arquitetura baseada na CryEngine modificada pela NCSoft. Os recursos textuais e de interface (UI) residem primariamente nos arquivos empacotados em arquivos `.pak` (contêineres ZIP modificados com inversão de assinaturas por XOR 0xFF e cabeçalhos deflate ofuscados com tabela de 1056 bytes).

Na execução do cliente (por exemplo via `Start x64 - PORTUGUÊS BRASIL.bat`), o binário de 64 bits (`bin64\Aion.bin`) recebe o parâmetro de inicialização `-lang:BRA`. Esse parâmetro instrui o cliente a carregar o pacote de idioma localizado em:
`l10n\BRA\Data\data.pak`

Este diretório de trabalho (`Tradução - Português Brasil`) contém todos os arquivos desempacotados e estruturados que compõem o pacote de localização em Português do Brasil.

---

## 2. Estrutura de Diretórios e Tipos de Arquivos

A árvore de diretórios da tradução brasileira é composta pelos seguintes módulos:

```
Tradução - Português Brasil/
├── strings/              # Tabelas de strings principais do jogo (26 arquivos)
│   ├── client_strings_bm.xml
│   ├── client_strings_bmrestrict.xml
│   ├── client_strings_dic_etc.xml
│   ├── client_strings_dic_item.xml
│   ├── client_strings_dic_monster.xml
│   ├── client_strings_dic_people.xml
│   ├── client_strings_dic_place.xml
│   ├── client_strings_etc.xml
│   ├── client_strings_funcpet.xml
│   ├── client_strings_gossip.xml
│   ├── client_strings_item.xml
│   ├── client_strings_item2.xml
│   ├── client_strings_level.xml
│   ├── client_strings_monster.xml
│   ├── client_strings_msg.xml
│   ├── client_strings_npc.xml
│   ├── client_strings_quest.xml
│   ├── client_strings_skill.xml
│   ├── client_strings_ui.xml
│   ├── client_strings_url.xml
│   ├── stringtable_dialog.xml
│   ├── stringtable_gg.xml
│   ├── stringtable_tip.xml
│   ├── error/clienterrormsgs.xml
│   ├── aionfilterchat.txt.ready
│   └── banned.txt
├── cutscene/             # Legendas de cutscenes cinematográficas (344 arquivos XML)
│   └── cs_*.xml
├── help/                 # Sistema de ajuda, tutoriais e comandos de chat (15 arquivos)
│   ├── chatcommand.html
│   ├── macro.html
│   ├── tutorial.html
│   ├── tutorial.xml
│   ├── tutorial_events.xml
│   └── petition_*.xml
├── ui/                   # Definições de layouts e janelas da interface (494 arquivos)
│   ├── Credit*.html
│   ├── game/             # Layouts das janelas de diálogo (*_dialog.xml)
│   ├── game_hud_s1/      # HUD variante Season 1
│   ├── game_hud_s2/      # HUD variante Season 2
│   ├── game_hud_s3/      # HUD variante Season 3
│   └── preload/          # Telas de carregamento e preload de UI
├── dialogs/              # Diálogos completos de quests e NPCs (11.597 arquivos)
├── housing/              # Textos do sistema residencial e caixas de correio (6 arquivos XML)
├── Sounds/               # Eventos sonoros e áudios de itens (2 arquivos XML)
└── fonts/                # Fontes TrueType (TTF) e mapeamento de shaders de fonte (14 arquivos)
```

---

## 3. Especificação de Formato e Codificação (Encoding)

### 3.1 Codificação Obrigatória
* **Encoding**: `UTF-16LE` (Little Endian) com BOM (`\xFF\xFE`).
* **Terminador de Linha**: Padrão Windows `\r\n` (CRLF).
* **XML Header**: `<?xml version="1.0" encoding="utf-16"?>`.
* Qualquer tentativa de salvar como UTF-8 ou CP1252 quebra a leitura pelo cliente do Aion Classic ou gera corrupção de caracteres acentuados.

### 3.2 Formato das Tabelas de Strings (`strings/*.xml`)
Estrutura canônica de cada arquivo de strings:
```xml
<?xml version="1.0" encoding="utf-16"?>
<strings>
  <string>
    <id>123456</id>
    <name>STR_IDENTIFICADOR_SIMBOLICO</name>
    <body>Texto traduzido em Português do Brasil</body>
  </string>
</strings>
```
* `<id>`: Identificador numérico inteiro positivo único. **Imutável**.
* `<name>`: Nome de símbolo interno do cliente / scripts (ex: `STR_ITEM_...`, `STR_SKILL_...`, `STR_QUEST_...`, `STR_MSG_...`). **Imutável**.
* `<body>`: O conteúdo textual exibido ao jogador. **Alvo de tradução e revisão**.
* Tags adicionais (como `<display_type>`, `<__review__>`): Devem ser preservadas rigorosamente quando existirem.

### 3.3 Formato das Cutscenes (`cutscene/cs_*.xml`)
Estrutura canônica:
```xml
<?xml version="1.0" encoding="utf-16"?>
<CutSceneText>
  <Text label="P01">Legenda exibida durante o vídeo/cutscene.</Text>
  <Text label="P02">Segunda fala da cena cinematográfica.</Text>
</CutSceneText>
```
* O atributo `label` (ex: `P01`, `P02`) sincroniza o texto com o áudio/timeline da cena. **Imutável**.

### 3.4 Formato do Sistema de Ajuda (`help/*.html`, `help/*.xml`)
Mesmo com extensão `.html`, os arquivos de ajuda do Aion utilizam uma estrutura encapsulada em XML (`<HtmlPages><HtmlPage name="...">...`) contendo XHTML interno com atributos como `paraspace="7"`, tags `<font color="...">`, links `<a href="...">` e listas.
* Codificação: `UTF-16LE` com declaração `<?xml version="1.0" encoding="UTF-16" ?>`.

---

## 4. Regras Rígidas de Placeholders, Tags e Variáveis

O mecanismo de formatação de mensagens do Aion injeta valores dinâmicos de runtime (nomes de personagens, valores de dano, itens, locais, contadores de tempo). A quebra de qualquer token impede a exibição correta e pode causar crash do cliente.

### 4.1 Lista de Tokens Protegidos (NUNCA TRADUZIR OU ALTERAR)
1. **Argumentos Posicionais Simples**:
   * `%0`, `%1`, `%2`, `%3`, `%4`, etc.
   * `%0d`, `%0s`, `%0m`, `%0th`
   * `%d`, `%s`, `%f`
2. **Identificadores Numéricos e Espaciais**:
   * `%num0`, `%num1`, `%num2`, `%num3`
   * `%num0sp`
   * `%addr0`
   * `%qunaname`
3. **Data e Tempo**:
   * `%DATETIME0`, `%DATETIME1`
   * `%TIME_WEEKDAY0`, `%TIME_HOUR3`
   * `%DURATIONDAY0`, `%DURATIONTIME1`
4. **Localização e Mundo**:
   * `%SUBZONE2`, `%WORLDNAME1`
5. **Entidades e Atores de Combate**:
   * `[%Skillcaster]`, `[%SkillCaster]`
   * `[%Target]`, `[%gchar:...]`
6. **Controles de Estilo e Cores**:
   * `[font:...]`, `[/font]`
   * `[color:...]`, `[/color]`
   * `<font color="...">`, `</font>`
   * Quebras de linha e espaçadores: `\n`, `\r\n`, `<br>`
   * Entidades XML obrigatórias: `&amp;`, `&lt;`, `&gt;`, `&quot;`, `&apos;`

---

## 5. Regras de Auditoria e Redirecionamento de URLs

Conforme especificado pelo projeto:
1. **Domínio Autorizado**:
   * `aionlostacademy.com`
   * `www.aionlostacademy.com`
2. **URLs Proibidas**:
   * Quaisquer links para `gameforge.com`, `gameforge.eu`, `ncsoft.com`, `plaync.com` ou variantes antigas/externas.
   * URLs corrompidas por tradução literal (ex: `https://gameforge.com/.../n 1 jogo/aion_classic` ou `n 1 força física`).
3. **Preservação de Parâmetros**:
   * Query strings e substituições dinâmicas como `?c=pt&amp;emblema=%0&amp;pid=%1` devem ser mantidas e adaptadas para o domínio Lost Academy.

---

## 6. Diretrizes de Qualidade e Terminologia MMORPG (PT-BR)

1. **Tom e Registro**:
   * Linguagem imersiva de alta fantasia épica (Atreia, Elyos, Asmodians, Balaur).
   * Sem gírias anacrônicas ou linguagem de internet informal em diálogos e lore.
   * Diálogos de NPCs devem refletir sua facção, nobreza ou natureza humilde/rude.
2. **Terminologia Consistente**:
   * Atributos de combate: Physical Attack (Ataque Físico), Magic Boost (Poder Mágico), Critical Strike (Ataque Crítico), Accuracy (Precisão), Evasion (Evasão), Parry (Aparar), Block (Bloqueio).
   * Efeitos de status: Stun (Atordoamento), Silence (Silêncio), Paralyze (Paralisia), Blind (Cegueira), Root (Enraizamento), Sleep (Sono), Fear (Medo), Knockback (Repulsão), Stumble (Queda/Derrubado).
   * Economia e Facções: Kinah (Kinah), Abyss Points (Pontos de Abismo), Daeva (Daeva), Elysea (Elísia), Asmodae (Asmodae), Balaurea (Balaurea).
3. **Erradicação de Inglês Residual e Artefatos de Dicionário**:
   * Eliminar todas as definições numéricas coladas (ex: `[ n 1 prova]`, `[ n 1 força física]`).
   * Traduzir completamente nomes de botões, abas, menus e descrições de habilidades.
   * Não deixar frases híbridas ("Causa 500 de damage ao target").

---

## 7. Critérios de Aceitação e Portões de Qualidade (Gates)

* **GATE 1**: Documentação técnica completa (`context.md` e `readme.md`) criada e aprovada.
* **GATE 2**: Inventário exaustivo de 100% dos arquivos com métricas quantitativas de entradas, termos em inglês e URLs.
* **GATE 3**: Comparação contextual com a referência oficial em inglês (`Client 5.0 - Dados Extraidos\Idioma em Inglês`).
* **GATE 4**: Tradução contextualizada de todas as pendências identificadas.
* **GATE 5**: Validação estrutural de integridade XML, integridade de tags, IDs e codificação UTF-16LE.
* **GATE 6**: Auditoria de URLs com 100% de apontamento para Lost Academy.
* **GATE 7**: Varredura regressiva contra inglês residual.
* **GATE 8**: Garantia linguística (concordância, acentuação, ortografia).
* **GATE 9**: Relatório final com tabela comparativa Antes x Depois.

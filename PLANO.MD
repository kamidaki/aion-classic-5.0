# Plano de Engenharia — Normalização de Nomes XML, Suporte Dual-Language (PT-BR / EN), Build, Publicação e Git

> **Projeto**: Aion Classic 5.0 EU — Java Emulator (Java 25 LTS)  
> **Status**: Planejamento Técnico Concluído (Fase 0 — Aguardando Aprovação para Execução)  
> **Data**: Outubro / 2026  
> **Autoridade Canônica PT-BR**: `Ferramentas e Documentos/Client e Coletas/Tradução - Português Brasil`  
> **Autoridade Canônica EN**: `Ferramentas e Documentos/Client e Coletas/Client 5.0 - Dados Extraidos/Idioma em Inglês`  
> **Dados Brutos do Cliente 5.0**: `Ferramentas e Documentos/Client e Coletas/Client 5.0 - Dados Extraidos/data`  

---

## 1. Resumo Executivo e Objetivos Técnicos

O emulador **Aion Classic 5.0 EU** (construído em **Java 25 LTS** multi-modular) opera com um subsistema estático de dados baseado em XML (`data/static_data/`) carregado via JAXB (Jakarta XML Bind 2.3.3) e validado em tempo de inicialização contra esquemas XML Schema Definition (`*.xsd`).

Atualmente, centenas de milhares de entidades estáticas (itens, NPCs, habilidades, missões, pontos de teleporte, coletáveis, mascotes, mapas e títulos) encontram-se com o atributo legado genérico `name="..."`. Este atributo sofre de quatro patologias críticas:
1. **Divergência Linguística**: Muitas entidades estão nomeadas em inglês (ex: `name="Kobold Pick"`, `name="Kamikaze Worm"`), enquanto a proposta do servidor é operar nativamente em Português do Brasil.
2. **Mojibake e Corrupção de Codificação**: Centenas de nomes contêm sequências UTF-8 duplamente decodificadas como Latin-1 (ex: `name="Espada do cÃ­rculo"`, `name="Treinamento bÃ¡sico de maÃ§a"`, `name="PrÃ³logo"`).
3. **Ausência de Suporte Internacional (Dual-Language)**: O emulador não expõe uma arquitetura que permita coexistência clara entre o nome em Inglês original e a localização em Português do Brasil.
4. **Desconexão com a Tabela Canônica do Cliente**: Nomes manuais ou stubs desatualizados divergem das tabelas auditadas oficiais do cliente (`client_strings_*.xml`).

### Objetivos Primários:
- **Migração do Esquema XML**: Substituir o atributo legado `name="..."` pela representação estruturada dual-language:
  ```xml
  name_en="Circulus's Sword" name_pt="Espada do círculo"
  ```
- **Preservação e Compatibilidade Semântica no Runtime Java**:
  - `getName()` continuará retornando rigorosamente o nome em Português (`name_pt`), mantendo 100% de compatibilidade retroativa com toda a mecânica, comandos GM, logs e UI em português.
  - Introdução do método acessor canônico `getNameEn()` para retornar o nome em Inglês oficial (`name_en`).
  - Fallback defensivo: Caso `name_pt` seja nulo ou vazio, recai sobre `name_en`; caso ambos sejam nulos, recorre ao `name` legado.
- **Validação Estrita de Schemas XSD**: Atualizar os esquemas XML (`*.xsd`) para declarar `name_en` e `name_pt`, assegurando que `XmlDataLoader.validateAsync()` passe com zero advertências e zero erros.
- **Compilação e Sincronização Estrita**: Compilar o backend com Maven 3.9+ e Java 25 LTS, sincronizando os XMLs e binários entre `Código Fonte - Emulador` e `Emulador - Produto Final`.
- **Publicação e Git**: Criar commits atômicos em conformidade com o padrão institucional do projeto e mitigar problemas de timeout HTTP 408 no GitHub.

---

## 2. Inventário Completo da Arquitetura e do Repositório

O repositório está organizado sob a raiz `D:\AION CLASSIC 5.0 - EMULADOR` com separação de responsabilidades:

```text
D:\AION CLASSIC 5.0 - EMULADOR\
├── Código Fonte - Emulador\                          # Backend Java 25 (LTS) multi-modular
│   ├── commons\                                      # Conexões de rede NIO, criptografia Blowfish/RSA, GeoIP
│   ├── chat-server\                                  # Servidor de canais e mensagens
│   ├── game-server\                                  # Motor do jogo, combate, IA, instâncias, templates
│   │   ├── src\com\aionemu\gameserver\model\         # Modelos de entidades e templates JAXB
│   │   │   └── templates\                            # VisibleObjectTemplate, L10n, ItemTemplate, NpcTemplate, etc.
│   │   ├── data\static_data\                         # Banco de dados estático em XML e esquemas XSD
│   │   └── pom.xml                                   # Configuração de compilação e packaging do GameServer
│   ├── login-server\                                 # Servidor de autenticação e contas
│   └── pom.xml                                       # POM agregador raiz (Java release 25)
│
├── Emulador - Produto Final\                         # Ambiente de execução em produção
│   ├── Aion Classic - EMULADOR.exe                   # Launcher e Supervisor nativo em Rust
│   ├── config.json                                   # Parâmetros de boot da JVM
│   ├── GameServer\                                   # Servidor de Jogo consolidado
│   │   ├── libs\                                     # Jars de produção (game-server-4.8-SNAPSHOT.jar, etc.)
│   │   └── data\static_data\                         # Espelho de dados estáticos para produção
│   ├── LoginServer\                                  # Servidor de Login consolidado
│   └── ChatServer\                                   # Servidor de Chat consolidado
│
└── Ferramentas e Documentos\                         # Hub de referências canônicas e ferramentas
    ├── Client e Coletas\
    │   ├── Client 5.0 - Dados Extraidos\             # Tabelas canônicas extraídas (Data/, Levels/, etc.)
    │   │   └── Idioma em Inglês\strings\             # 26 tabelas oficiais de strings em Inglês (UTF-16LE BOM)
    │   └── Tradução - Português Brasil\strings\      # 26 tabelas auditadas de strings em PT-BR (UTF-16LE BOM)
    ├── Ferramentas Python e PowerShell\parsersXML\   # Suíte de scripts de extração e parsers XML
    └── Patch final - Client 5.0\l10n\BRA\Data\       # Pacote compilado data.pak (84,8 MB)
```

---

## 3. Descobertas Técnicas e Inconsistências Identificadas

A varredura completa executada na Fase 0 revelou as seguintes métricas do repositório:
- **Total de arquivos XML em `static_data` com atributo `name`**: 186 arquivos.
- **Total de nós XML com atributo `name`**: 401.213 elementos.

### 3.1 Classificação Funcional dos Nós XML:
Nem todo atributo `name` em XML representa um nome de entidade translatável de jogo. A análise dividiu as ocorrências em duas classes:

1. **Entidades de Mundo / Gameplay (Alvos da Normalização Dual-Language)**:
   - `<item_template>`: 79.664 ocorrências em `items/item_templates.xml`
   - `<npc_template>`: 39.010 ocorrências em `npcs/npc_templates.xml`
   - `<skill_template>`: 12.139 ocorrências em `skills/skill_templates.xml`
   - `<quest>`: 9.465 ocorrências em `quest_data/quest_data.xml`
   - `<gatherable_template>`: 769 ocorrências em `gatherables/gatherable_templates.xml`
   - `<material>`: 3.901 ocorrências em `gatherables/gatherable_templates.xml`
   - `<pet>`: 218 ocorrências em `pets/pets.xml`
   - `<map>`: 151 ocorrências em `world_maps.xml`
   - `<itemset>`: 558 ocorrências em `item_sets/item_sets.xml`
   - `<teleloc_template>`: 284 ocorrências em `teleport_location.xml`
   - `<title>`: 262 ocorrências em `player_titles.xml`
   - `<storybook>`: 16 ocorrências em `storybook/storybook.xml`
   - `<npc_faction>`: 18 ocorrências em `npc_factions/npc_factions.xml`

2. **Atributos Técnicos e Enums (Preservados Intactos)**:
   - `<add name="PHYSICAL_DEFENSE" ...>` / `<rate name="MAXHP" ...>` / `<abs ...>` (207.431 instâncias): Representam nomes de modificadores de atributos do sistema de estatísticas (`StatEnum`), mapeados estritamente pelo enumerador Java.
   - `<motion name="...">` / `<motion_time name="...">` (8.634 instâncias): Identificadores de clipes de animação da CryEngine.
   - `<zone name="AGARIC_SPORE_ROAD_210010000" ...>` (4.002 instâncias): Identificadores estritos de colisão e malha do `ZoneName.valueOf()`. Alterá-los quebraria o subsistema de geometria.
   - `<tribe name="...">` (724 instâncias): Nomes de tribos de facções e hostilidade.

### 3.2 Taxa de Resolução Direta de Strings Auditadas:
Confrontando os identificadores das entidades contra as tabelas oficiais PT-BR e EN (`client_strings_*.xml`), obtivemos as seguintes taxas de correspondência determinística:
- **Itens (`item_templates.xml`)**: 79.586 de 79.664 correspondências (**99,90%** de cobertura).
- **NPCs (`npc_templates.xml`)**: 37.298 de 39.010 correspondências (**95,61%** de cobertura; os restantes são triggers invisíveis de IA com `name=" "`).
- **Habilidades (`skill_templates.xml`)**: 11.957 de 12.139 correspondências (**98,50%** de cobertura).
- **Coletáveis (`gatherable_templates.xml`)**: 768 de 769 correspondências (**99,87%** de cobertura).
- **Missões (`quest_data.xml`)**: 6.877 missões 5.0 oficiais mapeadas (**100%** das oficiais 5.0; as 2.588 restantes são missões legadas 4.8 preservadas no emulador).

---

## 4. Especificação Formal do Esquema Dual-Language (`name_en` e `name_pt`)

### 4.1 Formato XML Canônico:
Todas as entidades migradas adotarão a seguinte estrutura de atributos:
```xml
<!-- Exemplo: Itens -->
<item_template id="100000001" name_en="Circulus's Sword" name_pt="Espada do círculo" level="1" cName="sword_circulous" mask="24188" item_group="SWORD" quality="COMMON" price="5" desc="700558" attack_type="PHYSICAL" max_enchant="15" enchant_group="common_enchant" client_mask="35644">
    <weapon_stats hit_count="2" attack_range="1500" parry="173" critical="50" attack_speed="1400" max_damage="20" min_damage="16"/>
    <idian burn_attack="29" burn_defend="12"/>
</item_template>

<!-- Exemplo: NPCs -->
<npc_template npc_id="201000" level="1" name_en="Kamikaze Worm" name_pt="Verme Kamikaze" name_id="350051" height="1.02" group_drop="NONE" rank="NOVICE" rating="JUNK" race="MAGICALMONSTER" tribe="GENERAL" type="ABYSS_GUARD" ai="homing" srange="10" sangle="240" arange="2" attack_speed="6000" hpgauge="1">
    <stats maxHp="111">
        <speeds walk="2" group_walk="2" run="10" run_fight="10" group_run_fight="10" />
    </stats>
    <bound_radius front="0.45" side="0.56" upper="2.82" />
</npc_template>

<!-- Exemplo: Habilidades -->
<skill_template skill_id="2" name_en="Basic Dagger Training" name_pt="Treinamento básico de adaga" nameId="281817" delayId="2" stack="WA_EQUIP_ENHANCEDDAGGER" lvl="1" skilltype="PHYSICAL" skillsubtype="NONE" tslot="NOSHOW" activation="PASSIVE" cooldown="0" duration="0">
    <properties first_target="ME"/>
    <useconditions>
        <playermove allow="false"/>
    </useconditions>
    <effects>
        <wpnmastery weapon="DAGGER" effectid="102" e="1" basiclvl="1">
            <change stat="PHYSICAL_ATTACK" func="PERCENT" value="25"/>
        </wpnmastery>
    </effects>
</skill_template>

<!-- Exemplo: Missões -->
<quest id="1001" name_en="The Kerubim Threat" name_pt="A ameaça de querrubim" nameId="1102001" quest_zone="Poeta" minlevel_permitted="99" max_repeat_count="1" cannot_share="true" cannot_giveup="true" race_permitted="ELYOS" category="QUEST">
    ...
</quest>

<!-- Exemplo: Coletáveis -->
<gatherable_template id="400001" name_en="Kukuru" name_pt="Curto" nameId="701957" sourceType="VEGETABLE" harvestCount="3" skillLevel="20" harvestSkill="30002" successAdj="100" failureAdj="100" aerialAdj="100">
    <materials>
        <material rate="10000000" nameid="702021" itemid="152000001" name_en="Kukuru" name_pt="Kukuru" />
    </materials>
</gatherable_template>

<!-- Exemplo: Mascotes -->
<pet id="900000" name_en="Siberian Wild Tiger (Purebred)" name_pt="Tigre selvagem da Sibéria (de raça pura)" nameid="1600012" condition_reward="188051378">
    ...
</pet>

<!-- Exemplo: Mapas do Mundo -->
<map id="110010000" name_en="Sanctum" name_pt="Santuário" cName="LC1" water_level="16" death_level="400" world_type="ELYSEA" world_size="3072" drop_type="NONE" flags="RECALL GLIDE FLY RIDE PVP DUEL_SAME_RACE" pve_attack_ratio="150" pve_defend_ratio="50"/>

<!-- Exemplo: Locais de Teleporte -->
<teleloc_template loc_id="12" mapid="210010000" name_en="Akarios Village" name_pt="Aldeia Akarios" name_id="400499"/>

<!-- Exemplo: Títulos -->
<title id="5" nameId="1100904" desc_en="Krall Hunter" desc_pt="Caçador de Krall" race="ELYOS" available="false">
    ...
</title>
```

### 4.2 Regra de Omissão do Atributo Legado:
Conforme mandatório no prompt, o atributo genérico `name` **não deve coexistir** com `name_en` e `name_pt` nas entidades migradas. Ele será completamente substituído pelos dois atributos semânticos, eliminando a redundância e ambiguidades.

---

## 5. Estratégia de Migração e Auditoria Componente a Componente

| Componente | Arquivo XML Alvo | Arquivo XSD Alvo | Chave de Resolução | Arquivo de Strings Primário | Arquivo de Strings Secundário |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Itens** | `items/item_templates.xml` | `items/item_templates.xsd` | Atributo `desc` | `client_strings_item.xml` | `client_strings_item2.xml` |
| **NPCs** | `npcs/npc_templates.xml` | `npcs/npcs.xsd` | Atributo `name_id` | `client_strings_npc.xml` | `client_strings_monster.xml` |
| **Skills** | `skills/skill_templates.xml` | `skills/skills.xsd` | Atributo `nameId` | `client_strings_skill.xml` | `client_strings_skill.xml` |
| **Quests** | `quest_data/quest_data.xml` | `quest_data/quest_data.xsd` | Atributo `nameId` | `client_strings_quest.xml` | Nome original preservado |
| **Coletáveis** | `gatherables/gatherable_templates.xml` | `gatherables/gatherable_templates.xsd` | Atributo `nameId` | `client_strings_etc.xml` | `client_strings_item.xml` |
| **Materiais** | `gatherables/gatherable_templates.xml` | `gatherables/gatherable_templates.xsd` | Atributo `nameid` | `client_strings_item.xml` | `client_strings_item2.xml` |
| **Pets** | `pets/pets.xml` | `pets/pets.xsd` | Atributo `nameid` | `client_strings_funcpet.xml` | `client_strings_etc.xml` |
| **Mapas** | `world_maps.xml` | `world_maps.xsd` | Atributo `id` / `cName` | `client_strings_level.xml` | `client_strings_dic_place.xml` |
| **Teleportes** | `teleport_location.xml` | `teleport_location.xsd` | Atributo `name_id` | `client_strings_level.xml` | `client_strings_dic_place.xml` |
| **Títulos** | `player_titles.xml` | `player_titles.xsd` | Atributo `nameId` | `client_strings_quest.xml` | `client_strings_ui.xml` |
| **Item Sets** | `item_sets/item_sets.xml` | `item_sets/item_sets.xsd` | Atributo `name` existente | `client_strings_item.xml` | Normalização bilíngue |

---

## 6. Arquitetura de Integração do Runtime Java

### 6.1 `VisibleObjectTemplate.java` e Hierarquia Base
A classe abstrata `VisibleObjectTemplate` é o nó raiz de quase todos os templates de objetos físicos do mundo.
Modificação canônica:
```java
package com.aionemu.gameserver.model.templates;

/**
 * @author Lost Academy Team & Durak
 */
public abstract class VisibleObjectTemplate implements L10n {

	public abstract int getTemplateId();

	/**
	 * Retorna o nome padrão/primário (PT-BR) do objeto no emulador.
	 * Mantém 100% de compatibilidade retroativa com código existente.
	 */
	public abstract String getName();

	/**
	 * Retorna o nome em inglês (EN) oficial da entidade para futuras APIs.
	 */
	public String getNameEn() {
		return getName();
	}

	public BoundRadius getBoundRadius() {
		return BoundRadius.DEFAULT;
	}
}
```

### 6.2 Implementação nos Templates Concretos
Exemplo padrão implementado em `ItemTemplate`, `NpcTemplate`, `SkillTemplate`, `QuestTemplate`, `GatherableTemplate`, `PetTemplate`, `WorldMapTemplate`, `TelelocationTemplate`:
```java
@XmlAttribute(name = "name_en")
private String nameEn;

@XmlAttribute(name = "name_pt")
private String namePt;

@Deprecated
@XmlAttribute(name = "name")
private String name;

@Override
public String getName() {
	if (namePt != null && !namePt.isEmpty()) {
		return namePt;
	}
	if (name != null && !name.isEmpty()) {
		return name;
	}
	return nameEn != null ? nameEn : "";
}

public String getNameEn() {
	if (nameEn != null && !nameEn.isEmpty()) {
		return nameEn;
	}
	if (name != null && !name.isEmpty()) {
		return name;
	}
	return namePt != null ? namePt : "";
}
```

### 6.3 Atualização dos Esquemas XSD
Todos os esquemas XML associados receberão as declarações formais:
```xml
<xs:attribute name="name_en" type="xs:string"/>
<xs:attribute name="name_pt" type="xs:string"/>
<xs:attribute name="name" type="xs:string"/> <!-- Mantido como opcional para resiliência -->
```
Isso assegura que o validador JAXB/SAX em `XmlDataLoader.java` (`XmlUtil.getSchema(XML_SCHEMA_FILE).newValidator().validate(...)`) execute sem quaisquer erros de validação estrutural.

---

## 7. Pipeline de Normalização, Extração e Tradução Automatizada

Será desenvolvido um script modular de alta performance em Python (`Ferramentas e Documentos/Ferramentas Python e PowerShell/parsersXML/normalize_xml_dual_language.py`) seguindo a filosofia dos parsers já existentes no projeto.

### Etapas do Pipeline:
1. **Indexação em Memória das Strings Oficiais**:
   - Carrega 100% dos arquivos de `Tradução - Português Brasil/strings/*.xml` decodificando UTF-16LE com BOM.
   - Carrega 100% dos arquivos de `Client 5.0 - Dados Extraidos/Idioma em Inglês/strings/*.xml` decodificando UTF-16LE com BOM.
   - Mapeia por `ID numérico -> Body` e por `STR_NAME -> Body`.
2. **Higienização de Strings**:
   - Aplica `html.unescape()` para entidades como `&quot;`, `&amp;`, `&apos;`.
   - Remove sequências residuais de mojibake (ex: `Ã¡` -> `á`, `Ã©` -> `é`).
   - Remove tags XML vazias e normaliza espaçamentos.
3. **Processamento Streaming / AST dos Arquivos XML**:
   - Para cada entidade alvo em `Código Fonte - Emulador/game-server/data/static_data`:
     - Resolve `name_pt` a partir da tabela PT-BR.
     - Resolve `name_en` a partir da tabela EN.
     - Aplica fallbacks determinísticos quando o ID for inexistente (ex: missões preservadas 4.8).
     - Remove o atributo `name="..."` legado.
     - Insere `name_en="..." name_pt="..."`.
4. **Escrita UTF-8 com Indentação Preservada**:
   - Gravação dos arquivos com quebras de linha canônicas (`\r\n` ou `\n` conforme original).
   - Validação da integridade de codificação UTF-8.

---

## 8. Plano de Compilação Maven, Empacotamento e Sincronização

A execução do build e empacotamento seguirá o fluxo canônico:

1. **Compilação Backend**:
   ```powershell
   cd "D:\AION CLASSIC 5.0 - EMULADOR\Código Fonte - Emulador"
   mvn clean package -DskipTests=false
   ```
   - Valida compilação sob Java 25 LTS com `maven-compiler-plugin 3.14.1`.
   - Executa testes unitários (JUnit 6 / Surefire).
   - Gera o pacote `game-server/target/game-server-4.8-SNAPSHOT.jar` e dependências.

2. **Sincronização Código-Fonte $\leftrightarrow$ Produto Final**:
   Conforme diretriz inegociável do projeto em `CONTEXT.md`:
   - Copiar o JAR compilado `game-server-4.8-SNAPSHOT.jar` para `Emulador - Produto Final/GameServer/libs/`.
   - Copiar o JAR compilado `commons-4.8-SNAPSHOT.jar` para `Emulador - Produto Final/GameServer/libs/`.
   - Espelhar recursivamente todo o diretório atualizado `Código Fonte - Emulador/game-server/data/static_data/` para `Emulador - Produto Final/GameServer/data/static_data/`.

---

## 9. Protocolo de Validação Multi-Fases e Portões de Aceitação

Para garantir **Zero Regressão**, a entrega passará por 6 Portões de Aceitação rigorosos:

* **PORTÃO 1 (Integridade XML)**:
  - 100% dos arquivos XML modificados passam por parser sintático estrito sem erros de formatação.
  - Zero caracteres de mojibake remanescentes nos nomes.
* **PORTÃO 2 (Conformidade com Esquema XSD)**:
  - Validação SAX/JAXB de `static_data.xsd` e todos os sub-esquemas contra os arquivos modificados.
  - Zero erros de validação de esquema.
* **PORTÃO 3 (Compilação Java 25 Limpa)**:
  - Execução de `mvn clean compile` e `mvn package` com zero erros e zero advertências bloqueantes.
* **PORTÃO 4 (Sincronização 100% Produto Final)**:
  - Verificação de hash MD5/SHA256 ou paridade de bytes entre `Código Fonte - Emulador` e `Emulador - Produto Final`.
* **PORTÃO 5 (Validação de Runtime do GameServer)**:
  - Teste de carregamento do `XmlDataLoader` e `DataManager` em tempo de boot do GameServer.
  - Verificação de que o servidor carrega os 79.664 itens, 39.010 NPCs e 12.139 skills sem exceções de inicialização.
* **PORTÃO 6 (Verificação Funcional de Acessores)**:
  - Validação de que `itemTemplate.getName()` retorna a string em Português e `itemTemplate.getNameEn()` retorna a string em Inglês.

---

## 10. Estratégia de Git, Mensagens de Commit Padronizadas e Mitigação de HTTP 408

### 10.1 Padrão Obrigatório de Commits:
Seguindo rigorosamente `CONTEXT.md`:
- **Idioma Estritamente em Português**.
- **Formato de Uma Linha por Alteração**.

Plano de commits atômicos:
1. `feat(data): adicionar suporte a name_en e name_pt nos esquemas xsd de static_data`
2. `feat(server): implementar getnameen e mapeamento jaxb dual-language nos templates java`
3. `fix(static_data): normalizar nomes de itens para dual-language name_en e name_pt alinhados ao cliente`
4. `fix(static_data): normalizar nomes de npcs para dual-language name_en e name_pt alinhados ao cliente`
5. `fix(static_data): normalizar nomes de skills para dual-language name_en e name_pt alinhados ao cliente`
6. `fix(static_data): normalizar nomes de quests, coletaveis, pets, mapas e titulos para dual-language`
7. `build: compilar game-server em java 25 e sincronizar produto final com static_data atualizado`

### 10.2 Procedimento para Prevenção do Erro HTTP 408 (Push de Grande Escala):
Conforme documentado em `CONTEXT.md`, caso o `git push` tradicional encontre timeout ou reempacotamento de objetos históricos:
1. Identificar os objetos delta pendentes:
   ```cmd
   git rev-list --objects HEAD ^origin/main
   ```
2. Gerar pacote enxuto via `git pack-objects --stdout`.
3. Transmitir delta compacto via Smart HTTP ou push pontual da branch.

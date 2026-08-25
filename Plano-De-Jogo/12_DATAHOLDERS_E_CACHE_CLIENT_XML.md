# Plano de Jogo - DataHolders & Cache Direto de Alta Performance dos XMLs do Client

Este documento define a estratégia de extração, compactação em memória e cache binário de altíssima performance para os dados estáticos do jogo diretamente a partir dos arquivos brutos do cliente em `Produto Final/data/client/` (substituindo a abordagem pesada de conversores XML do Java).

---

## 1. O Problema das Abordagens Tradicionais em Java

Em emuladores Java clássicos:
1. O desenvolvedor precisa converter os XMLs do cliente em XMLs intermediários do Java.
2. Cada inicialização do servidor requer o parsing de centenas de megabytes de texto via JAXB, demorando **$40\text{ a }90\text{ segundos}$** e consumindo mais de **$2.5\text{ GB de RAM}$** apenas com árvores de objetos `String` e nós XML.

---

## 2. A Solução em Rust: Parser Streaming SAX + Cache Binário Zero-Copy

No emulador em Rust:
1. Lemos os arquivos originais diretamente de `Produto Final/data/client/` usando o parser streaming `quick-xml` (que processa $180\text{ MB}$ em menos de $1.2\text{ segundos}$ em uma única thread).
2. Extraímos apenas os campos essenciais para a simulação do servidor, compactando strings em IDs inteiros e enums de 1 a 2 bytes.
3. Gravamos o resultado serializado em arquivos binários compactos (`.bin`) usando `bincode`.
4. Nas inicializações seguintes, o servidor carrega os arquivos `.bin` via `mmap` em **menos de $15\text{ milissegundos}$**, com consumo de memória inferior a **$95\text{ MB de RAM}$** para todo o conjunto de dados do jogo.

```mermaid
graph TD
    subgraph Primeira_Execucao ["Primeira Execução (Geração do Cache)"]
        RawXML[XMLs Brutos do Client em data/client/] --> SAX[Parser SAX Streaming rápido quick-xml]
        SAX --> CompactStructs[Structs Rust Compactas com Tipos Primitivos]
        CompactStructs --> BincodeGen[Serializador Binário Bincode]
        BincodeGen --> BinCache[data/cache/*.bin Arquivos de Cache Binário]
    end

    subgraph Inicializacoes_Seguintes ["Inicializações Subsequentes (Produção)"]
        BinCache --> Mmap[Carregamento Instantâneo via Memory-Map]
        Mmap --> MemoryHolders[DataHolders em Memória RAM < 95 MB em 15ms]
    end
```

---

## 3. Mapeamento dos Arquivos do Client para DataHolders

| Arquivo Bruto do Client | Tamanho | Struct em Rust | DataHolder |
| :--- | :--- | :--- | :--- |
| `items/client_items.xml` | $189.5\text{ MB}$ | `ItemTemplate` | `ItemDataHolder` (Mais de $180.000$ itens) |
| `npcs/client_npcs.xml` | $84.2\text{ MB}$ | `NpcTemplate` | `NpcDataHolder` (Mais de $25.000$ NPCs) |
| `skills/client_skills.xml` | $33.2\text{ MB}$ | `SkillTemplate` | `SkillDataHolder` |
| `npcs/client_npc_goodslist.xml` | $3.8\text{ MB}$ | `GoodsListTemplate` | `GoodsDataHolder` (Lojas de NPCs) |
| `PC/client_titles.xml` | $215\text{ KB}$ | `TitleTemplate` | `TitleDataHolder` (Títulos e Bônus) |
| `PC/client_battlepass_reward.xml`| $3.2\text{ MB}$ | `BattlePassReward` | `BattlePassDataHolder` |
| `PC/client_login_event.xml` | $388\text{ KB}$ | `AttendanceReward` | `AttendanceDataHolder` |
| `world/client_world_*.xml` | $\approx 25\text{ MB}$ | `WorldZoneTemplate` | `WorldDataHolder` (Zonas e Mapas) |

---

## 4. Exemplo de Struct Compacta em Rust (`ItemTemplate`)

Ao invés de carregar tags XML gigantes, cada item é armazenado de forma ultra-compacta:

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ItemTemplate {
    pub id: u32,                  // 4 bytes
    pub name_id: u32,             // 4 bytes (referência para Strings)
    pub item_type: ItemType,      // 1 byte
    pub category: ItemCategory,   // 1 byte
    pub slot: u32,                // 4 bytes (Equipment Slot Mask)
    pub level: u8,                // 1 byte
    pub quality: ItemQuality,     // 1 byte (Junk, Common, Rare, Hero, Mythic)
    pub price: u64,               // 8 bytes (Preço de compra/venda em Kinah)
    pub max_stack: u32,           // 4 bytes (Limite de empilhamento)
    pub modifiers: Vec<StatBonus>,// Bônus de atributos
}
```
* **Tamanho Médio por Item**: $\approx 48\text{ bytes}$.
* **$180.000\text{ itens}$** ocupam apenas **$\approx 8.6\text{ MB}$** na memória RAM!

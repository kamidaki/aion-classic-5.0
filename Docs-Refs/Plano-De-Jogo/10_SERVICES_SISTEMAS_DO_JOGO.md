# Plano de Jogo - Serviços Centrais do Jogo (Services)

Este documento mapeia os **59 serviços essenciais** do Java 4.8 (`com/aionemu/gameserver/services/`) e do Java 2.8 para a arquitetura modular de serviços assíncronos em Rust.

---

## 1. Mapeamento Geral dos Serviços por Categoria

### A. Economia, Inventário e Equipamentos
| Serviço Java 4.8 | Módulo em Rust | Responsabilidade |
| :--- | :--- | :--- |
| `services.item.ItemService` | `services::item_service.rs` | Criação, deleção, divisão e fusão de itens |
| `services.ArmsfusionService` | `services::armsfusion.rs` | Fusão de armas de duas mãos (combina atributos e slots de manastone) |
| `services.EnchantService` | `services::enchant.rs` | Encantamento com Enchantment Stones (+1 até +15), Godstones e Manastones |
| `services.CubeExpandService` | `services::cube_expand.rs` | Expansão de linhas da bolsa via Kinah em NPCs ou cupons |
| `services.WarehouseService` | `services::warehouse.rs` | Armazém pessoal, armazém de conta e armazém de legião |
| `services.BrokerService` | `services::broker.rs` | Casa de leilões/mercado com taxas de corretagem e histórico de vendas |
| `services.TradeService` | `services::trade.rs` | Trocas diretas entre dois jogadores (P2P Trade) com confirmação dupla |
| `services.PrivateStoreService`| `services::private_store.rs`| Lojas pessoais abertas por jogadores no mapa |
| `services.mail.MailService` | `services::mail.rs` | Envio de cartas, cartas expressas com NPC mensageiro e anexos de itens/Kinah |
| `services.RepurchaseService` | `services::repurchase.rs` | Recompra (Buyback) de itens vendidos acidentalmente a NPCs |

---

### B. Social, Legiões e Grupos
| Serviço Java 4.8 | Módulo em Rust | Responsabilidade |
| :--- | :--- | :--- |
| `services.LegionService` | `services::legion.rs` | Criação de legiões, níveis (1 a 8), cargos, permissões, histórico e buffs de guilda |
| `services.HTMLService` | `services::emblem_download.rs`| Upload e download do emblema da legião em chunks de pacotes para o cliente |
| `services.AutoGroupService` | `services::auto_group.rs` | Localizador automático de grupos (Dungeon Matchmaking) para masmorras |
| `services.FindGroupService` | `services::find_group.rs` | Mural de busca de grupos (LFG - Looking For Group) |
| `services.SocialService` | `services::social.rs` | Lista de amigos, lista de bloqueio e status online/offline |

---

### C. PvP, Abyss, Cerco e Facções
| Serviço Java 4.8 | Módulo em Rust | Responsabilidade |
| :--- | :--- | :--- |
| `services.abyss.AbyssService` | `services::abyss.rs` | Cálculo de Abyss Points (AP), ranqueamento diário (Soldier até Governor) e Abyss Skills |
| `services.SiegeService` | `services::siege.rs` | Guerras de cerco em fortalezas e artefatos, timers de vulnerabilidade, escudos e recompensas de medalhas |
| `services.RiftService` | `services::rift.rs` | Abertura e fechamento de fendas dimensionais entre Elysea e Asmodae |
| `services.DuelService` | `services::duel.rs` | Duelos 1v1 com bandeira de arena, contagem regressiva e término sem perda de XP |
| `services.KiskService` | `services::kisk.rs` | Pedras de ressurreição móveis (Kisks) plantadas por jogadores no mapa |

---

### D. Mundo, Teleportes e Ambiente
| Serviço Java 4.8 | Módulo em Rust | Responsabilidade |
| :--- | :--- | :--- |
| `services.teleport.TeleportService` | `services::teleport.rs` | Teleporte por estátuas, voo em rotas de pássaro (Flight Path) e correntes de vento |
| `services.WeatherService` | `services::weather.rs` | Sistema de clima dinâmico por zona (chuva, neve, sol, tempestade) |
| `services.StaticDoorService` | `services::static_doors.rs`| Controle de portas interativas em masmorras e cidades |
| `services.RespawnService` | `services::respawn.rs` | Ressurreição no obelisco de vínculo, kisk ou ressurreição por skill |

---

### E. Gestão, Segurança e Administração
| Serviço Java 4.8 | Módulo em Rust | Responsabilidade |
| :--- | :--- | :--- |
| `services.AdminService` | `services::admin.rs` | Comandos de Game Master (`//spawn`, `//goto`, `//additem`, `//kick`, etc.) |
| `services.PunishmentService` | `services::punishment.rs` | Sistema de prisão (Prison Map), silenciamento de chat (Mute) e banimentos |
| `services.PeriodicSaveService`| `services::periodic_save.rs`| Salvamento assíncrono em lote de personagens, inventários e quests a cada 5 minutos |

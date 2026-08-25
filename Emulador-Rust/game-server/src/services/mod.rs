//! Camada Central de Serviços do Servidor de Jogo (Padrão Java AION - com.aionemu.gameserver.services)
//!
//! Cada serviço gerencia um subsistema específico e isolado, recebendo dados e orquestrando o estado do jogo.

pub mod spatial_service;
pub mod player_service;
pub mod combat_service;
pub mod skill_service;
pub mod item_service;
pub mod item;
pub mod dialog_service;
pub mod mail_service;
pub mod chat_service;
pub mod environment_service;

pub use spatial_service::SpatialService;
pub use player_service::PlayerService;
pub use combat_service::CombatService;
pub use skill_service::SkillService;
pub use item_service::ItemService;
pub use item::{
    ItemEquipService, ItemSocketService, ItemFusionService, ItemEnchantService,
    ItemChargeService, ItemDyeService, ItemRemodelService, ItemSplitService,
};
pub use dialog_service::DialogService;
pub use mail_service::MailService;
pub use chat_service::ChatService;
pub use environment_service::EnvironmentService;

// Re-exportações dos serviços especialistas
pub use crate::teleport::TeleportService;
pub use crate::title::TitleService;
pub use crate::trade::TradeService;
pub use crate::social::PartyService;
pub use crate::guild::GuildManager;
pub use crate::environment::WindstreamService;

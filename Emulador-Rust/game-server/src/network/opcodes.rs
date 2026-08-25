//! Catálogo Canônico de Opcodes CM e SM - Aion Classic 4.5

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PacketDirection {
    ClientToServer,
    ServerToClient,
}

#[derive(Debug, Clone)]
pub struct PacketDefinition {
    pub opcode: u16,
    pub name: &'static str,
    pub direction: PacketDirection,
    pub description: &'static str,
}

/// Opcodes de Cliente (CM - Client to Server)
pub mod cm {
    pub const CM_VERSION_CHECK: u16 = 0x00;
    pub const CM_DISCONNECT: u16 = 0x02;
    pub const CM_QUIT: u16 = 0x03;
    pub const CM_DELETE_CHARACTER: u16 = 0x04;
    pub const CM_REVIVE: u16 = 0x05;
    pub const CM_RECONNECT_AUTH: u16 = 0x06;
    pub const CM_ENTER_WORLD: u16 = 0x08;
    pub const CM_LEVEL_READY: u16 = 0x09;
    pub const CM_CHARACTER_LIST: u16 = 0x0B;
    pub const CM_CREATE_CHARACTER: u16 = 0x0C;
    pub const CM_CHECK_NICKNAME: u16 = 0x0D;
    pub const CM_CAPTCHA: u16 = 0x0E;
    pub const CM_TIME_CHECK: u16 = 0x12;
    pub const CM_GATHER: u16 = 0x13;
    pub const CM_PET_EMOTE: u16 = 0x15;
    pub const CM_PET: u16 = 0x16;
    pub const CM_CHAT_MESSAGE_PUBLIC: u16 = 0x1B;
    pub const CM_CHAT_MESSAGE_WHISPER: u16 = 0x1C;
    pub const CM_TARGET_SELECT: u16 = 0x1F;
    pub const CM_ATTACK: u16 = 0x20;
    pub const CM_CASTSPELL: u16 = 0x21;
    pub const CM_USE_ITEM: u16 = 0x25;
    pub const CM_EQUIP_ITEM: u16 = 0x26;
    pub const CM_EMOTION: u16 = 0x2B;
    pub const CM_PING: u16 = 0x2C;
    pub const CM_MOVE: u16 = 0x30;
    pub const CM_PATH_FLY: u16 = 0x31;
    pub const CM_BUY_SELL: u16 = 0x33;
    pub const CM_SHOW_DIALOG: u16 = 0x34;
    pub const CM_DIALOG_SELECT: u16 = 0x36;
    pub const CM_WINDSTREAM: u16 = 0x46;
    pub const CM_PARTY: u16 = 0x60;
    pub const CM_PARTY_BY_NAME: u16 = 0x61;
    pub const CM_ADD_BUDDY: u16 = 0x6F;
    pub const CM_REGISTER_AUTOGROUP: u16 = 0x75;
    pub const CM_MAIL_READ: u16 = 0x86;
    pub const CM_MAIL_POSTMAN: u16 = 0xA2;
    pub const CM_REQUEST_GUILD_HISTORY: u16 = 0xC5;
    pub const CM_GUILD_USER_BUY_BUFF: u16 = 0xC6;
    pub const CM_GUILD: u16 = 0xC7;
    pub const CM_GLOBAL_TRADE_REGISTER: u16 = 0x0100;
    pub const CM_GLOBAL_TRADE_SALESLOG: u16 = 0x0101;
    pub const CM_GLOBAL_TRADE_BUY: u16 = 0x0102;
    pub const CM_GLOBAL_TRADE_AVG_PRICE: u16 = 0x0103;
}

/// Opcodes de Servidor (SM - Server to Client)
pub mod sm {
    pub const SM_VERSION_CHECK: u16 = 0x00;
    pub const SM_STATS_INFO: u16 = 0x01;
    pub const SM_STATUPDATE_HP: u16 = 0x03;
    pub const SM_STATUPDATE_MP: u16 = 0x04;
    pub const SM_ATTACK_STATUS: u16 = 0x05;
    pub const SM_STATUPDATE_DP: u16 = 0x06;
    pub const SM_STATUPDATE_EXP: u16 = 0x08;
    pub const SM_ENTER_WORLD_CHECK: u16 = 0x0D;
    pub const SM_NPC_INFO: u16 = 0x0E;
    pub const SM_PLAYER_SPAWN: u16 = 0x0F;
    pub const SM_GATHERABLE_INFO: u16 = 0x11;
    pub const SM_REQUEST_TELEPORT: u16 = 0x14;
    pub const SM_POSITION_SELF: u16 = 0x15;
    pub const SM_DELETE: u16 = 0x16;
    pub const SM_MESSAGE: u16 = 0x18;
    pub const SM_SYSTEM_MESSAGE: u16 = 0x19;
    pub const SM_INVENTORY_INFO: u16 = 0x1A;
    pub const SM_PLAYER_INFO: u16 = 0x20;
    pub const SM_CASTSPELL: u16 = 0x21;
    pub const SM_UPDATE_PLAYER_APPEARANCE: u16 = 0x24;
    pub const SM_EMOTION: u16 = 0x25;
    pub const SM_CASTSPELL_RESULT: u16 = 0x2B;
    pub const SM_SKILL_LIST: u16 = 0x2C;
    pub const SM_ABNORMAL_STATE: u16 = 0x31;
    pub const SM_SKILL_COOLDOWN: u16 = 0x33;
    pub const SM_MOVE: u16 = 0x37;
    pub const SM_DIALOG_WINDOW: u16 = 0x3C;
    pub const SM_WEATHER: u16 = 0x43;
    pub const SM_QUEST_LIST: u16 = 0x47;
    pub const SM_GUILD_INFO: u16 = 0x6D;
    pub const SM_BUDDY_LIST: u16 = 0x83;
    pub const S_SA_ACCOUNT_ITEM_NOTI: u16 = 0x8B;
    pub const SM_GUILD_MEMBER_INFO: u16 = 0x9C;
    pub const SM_MAIL: u16 = 0xA0;
    pub const SM_WIND_PATH_RESULT: u16 = 0xA2;
    pub const SM_WIND_STATE_INFO: u16 = 0xA3;
    pub const SM_PARTY_MATCH: u16 = 0xA5;
    pub const SM_USER_SELL_HISTORY_LIST: u16 = 0xA6;
    pub const SM_GUILD_EMBLEM_IMG_DATA: u16 = 0xD5;
    pub const SM_SKILL_PENALTY_STATUS_OTHER: u16 = 0xD8;
    pub const SM_ALLIANCE_INFO: u16 = 0xF5;
    pub const SM_ALLIANCE_MEMBER_INFO: u16 = 0xF6;
    pub const SM_STORE_SALE_INFO: u16 = 0xFD;
    pub const SM_GLOBAL_TRADE_LIST: u16 = 0x013C;
    pub const SM_GLOBAL_TRADE_COMMIT: u16 = 0x013F;
    pub const SM_GLOBAL_TRADE_SALESLOG: u16 = 0x0141;
    pub const SM_GLOBAL_TRADE_STATE: u16 = 0x0144;
    pub const SM_GLOBAL_TRADE_HISTORY: u16 = 0x0145;
    pub const SM_GUILD_DONATION: u16 = 0x0157;
    pub const SM_USER_GUILD_DONATION: u16 = 0x0158;
    pub const SM_USER_GUILD_DONATION_LIST: u16 = 0x0159;
}

pub struct PacketRegistry;

impl PacketRegistry {
    pub const CLIENT_PACKETS: &'static [PacketDefinition] = &[
        PacketDefinition { opcode: cm::CM_VERSION_CHECK, name: "CM_VERSION_CHECK", direction: PacketDirection::ClientToServer, description: "Handshake de versão e chaves de criptografia" },
        PacketDefinition { opcode: cm::CM_DISCONNECT, name: "CM_DISCONNECT", direction: PacketDirection::ClientToServer, description: "Notificação de desconexão do cliente" },
        PacketDefinition { opcode: cm::CM_QUIT, name: "CM_QUIT", direction: PacketDirection::ClientToServer, description: "Retorno para a tela de seleção de personagens" },
        PacketDefinition { opcode: cm::CM_DELETE_CHARACTER, name: "CM_DELETE_CHARACTER", direction: PacketDirection::ClientToServer, description: "Solicitação de deleção de personagem" },
        PacketDefinition { opcode: cm::CM_REVIVE, name: "CM_REVIVE", direction: PacketDirection::ClientToServer, description: "Ressurreição no obelisco ou kisk" },
        PacketDefinition { opcode: cm::CM_RECONNECT_AUTH, name: "CM_RECONNECT_AUTH", direction: PacketDirection::ClientToServer, description: "Reconexão ao servidor de autenticação" },
        PacketDefinition { opcode: cm::CM_ENTER_WORLD, name: "CM_ENTER_WORLD", direction: PacketDirection::ClientToServer, description: "Entrada no mundo com o personagem selecionado" },
        PacketDefinition { opcode: cm::CM_LEVEL_READY, name: "CM_LEVEL_READY", direction: PacketDirection::ClientToServer, description: "Notificação de renderização do mapa 3D concluída" },
        PacketDefinition { opcode: cm::CM_CHARACTER_LIST, name: "CM_CHARACTER_LIST", direction: PacketDirection::ClientToServer, description: "Requisição da lista de personagens da conta" },
        PacketDefinition { opcode: cm::CM_CREATE_CHARACTER, name: "CM_CREATE_CHARACTER", direction: PacketDirection::ClientToServer, description: "Criação de novo personagem e personalização" },
        PacketDefinition { opcode: cm::CM_CHECK_NICKNAME, name: "CM_CHECK_NICKNAME", direction: PacketDirection::ClientToServer, description: "Verificação de disponibilidade de nome" },
        PacketDefinition { opcode: cm::CM_CAPTCHA, name: "CM_CAPTCHA", direction: PacketDirection::ClientToServer, description: "Validação de captcha anti-bot" },
        PacketDefinition { opcode: cm::CM_TIME_CHECK, name: "CM_TIME_CHECK", direction: PacketDirection::ClientToServer, description: "Sincronização de relógio de alta precisão" },
        PacketDefinition { opcode: cm::CM_GATHER, name: "CM_GATHER", direction: PacketDirection::ClientToServer, description: "Extração de vitalidade ou éter" },
        PacketDefinition { opcode: cm::CM_PET_EMOTE, name: "CM_PET_EMOTE", direction: PacketDirection::ClientToServer, description: "Interação e carinho com mascote" },
        PacketDefinition { opcode: cm::CM_PET, name: "CM_PET", direction: PacketDirection::ClientToServer, description: "Spawn, despawn e bolsa de pet" },
        PacketDefinition { opcode: cm::CM_CHAT_MESSAGE_PUBLIC, name: "CM_CHAT_MESSAGE_PUBLIC", direction: PacketDirection::ClientToServer, description: "Mensagem enviada no chat público" },
        PacketDefinition { opcode: cm::CM_CHAT_MESSAGE_WHISPER, name: "CM_CHAT_MESSAGE_WHISPER", direction: PacketDirection::ClientToServer, description: "Mensagem privada enviada a outro jogador" },
        PacketDefinition { opcode: cm::CM_TARGET_SELECT, name: "CM_TARGET_SELECT", direction: PacketDirection::ClientToServer, description: "Seleção de alvo com mouse ou Tab" },
        PacketDefinition { opcode: cm::CM_ATTACK, name: "CM_ATTACK", direction: PacketDirection::ClientToServer, description: "Ataque físico automático continuo" },
        PacketDefinition { opcode: cm::CM_CASTSPELL, name: "CM_CASTSPELL", direction: PacketDirection::ClientToServer, description: "Conjuração de magia ou técnica especial" },
        PacketDefinition { opcode: cm::CM_USE_ITEM, name: "CM_USE_ITEM", direction: PacketDirection::ClientToServer, description: "Consumo de poção, comida ou pergaminho" },
        PacketDefinition { opcode: cm::CM_EQUIP_ITEM, name: "CM_EQUIP_ITEM", direction: PacketDirection::ClientToServer, description: "Equipar ou desequipar item" },
        PacketDefinition { opcode: cm::CM_EMOTION, name: "CM_EMOTION", direction: PacketDirection::ClientToServer, description: "Emotes, asas abertas, sentar ou pular" },
        PacketDefinition { opcode: cm::CM_PING, name: "CM_PING", direction: PacketDirection::ClientToServer, description: "Heartbeat de conexão ativa" },
        PacketDefinition { opcode: cm::CM_MOVE, name: "CM_MOVE", direction: PacketDirection::ClientToServer, description: "Vetor de deslocamento contínuo" },
        PacketDefinition { opcode: cm::CM_PATH_FLY, name: "CM_PATH_FLY", direction: PacketDirection::ClientToServer, description: "Progresso de voo em corrente de vento" },
        PacketDefinition { opcode: cm::CM_SHOW_DIALOG, name: "CM_SHOW_DIALOG", direction: PacketDirection::ClientToServer, description: "Abertura de diálogo com NPC" },
        PacketDefinition { opcode: cm::CM_BUY_SELL, name: "CM_BUY_SELL", direction: PacketDirection::ClientToServer, description: "Compra e venda em loja de NPC" },
        PacketDefinition { opcode: cm::CM_DIALOG_SELECT, name: "CM_DIALOG_SELECT", direction: PacketDirection::ClientToServer, description: "Seleção de opção em diálogo HTML" },
        PacketDefinition { opcode: cm::CM_WINDSTREAM, name: "CM_WINDSTREAM", direction: PacketDirection::ClientToServer, description: "Navegação em rota de fluxo de vento" },
        PacketDefinition { opcode: cm::CM_PARTY, name: "CM_PARTY", direction: PacketDirection::ClientToServer, description: "Operações de grupo/party por ID" },
        PacketDefinition { opcode: cm::CM_PARTY_BY_NAME, name: "CM_PARTY_BY_NAME", direction: PacketDirection::ClientToServer, description: "Convite de grupo/party por nome de personagem" },
        PacketDefinition { opcode: cm::CM_ADD_BUDDY, name: "CM_ADD_BUDDY", direction: PacketDirection::ClientToServer, description: "Adicionar ou remover amigo da lista" },
        PacketDefinition { opcode: cm::CM_REGISTER_AUTOGROUP, name: "CM_REGISTER_AUTOGROUP", direction: PacketDirection::ClientToServer, description: "Entrada na fila de matchmaking de arena" },
        PacketDefinition { opcode: cm::CM_MAIL_READ, name: "CM_MAIL_READ", direction: PacketDirection::ClientToServer, description: "Leitura ou interação com carta no correio" },
        PacketDefinition { opcode: cm::CM_MAIL_POSTMAN, name: "CM_MAIL_POSTMAN", direction: PacketDirection::ClientToServer, description: "Envio de carta pelo correio ou mensageiro" },
        PacketDefinition { opcode: cm::CM_REQUEST_GUILD_HISTORY, name: "CM_REQUEST_GUILD_HISTORY", direction: PacketDirection::ClientToServer, description: "Histórico de eventos e registros da legião" },
        PacketDefinition { opcode: cm::CM_GUILD_USER_BUY_BUFF, name: "CM_GUILD_USER_BUY_BUFF", direction: PacketDirection::ClientToServer, description: "Compra ou ativação de buff da legião" },
        PacketDefinition { opcode: cm::CM_GUILD, name: "CM_GUILD", direction: PacketDirection::ClientToServer, description: "Operações gerais de gerenciamento da legião" },
        PacketDefinition { opcode: cm::CM_GLOBAL_TRADE_REGISTER, name: "CM_GLOBAL_TRADE_REGISTER", direction: PacketDirection::ClientToServer, description: "Registro de item para venda no broker" },
        PacketDefinition { opcode: cm::CM_GLOBAL_TRADE_SALESLOG, name: "CM_GLOBAL_TRADE_SALESLOG", direction: PacketDirection::ClientToServer, description: "Consulta de histórico de vendas do broker" },
        PacketDefinition { opcode: cm::CM_GLOBAL_TRADE_BUY, name: "CM_GLOBAL_TRADE_BUY", direction: PacketDirection::ClientToServer, description: "Compra de item anunciado no broker" },
        PacketDefinition { opcode: cm::CM_GLOBAL_TRADE_AVG_PRICE, name: "CM_GLOBAL_TRADE_AVG_PRICE", direction: PacketDirection::ClientToServer, description: "Consulta de preço médio no broker" },
    ];

    pub const SERVER_PACKETS: &'static [PacketDefinition] = &[
        PacketDefinition { opcode: sm::SM_VERSION_CHECK, name: "SM_VERSION_CHECK", direction: PacketDirection::ServerToClient, description: "Resposta de versão e chave de sessão" },
        PacketDefinition { opcode: sm::SM_STATS_INFO, name: "SM_STATS_INFO", direction: PacketDirection::ServerToClient, description: "Atributos, defesas e resistências do jogador" },
        PacketDefinition { opcode: sm::SM_STATUPDATE_HP, name: "SM_STATUPDATE_HP", direction: PacketDirection::ServerToClient, description: "Atualização de HP do jogador local" },
        PacketDefinition { opcode: sm::SM_STATUPDATE_MP, name: "SM_STATUPDATE_MP", direction: PacketDirection::ServerToClient, description: "Atualização de MP do jogador local" },
        PacketDefinition { opcode: sm::SM_ATTACK_STATUS, name: "SM_ATTACK_STATUS", direction: PacketDirection::ServerToClient, description: "Atualização de HP de outras entidades no mundo" },
        PacketDefinition { opcode: sm::SM_STATUPDATE_DP, name: "SM_STATUPDATE_DP", direction: PacketDirection::ServerToClient, description: "Atualização de Pontos Divinos (DP)" },
        PacketDefinition { opcode: sm::SM_STATUPDATE_EXP, name: "SM_STATUPDATE_EXP", direction: PacketDirection::ServerToClient, description: "Atualização da barra de experiência (XP)" },
        PacketDefinition { opcode: sm::SM_ENTER_WORLD_CHECK, name: "SM_ENTER_WORLD_CHECK", direction: PacketDirection::ServerToClient, description: "Permissão para tela de carregamento" },
        PacketDefinition { opcode: sm::SM_NPC_INFO, name: "SM_NPC_INFO", direction: PacketDirection::ServerToClient, description: "Spawn de monstro ou NPC no cliente" },
        PacketDefinition { opcode: sm::SM_PLAYER_SPAWN, name: "SM_PLAYER_SPAWN", direction: PacketDirection::ServerToClient, description: "Posicionamento do jogador no mundo" },
        PacketDefinition { opcode: sm::SM_GATHERABLE_INFO, name: "SM_GATHERABLE_INFO", direction: PacketDirection::ServerToClient, description: "Spawn de objeto de coleta" },
        PacketDefinition { opcode: sm::SM_REQUEST_TELEPORT, name: "SM_REQUEST_TELEPORT", direction: PacketDirection::ServerToClient, description: "Teleporte e posicionamento no mundo (22 bytes)" },
        PacketDefinition { opcode: sm::SM_POSITION_SELF, name: "SM_POSITION_SELF", direction: PacketDirection::ServerToClient, description: "Correção forçada de coordenadas (Rollback)" },
        PacketDefinition { opcode: sm::SM_DELETE, name: "SM_DELETE", direction: PacketDirection::ServerToClient, description: "Remoção de objeto que saiu da visão" },
        PacketDefinition { opcode: sm::SM_MESSAGE, name: "SM_MESSAGE", direction: PacketDirection::ServerToClient, description: "Entrega de texto nos canais de chat" },
        PacketDefinition { opcode: sm::SM_SYSTEM_MESSAGE, name: "SM_SYSTEM_MESSAGE", direction: PacketDirection::ServerToClient, description: "Mensagem do sistema pré-traduzida" },
        PacketDefinition { opcode: sm::SM_INVENTORY_INFO, name: "SM_INVENTORY_INFO", direction: PacketDirection::ServerToClient, description: "Carga de itens da Cube no login" },
        PacketDefinition { opcode: sm::SM_PLAYER_INFO, name: "SM_PLAYER_INFO", direction: PacketDirection::ServerToClient, description: "Spawn de outro jogador com equipamentos" },
        PacketDefinition { opcode: sm::SM_CASTSPELL, name: "SM_CASTSPELL", direction: PacketDirection::ServerToClient, description: "Animação de conjuração de habilidade" },
        PacketDefinition { opcode: sm::SM_UPDATE_PLAYER_APPEARANCE, name: "SM_UPDATE_PLAYER_APPEARANCE", direction: PacketDirection::ServerToClient, description: "Troca visual de armaduras e armas" },
        PacketDefinition { opcode: sm::SM_EMOTION, name: "SM_EMOTION", direction: PacketDirection::ServerToClient, description: "Animação de asas, emotes e posturas" },
        PacketDefinition { opcode: sm::SM_CASTSPELL_RESULT, name: "SM_CASTSPELL_RESULT", direction: PacketDirection::ServerToClient, description: "Aplicação de dano, cura ou debuffs" },
        PacketDefinition { opcode: sm::SM_SKILL_LIST, name: "SM_SKILL_LIST", direction: PacketDirection::ServerToClient, description: "Catálogo de habilidades conhecidas" },
        PacketDefinition { opcode: sm::SM_ABNORMAL_STATE, name: "SM_ABNORMAL_STATE", direction: PacketDirection::ServerToClient, description: "Buffs, debuffs e status anormais" },
        PacketDefinition { opcode: sm::SM_SKILL_COOLDOWN, name: "SM_SKILL_COOLDOWN", direction: PacketDirection::ServerToClient, description: "Recargas ativas de habilidades" },
        PacketDefinition { opcode: sm::SM_MOVE, name: "SM_MOVE", direction: PacketDirection::ServerToClient, description: "Sincronização de movimento no mundo" },
        PacketDefinition { opcode: sm::SM_DIALOG_WINDOW, name: "SM_DIALOG_WINDOW", direction: PacketDirection::ServerToClient, description: "Janela HTML de diálogo com NPC" },
        PacketDefinition { opcode: sm::SM_WEATHER, name: "SM_WEATHER", direction: PacketDirection::ServerToClient, description: "Sincronização de clima e efeitos visuais" },
        PacketDefinition { opcode: sm::SM_QUEST_LIST, name: "SM_QUEST_LIST", direction: PacketDirection::ServerToClient, description: "Lista de missões ativas e completadas" },
        PacketDefinition { opcode: sm::SM_GUILD_INFO, name: "SM_GUILD_INFO", direction: PacketDirection::ServerToClient, description: "Informações principais da legião/guild" },
        PacketDefinition { opcode: sm::SM_BUDDY_LIST, name: "SM_BUDDY_LIST", direction: PacketDirection::ServerToClient, description: "Lista de amigos adicionados com status online" },
        PacketDefinition { opcode: sm::S_SA_ACCOUNT_ITEM_NOTI, name: "S_SA_ACCOUNT_ITEM_NOTI", direction: PacketDirection::ServerToClient, description: "Destrava essencial do lobby de personagens" },
        PacketDefinition { opcode: sm::SM_GUILD_MEMBER_INFO, name: "SM_GUILD_MEMBER_INFO", direction: PacketDirection::ServerToClient, description: "Detalhes de um membro da legião" },
        PacketDefinition { opcode: sm::SM_MAIL, name: "SM_MAIL", direction: PacketDirection::ServerToClient, description: "Lista de cartas e mensagens da caixa de correio" },
        PacketDefinition { opcode: sm::SM_WIND_PATH_RESULT, name: "SM_WIND_PATH_RESULT", direction: PacketDirection::ServerToClient, description: "Rota pré-calculada de voo em corrente de vento" },
        PacketDefinition { opcode: sm::SM_WIND_STATE_INFO, name: "SM_WIND_STATE_INFO", direction: PacketDirection::ServerToClient, description: "Confirmação de estado em corrente de vento" },
        PacketDefinition { opcode: sm::SM_PARTY_MATCH, name: "SM_PARTY_MATCH", direction: PacketDirection::ServerToClient, description: "Matchmaking de grupo ou busca de membros" },
        PacketDefinition { opcode: sm::SM_USER_SELL_HISTORY_LIST, name: "SM_USER_SELL_HISTORY_LIST", direction: PacketDirection::ServerToClient, description: "Histórico de itens vendidos recentemente (Buyback)" },
        PacketDefinition { opcode: sm::SM_GUILD_EMBLEM_IMG_DATA, name: "SM_GUILD_EMBLEM_IMG_DATA", direction: PacketDirection::ServerToClient, description: "Fragmento do arquivo PNG do emblema da legião" },
        PacketDefinition { opcode: sm::SM_SKILL_PENALTY_STATUS_OTHER, name: "SM_SKILL_PENALTY_STATUS_OTHER", direction: PacketDirection::ServerToClient, description: "Penalidade e cooldown de habilidade" },
        PacketDefinition { opcode: sm::SM_ALLIANCE_INFO, name: "SM_ALLIANCE_INFO", direction: PacketDirection::ServerToClient, description: "Informações da aliança de múltiplos grupos" },
        PacketDefinition { opcode: sm::SM_ALLIANCE_MEMBER_INFO, name: "SM_ALLIANCE_MEMBER_INFO", direction: PacketDirection::ServerToClient, description: "Status de membro participante da aliança" },
        PacketDefinition { opcode: sm::SM_STORE_SALE_INFO, name: "SM_STORE_SALE_INFO", direction: PacketDirection::ServerToClient, description: "Confirmação e resultado de compra/venda em loja" },
        PacketDefinition { opcode: sm::SM_GLOBAL_TRADE_LIST, name: "SM_GLOBAL_TRADE_LIST", direction: PacketDirection::ServerToClient, description: "Catálogo de ofertas disponíveis no broker" },
        PacketDefinition { opcode: sm::SM_GLOBAL_TRADE_COMMIT, name: "SM_GLOBAL_TRADE_COMMIT", direction: PacketDirection::ServerToClient, description: "Confirmação de transação no broker" },
        PacketDefinition { opcode: sm::SM_GLOBAL_TRADE_SALESLOG, name: "SM_GLOBAL_TRADE_SALESLOG", direction: PacketDirection::ServerToClient, description: "Histórico de preços e vendas recentes no broker" },
        PacketDefinition { opcode: sm::SM_GLOBAL_TRADE_STATE, name: "SM_GLOBAL_TRADE_STATE", direction: PacketDirection::ServerToClient, description: "Estado geral de transações do jogador no broker" },
        PacketDefinition { opcode: sm::SM_GLOBAL_TRADE_HISTORY, name: "SM_GLOBAL_TRADE_HISTORY", direction: PacketDirection::ServerToClient, description: "Histórico de compras e vendas pessoais no broker" },
        PacketDefinition { opcode: sm::SM_GUILD_DONATION, name: "SM_GUILD_DONATION", direction: PacketDirection::ServerToClient, description: "Informações de doação da legião" },
        PacketDefinition { opcode: sm::SM_USER_GUILD_DONATION, name: "SM_USER_GUILD_DONATION", direction: PacketDirection::ServerToClient, description: "Estado de doações diárias do jogador" },
        PacketDefinition { opcode: sm::SM_USER_GUILD_DONATION_LIST, name: "SM_USER_GUILD_DONATION_LIST", direction: PacketDirection::ServerToClient, description: "Lista de doações efetuadas" },
    ];
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn verify_critical_client_and_server_opcodes() {
        assert_eq!(cm::CM_VERSION_CHECK, 0x00);
        assert_eq!(cm::CM_QUIT, 0x03);
        assert_eq!(cm::CM_CHECK_NICKNAME, 0x0D);
        assert_eq!(cm::CM_ATTACK, 0x20);
        assert_eq!(cm::CM_MOVE, 0x30);
        assert_eq!(cm::CM_GLOBAL_TRADE_REGISTER, 0x0100);

        assert_eq!(sm::SM_VERSION_CHECK, 0x00);
        assert_eq!(sm::SM_STATUPDATE_HP, 0x03);
        assert_eq!(sm::SM_REQUEST_TELEPORT, 0x14);
        assert_eq!(sm::SM_INVENTORY_INFO, 0x1A);
        assert_eq!(sm::SM_GLOBAL_TRADE_LIST, 0x013C);
    }
}

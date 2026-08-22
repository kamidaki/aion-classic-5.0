//! Dicionário Exaustivo de Opcodes e Mapeamento de Pacotes CM e SM - Aion Classic 4.5

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

pub struct PacketRegistry;

impl PacketRegistry {
    /// Lista de todos os opcodes CM (Cliente -> Servidor) mapeados
    pub const CLIENT_PACKETS: &'static [PacketDefinition] = &[
        PacketDefinition { opcode: 0x00, name: "CM_VERSION_CHECK", direction: PacketDirection::ClientToServer, description: "Handshake de versão e chaves de criptografia" },
        PacketDefinition { opcode: 0x02, name: "CM_DISCONNECT", direction: PacketDirection::ClientToServer, description: "Notificação de desconexão do cliente" },
        PacketDefinition { opcode: 0x03, name: "CM_QUIT", direction: PacketDirection::ClientToServer, description: "Retorno para a tela de seleção de personagens" },
        PacketDefinition { opcode: 0x04, name: "CM_DELETE_CHARACTER", direction: PacketDirection::ClientToServer, description: "Solicitação de deleção de personagem" },
        PacketDefinition { opcode: 0x05, name: "CM_REVIVE", direction: PacketDirection::ClientToServer, description: "Ressurreição no obelisco ou kisk" },
        PacketDefinition { opcode: 0x06, name: "CM_RECONNECT_AUTH", direction: PacketDirection::ClientToServer, description: "Reconexão ao servidor de autenticação" },
        PacketDefinition { opcode: 0x08, name: "CM_ENTER_WORLD", direction: PacketDirection::ClientToServer, description: "Entrada no mundo com o personagem selecionado" },
        PacketDefinition { opcode: 0x09, name: "CM_LEVEL_READY", direction: PacketDirection::ClientToServer, description: "Notificação de renderização do mapa 3D concluída" },
        PacketDefinition { opcode: 0x0B, name: "CM_CHARACTER_LIST", direction: PacketDirection::ClientToServer, description: "Requisição da lista de personagens da conta" },
        PacketDefinition { opcode: 0x0C, name: "CM_CREATE_CHARACTER", direction: PacketDirection::ClientToServer, description: "Criação de novo personagem e personalização" },
        PacketDefinition { opcode: 0x0D, name: "CM_CHECK_NICKNAME", direction: PacketDirection::ClientToServer, description: "Verificação de disponibilidade de nome" },
        PacketDefinition { opcode: 0x0E, name: "CM_CAPTCHA", direction: PacketDirection::ClientToServer, description: "Validação de captcha anti-bot" },
        PacketDefinition { opcode: 0x12, name: "CM_TIME_CHECK", direction: PacketDirection::ClientToServer, description: "Sincronização de relógio de alta precisão" },
        PacketDefinition { opcode: 0x13, name: "CM_GATHER", direction: PacketDirection::ClientToServer, description: "Extração de vitalidade ou éter" },
        PacketDefinition { opcode: 0x15, name: "CM_PET_EMOTE", direction: PacketDirection::ClientToServer, description: "Interação e carinho com mascote" },
        PacketDefinition { opcode: 0x16, name: "CM_PET", direction: PacketDirection::ClientToServer, description: "Spawn, despawn e bolsa de pet" },
        PacketDefinition { opcode: 0x1B, name: "CM_CHAT_MESSAGE_PUBLIC", direction: PacketDirection::ClientToServer, description: "Mensagem enviada no chat público" },
        PacketDefinition { opcode: 0x1C, name: "CM_CHAT_MESSAGE_WHISPER", direction: PacketDirection::ClientToServer, description: "Mensagem privada enviada a outro jogador" },
        PacketDefinition { opcode: 0x1F, name: "CM_TARGET_SELECT", direction: PacketDirection::ClientToServer, description: "Seleção de alvo com mouse ou Tab" },
        PacketDefinition { opcode: 0x20, name: "CM_ATTACK", direction: PacketDirection::ClientToServer, description: "Ataque físico automático continuo" },
        PacketDefinition { opcode: 0x21, name: "CM_CASTSPELL", direction: PacketDirection::ClientToServer, description: "Conjuração de magia ou técnica especial" },
        PacketDefinition { opcode: 0x25, name: "CM_USE_ITEM", direction: PacketDirection::ClientToServer, description: "Consumo de poção, comida ou pergaminho" },
        PacketDefinition { opcode: 0x26, name: "CM_EQUIP_ITEM", direction: PacketDirection::ClientToServer, description: "Equipar ou desequipar item" },
        PacketDefinition { opcode: 0x2B, name: "CM_EMOTION", direction: PacketDirection::ClientToServer, description: "Emotes, asas abertas, sentar ou pular" },
        PacketDefinition { opcode: 0x2C, name: "CM_PING", direction: PacketDirection::ClientToServer, description: "Heartbeat de conexão ativa" },
        PacketDefinition { opcode: 0x30, name: "CM_MOVE", direction: PacketDirection::ClientToServer, description: "Vetor de deslocamento contínuo" },
        PacketDefinition { opcode: 0x34, name: "CM_SHOW_DIALOG", direction: PacketDirection::ClientToServer, description: "Abertura de diálogo com NPC" },
        PacketDefinition { opcode: 0x36, name: "CM_DIALOG_SELECT", direction: PacketDirection::ClientToServer, description: "Seleção de opção em diálogo HTML" },
        PacketDefinition { opcode: 0x46, name: "CM_WINDSTREAM", direction: PacketDirection::ClientToServer, description: "Navegação em rota de fluxo de vento" },
        PacketDefinition { opcode: 0x60, name: "CM_CRAFT", direction: PacketDirection::ClientToServer, description: "Fabricação de item por receita de artesanato" },
        PacketDefinition { opcode: 0x75, name: "CM_REGISTER_AUTOGROUP", direction: PacketDirection::ClientToServer, description: "Entrada na fila de matchmaking de arena" },
    ];

    /// Lista de todos os opcodes SM (Servidor -> Cliente) mapeados
    pub const SERVER_PACKETS: &'static [PacketDefinition] = &[
        PacketDefinition { opcode: 0x00, name: "SM_VERSION_CHECK", direction: PacketDirection::ServerToClient, description: "Resposta de versão e chave de sessão" },
        PacketDefinition { opcode: 0x01, name: "SM_STATS_INFO", direction: PacketDirection::ServerToClient, description: "Atributos, defesas e resistências do jogador" },
        PacketDefinition { opcode: 0x03, name: "SM_STATUPDATE_HP", direction: PacketDirection::ServerToClient, description: "Atualização de HP do jogador local" },
        PacketDefinition { opcode: 0x04, name: "SM_STATUPDATE_MP", direction: PacketDirection::ServerToClient, description: "Atualização de MP do jogador local" },
        PacketDefinition { opcode: 0x05, name: "SM_ATTACK_STATUS", direction: PacketDirection::ServerToClient, description: "Atualização de HP de outras entidades no mundo" },
        PacketDefinition { opcode: 0x06, name: "SM_STATUPDATE_DP", direction: PacketDirection::ServerToClient, description: "Atualização de Pontos Divinos (DP)" },
        PacketDefinition { opcode: 0x08, name: "SM_STATUPDATE_EXP", direction: PacketDirection::ServerToClient, description: "Atualização da barra de experiência (XP)" },
        PacketDefinition { opcode: 0x0D, name: "SM_ENTER_WORLD_CHECK", direction: PacketDirection::ServerToClient, description: "Permissão para tela de carregamento" },
        PacketDefinition { opcode: 0x0E, name: "SM_NPC_INFO", direction: PacketDirection::ServerToClient, description: "Spawn de monstro ou NPC no cliente" },
        PacketDefinition { opcode: 0x0F, name: "SM_PLAYER_SPAWN", direction: PacketDirection::ServerToClient, description: "Posicionamento do jogador no mundo" },
        PacketDefinition { opcode: 0x11, name: "SM_GATHERABLE_INFO", direction: PacketDirection::ServerToClient, description: "Spawn de objeto de coleta" },
        PacketDefinition { opcode: 0x15, name: "SM_POSITION_SELF", direction: PacketDirection::ServerToClient, description: "Correção forçada de coordenadas (Rollback)" },
        PacketDefinition { opcode: 0x16, name: "SM_DELETE", direction: PacketDirection::ServerToClient, description: "Remoção de objeto que saiu da visão" },
        PacketDefinition { opcode: 0x18, name: "SM_MESSAGE", direction: PacketDirection::ServerToClient, description: "Entrega de texto nos canais de chat" },
        PacketDefinition { opcode: 0x19, name: "SM_SYSTEM_MESSAGE", direction: PacketDirection::ServerToClient, description: "Mensagem do sistema pré-traduzida" },
        PacketDefinition { opcode: 0x1A, name: "SM_INVENTORY_INFO", direction: PacketDirection::ServerToClient, description: "Carga de itens da Cube no login" },
        PacketDefinition { opcode: 0x20, name: "SM_PLAYER_INFO", direction: PacketDirection::ServerToClient, description: "Spawn de outro jogador com equipamentos" },
        PacketDefinition { opcode: 0x21, name: "SM_CASTSPELL", direction: PacketDirection::ServerToClient, description: "Animação de conjuração de habilidade" },
        PacketDefinition { opcode: 0x24, name: "SM_UPDATE_PLAYER_APPEARANCE", direction: PacketDirection::ServerToClient, description: "Troca visual de armaduras e armas" },
        PacketDefinition { opcode: 0x25, name: "SM_EMOTION", direction: PacketDirection::ServerToClient, description: "Animação de asas, emotes e posturas" },
        PacketDefinition { opcode: 0x2B, name: "SM_CASTSPELL_RESULT", direction: PacketDirection::ServerToClient, description: "Aplicação de dano, cura ou debuffs" },
        PacketDefinition { opcode: 0x2C, name: "SM_SKILL_LIST", direction: PacketDirection::ServerToClient, description: "Catálogo de habilidades conhecidas" },
        PacketDefinition { opcode: 0x31, name: "SM_ABNORMAL_STATE", direction: PacketDirection::ServerToClient, description: "Buffs, debuffs e status anormais" },
        PacketDefinition { opcode: 0x33, name: "SM_SKILL_COOLDOWN", direction: PacketDirection::ServerToClient, description: "Recargas ativas de habilidades" },
        PacketDefinition { opcode: 0x37, name: "SM_MOVE", direction: PacketDirection::ServerToClient, description: "Sincronização de movimento no mundo" },
        PacketDefinition { opcode: 0x3C, name: "SM_DIALOG_WINDOW", direction: PacketDirection::ServerToClient, description: "Janela HTML de diálogo com NPC" },
        PacketDefinition { opcode: 0x43, name: "SM_WEATHER", direction: PacketDirection::ServerToClient, description: "Sincronização de clima e efeitos visuais" },
        PacketDefinition { opcode: 0x47, name: "SM_QUEST_LIST", direction: PacketDirection::ServerToClient, description: "Lista de missões ativas e completadas" },
        PacketDefinition { opcode: 0x8B, name: "S_SA_ACCOUNT_ITEM_NOTI", direction: PacketDirection::ServerToClient, description: "Destrava essencial do lobby de personagens" },
    ];

    pub fn find_client_packet(opcode: u16) -> Option<&'static PacketDefinition> {
        Self::CLIENT_PACKETS.iter().find(|p| p.opcode == opcode)
    }

    pub fn find_server_packet(opcode: u16) -> Option<&'static PacketDefinition> {
        Self::SERVER_PACKETS.iter().find(|p| p.opcode == opcode)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn verify_critical_client_and_server_opcodes() {
        // Handshake
        assert_eq!(PacketRegistry::find_client_packet(0x00).unwrap().name, "CM_VERSION_CHECK");
        assert_eq!(PacketRegistry::find_server_packet(0x00).unwrap().name, "SM_VERSION_CHECK");

        // Movement
        assert_eq!(PacketRegistry::find_client_packet(0x30).unwrap().name, "CM_MOVE");
        assert_eq!(PacketRegistry::find_server_packet(0x37).unwrap().name, "SM_MOVE");

        // Combat
        assert_eq!(PacketRegistry::find_client_packet(0x20).unwrap().name, "CM_ATTACK");
        assert_eq!(PacketRegistry::find_client_packet(0x21).unwrap().name, "CM_CASTSPELL");
        assert_eq!(PacketRegistry::find_server_packet(0x2B).unwrap().name, "SM_CASTSPELL_RESULT");

        // Critical Lobby Unlocker
        assert_eq!(PacketRegistry::find_server_packet(0x8B).unwrap().name, "S_SA_ACCOUNT_ITEM_NOTI");
    }
}

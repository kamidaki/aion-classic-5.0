//! Suíte de Testes do Subsistema de Rede (Network)

#[cfg(test)]
pub mod tests {
    use std::time::Instant;
    use crate::network::aion::clientpackets::*;
    use crate::network::aion::serverpackets::*;
    use crate::network::aion_connection::{AionConnection, ConnectionState};
    use crate::network::banned_mac_manager::BannedMacManager;
    use crate::network::opcodes::*;
    use crate::network::packet_flood_filter::PacketFloodFilter;
    use crate::network::packet_handler::AionPacketHandler;
    use crate::network::system_message_id::SystemMessageId;

    #[test]
    fn test_aion_connection_lifecycle() {
        let mut conn = AionConnection::new(1);
        assert_eq!(conn.state, ConnectionState::Connected);
        assert!(!conn.is_in_game());

        conn.set_authed(100, [1, 2, 3, 4, 5, 6, 7, 8]);
        assert_eq!(conn.state, ConnectionState::Authed);

        conn.set_in_game(1001);
        assert_eq!(conn.state, ConnectionState::InGame);
        assert!(conn.is_in_game());

        conn.close();
        assert_eq!(conn.state, ConnectionState::Closed);
    }

    #[test]
    fn test_packet_handler_state_gate() {
        let mut conn = AionConnection::new(1);

        // No estado Connected, apenas login/auth é aceito
        assert!(AionPacketHandler::can_handle(0x00E4, &conn)); // Version Check / Auth
        assert!(!AionPacketHandler::can_handle(0x0020, &conn)); // CM_ATTACK bloqueado

        conn.set_authed(100, [0u8; 8]);
        assert!(AionPacketHandler::can_handle(0x00C7, &conn)); // Create char permitido

        conn.set_in_game(1001);
        assert!(AionPacketHandler::can_handle(0x0020, &conn)); // CM_ATTACK permitido em jogo
    }

    #[test]
    fn test_banned_mac_manager() {
        let mut mgr = BannedMacManager::new();
        assert!(!mgr.is_banned("AA:BB:CC:DD:EE:FF"));

        mgr.ban_mac("AA:BB:CC:DD:EE:FF");
        assert!(mgr.is_banned("aa:bb:cc:dd:ee:ff"));

        assert!(mgr.unban_mac("AA:BB:CC:DD:EE:FF"));
        assert!(!mgr.is_banned("AA:BB:CC:DD:EE:FF"));
    }

    #[test]
    fn test_packet_flood_filter() {
        let mut filter = PacketFloodFilter::new(5);
        for _ in 0..5 {
            assert!(filter.verify_packet());
        }
        // 6º pacote no mesmo segundo é bloqueado
        assert!(!filter.verify_packet());
    }

    #[test]
    fn test_system_message_ids() {
        assert_eq!(SystemMessageId::WelcomeToAion.id(), 1300000);
        assert_eq!(SystemMessageId::InstanceEntryDenied.id(), 1400360);
    }

    #[test]
    fn test_individual_packet_modules() {
        // Testa a instanciação direta de pacotes individuais (1 arquivo por pacote)
        let cm_atk = CmAttack {
            target_id: 100,
            attack_type: 1,
            time: 50,
        };
        assert_eq!(cm_atk.target_id, 100);

        let sm_hp = SmHitPoint {
            cur_hp: 5000,
            max_hp: 5000,
        };
        assert_eq!(sm_hp.cur_hp, 5000);

        let sm_key = SmKey {
            session_key: [1, 2, 3, 4, 5, 6, 7, 8],
        };
        assert_eq!(sm_key.session_key[0], 1);
    }
}

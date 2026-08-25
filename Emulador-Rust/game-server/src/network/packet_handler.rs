//! Despachante e Roteador Central de Pacotes (AionPacketHandler - Padrão Java Aion Classic 2.8 / 4.5)

use crate::network::aion_connection::AionConnection;

pub struct AionPacketHandler;

impl AionPacketHandler {
    /// Valida se o opcode do pacote é permitido no estado atual da conexão
    pub fn can_handle(opcode: u16, connection: &AionConnection) -> bool {
        use crate::network::aion_connection::ConnectionState;

        match connection.state {
            ConnectionState::Connected => {
                // Apenas pacotes de autenticação e verificação de versão permitidos
                matches!(opcode, 0x00E4 | 0x00E7 | 0x0113 | 0x00D9)
            }
            ConnectionState::Authed => {
                // Pacotes no lobby / seleção de personagens
                matches!(
                    opcode,
                    0x00E4 | 0x00E7 | 0x00E8 | 0x00C7 | 0x00BA | 0x00E9 | 0x00EC | 0x00ED | 0x00EE
                )
            }
            ConnectionState::InGame => {
                // Em jogo, todos os pacotes válidos são aceitos
                true
            }
            ConnectionState::Closed => false,
        }
    }
}

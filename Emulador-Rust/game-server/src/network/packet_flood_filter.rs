//! Filtro Anti-Flood de Pacotes de Rede (PacketFloodFilter - Padrão Java Aion Classic 2.8 / 4.5)

use std::time::Instant;

#[derive(Debug, Clone)]
pub struct PacketFloodFilter {
    max_packets_per_sec: u32,
    packet_count: u32,
    last_reset: Instant,
}

impl Default for PacketFloodFilter {
    fn default() -> Self {
        Self::new(100) // Padrão: máx 100 pacotes por segundo
    }
}

impl PacketFloodFilter {
    pub fn new(max_packets_per_sec: u32) -> Self {
        Self {
            max_packets_per_sec,
            packet_count: 0,
            last_reset: Instant::now(),
        }
    }

    /// Retorna true se o pacote for aceito, ou false se o limite de flood foi excedido
    pub fn verify_packet(&mut self) -> bool {
        let now = Instant::now();
        if now.duration_since(self.last_reset).as_secs() >= 1 {
            self.last_reset = now;
            self.packet_count = 0;
        }

        self.packet_count += 1;
        self.packet_count <= self.max_packets_per_sec
    }
}

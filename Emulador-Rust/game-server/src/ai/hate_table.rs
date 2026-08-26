//! Tabela de Ódio e Priorização de Alvos em Combate (Hate Table)

use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct HateEntry {
    pub entity_id: u32,
    pub hate_points: i32,
}

#[derive(Debug, Clone, Default)]
pub struct HateTable {
    pub entries: HashMap<u32, HateEntry>,
}

impl HateTable {
    pub fn new() -> Self {
        Self {
            entries: HashMap::new(),
        }
    }

    /// Adiciona dano direto ao ódio (1 dano = 1 ponto de hate)
    pub fn add_damage_hate(&mut self, entity_id: u32, damage: i32) {
        let entry = self.entries.entry(entity_id).or_insert(HateEntry {
            entity_id,
            hate_points: 0,
        });
        entry.hate_points += damage.max(1);
    }

    /// Adiciona ódio de cura de aliados (1 cura = 0.5 ponto de hate)
    pub fn add_heal_hate(&mut self, healer_id: u32, heal_amount: i32) {
        let entry = self.entries.entry(healer_id).or_insert(HateEntry {
            entity_id: healer_id,
            hate_points: 0,
        });
        entry.hate_points += (heal_amount as f32 * 0.5) as i32;
    }

    /// Adiciona provocação direta / Taunt instantâneo
    pub fn add_taunt_hate(&mut self, taunter_id: u32, taunt_amount: i32) {
        let entry = self.entries.entry(taunter_id).or_insert(HateEntry {
            entity_id: taunter_id,
            hate_points: 0,
        });
        entry.hate_points += taunt_amount;
    }

    /// Retorna o ID do jogador com o maior ódio acumulado
    pub fn get_highest_target(&self) -> Option<u32> {
        self.entries
            .values()
            .max_by_key(|e| e.hate_points)
            .map(|e| e.entity_id)
    }

    /// Remove um alvo específico (ex: quando morre ou usa Feign Death/Hide)
    pub fn remove_target(&mut self, entity_id: u32) {
        self.entries.remove(&entity_id);
    }

    /// Limpa toda a tabela de ódio (ao dar leash/resetar)
    pub fn clear(&mut self) {
        self.entries.clear();
    }

    pub fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }
}

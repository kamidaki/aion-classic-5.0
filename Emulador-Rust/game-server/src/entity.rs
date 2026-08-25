use std::collections::HashMap;

use crate::{
    character::{Character, Hp},
    data::npc,
    engine::{
        damage::{Hit, Type},
        Coord,
    },
    message::server as s,
    TICK_RATE,
};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AiState {
    Idle,
    Patrol,
    Aggro,
    Combat,
    Return,
    Dead,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BossPhase {
    Phase1_Normal,
    Phase2_Adds,
    Phase3_AoECast,
    Phase4_Enrage,
}

#[derive(Debug, Clone)]
pub struct BossAiController {
    pub current_phase: BossPhase,
    pub adds_spawned: bool,
    pub aoe_casted: bool,
    pub is_enraged: bool,
    pub damage_multiplier: f32,
    pub attack_speed_multiplier: f32,
}

impl Default for BossAiController {
    fn default() -> Self {
        Self {
            current_phase: BossPhase::Phase1_Normal,
            adds_spawned: false,
            aoe_casted: false,
            is_enraged: false,
            damage_multiplier: 1.0,
            attack_speed_multiplier: 1.0,
        }
    }
}

impl BossAiController {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn update_phase(&mut self, current_hp: i32, max_hp: i32) -> Option<BossPhase> {
        let hp_percent = (current_hp as f32 / max_hp.max(1) as f32) * 100.0;
        let old_phase = self.current_phase;

        if hp_percent <= 25.0 {
            self.current_phase = BossPhase::Phase4_Enrage;
            self.is_enraged = true;
            self.damage_multiplier = 2.0; // 100% de aumento de dano
            self.attack_speed_multiplier = 1.5; // 50% de velocidade adicional
        } else if hp_percent <= 50.0 {
            self.current_phase = BossPhase::Phase3_AoECast;
        } else if hp_percent <= 75.0 {
            self.current_phase = BossPhase::Phase2_Adds;
        } else {
            self.current_phase = BossPhase::Phase1_Normal;
        }

        if self.current_phase != old_phase {
            Some(self.current_phase)
        } else {
            None
        }
    }
}

#[derive(Debug, Clone)]
pub struct DropItem {
    pub item_id: u32,
    pub count: u32,
    pub chance_percent: f32,
}

#[derive(Debug)]
pub struct Entity {
    id: u32,
    target_id: Option<u32>,
    location: Coord,
    spawn_location: Coord,
    npc_id: u32,
    npc_name: u32,
    level: u16,
    pub hp: Hp,
    pub max_hp: i32,
    attack_sequence: u8,
    attack_speed: f32,
    attack_cooldown: f32,
    pub state: AiState,
    pub leash_range: f32,
    pub aggro_range: f32,
    pub hate_table: HashMap<u32, u32>,
    pub drop_table: Vec<DropItem>,
    pub boss_ai: Option<BossAiController>,
}

impl Entity {
    pub fn new(
        id: u32,
        location: Coord,
        npc_id: npc::Id,
        npc_name: npc::Name,
    ) -> Self {
        Self::novo(id, location, npc_id as u32, npc_name as u32)
    }

    pub fn novo(
        id: u32,
        location: Coord,
        npc_id: u32,
        npc_name: u32,
    ) -> Self {
        Self {
            id,
            location,
            spawn_location: location,
            npc_id,
            npc_name,
            target_id: None,
            attack_speed: const { 1.750 * TICK_RATE },
            attack_cooldown: const { 1.750 * TICK_RATE },
            attack_sequence: 0,
            level: 0x0D,
            hp: Hp::new(1817),
            max_hp: 1817,
            state: AiState::Idle,
            leash_range: 50.0,
            aggro_range: 15.0,
            hate_table: HashMap::new(),
            drop_table: vec![
                DropItem { item_id: 182400001, count: 150, chance_percent: 100.0 }, // Kinah
                DropItem { item_id: 160000001, count: 2, chance_percent: 50.0 },    // Potion
            ],
            boss_ai: None,
        }
    }

    pub fn is_dead(&self) -> bool {
        self.hp.current() <= 0 || self.state == AiState::Dead
    }

    pub fn is_alive(&self) -> bool {
        self.hp.current() > 0 && self.state != AiState::Dead
    }

    /// Retorna o alvo com maior nível de ódio acumulado
    pub fn get_top_threat(&self) -> Option<u32> {
        self.hate_table
            .iter()
            .max_by_key(|&(_, hate)| hate)
            .map(|(&id, _)| id)
    }

    /// Força o alvo para um jogador específico inserindo ódio superior (Taunt)
    pub fn taunt(&mut self, character_id: u32, bonus_hate: u32) {
        let max_current_hate = self.hate_table.values().copied().max().unwrap_or(0);
        let entry = self.hate_table.entry(character_id).or_insert(0);
        *entry = max_current_hate.saturating_add(bonus_hate);
        self.target_id = Some(character_id);
        self.state = AiState::Combat;
    }

    /// Adiciona ódio (hate) à tabela de aggro
    pub fn add_hate(&mut self, character_id: u32, amount: u32) {
        let entry = self.hate_table.entry(character_id).or_insert(0);
        *entry += amount;
        if self.target_id.is_none() || self.state == AiState::Idle {
            self.target_id = Some(character_id);
            self.state = AiState::Combat;
        } else {
            self.target_id = self.get_top_threat();
        }
    }

    /// Executa tique da máquina de estados de IA
    pub fn tick_ai(&mut self, characters: &mut HashMap<u32, Character>) -> Option<Vec<Hit>> {
        if self.is_dead() {
            self.state = AiState::Dead;
            return None;
        }

        // Atualiza fases de boss caso configurado
        if let Some(ref mut boss) = self.boss_ai {
            boss.update_phase(self.hp.current(), self.max_hp);
        }

        // 1. Validação de Leash / Evasão
        if self.location.distance(&self.spawn_location) > self.leash_range {
            self.state = AiState::Return;
            self.target_id = None;
            self.hate_table.clear();
            self.location = self.spawn_location; // Retorna imediatamente ao spawn
            self.hp.update(self.max_hp); // Restaura HP total
            self.state = AiState::Idle;
            return None;
        }

        // 2. Busca de Aggro automático se estiver Idle
        if self.state == AiState::Idle {
            for (char_id, character) in characters.iter() {
                if self.location.distance(character.location()) <= self.aggro_range {
                    self.add_hate(*char_id, 10);
                    break;
                }
            }
        }

        // 3. Combate ativo
        if self.state == AiState::Combat {
            let target_id = self.target_id?;
            if let Some(target) = characters.get_mut(&target_id) {
                if target.stats.hp.current() <= 0 {
                    self.hate_table.remove(&target_id);
                    self.target_id = self.get_top_threat();
                    if self.target_id.is_none() {
                        self.state = AiState::Idle;
                    }
                    return None;
                }
                return self.attack(target);
            } else {
                self.target_id = None;
                self.state = AiState::Idle;
            }
        }

        None
    }

    pub fn attack(&mut self, character: &mut Character) -> Option<Vec<Hit>> {
        if self.attack_cooldown >= 0. {
            self.attack_cooldown -= 1.;
            return None;
        }

        if self.location.distance(character.location()) > 5. {
            return None;
        }

        let speed = if let Some(ref boss) = self.boss_ai {
            self.attack_speed / boss.attack_speed_multiplier
        } else {
            self.attack_speed
        };

        self.attack_cooldown = speed;
        Some(self.calculate_damage(character))
    }

    pub fn set_taget(&mut self, target_id: u32) -> s::NpcChangedTarget {
        self.target_id = Some(target_id);
        s::NpcChangedTarget::new(target_id, self.id)
    }

    pub fn clear_target(&mut self) {
        self.target_id = None;
        self.hate_table.clear();
    }

    fn calculate_damage(&mut self, character: &mut Character) -> Vec<Hit> {
        let base_dmg = 128;
        let dmg = if let Some(ref boss) = self.boss_ai {
            (base_dmg as f32 * boss.damage_multiplier) as i32
        } else {
            base_dmg
        };

        let hits = vec![Hit::new(dmg, Type::MainHand)];
        character.stats.hp.update(-dmg);
        self.attack_sequence = self.attack_sequence.wrapping_add(1);
        hits
    }

    /// Gera drops ao ser derrotado
    pub fn generate_loot(&self) -> Vec<(u32, u32)> {
        let mut loot = Vec::new();
        for drop in &self.drop_table {
            if drop.chance_percent >= 50.0 {
                loot.push((drop.item_id, drop.count));
            }
        }
        loot
    }

    pub fn id(&self) -> u32 {
        self.id
    }
    pub fn target_id(&self) -> Option<u32> {
        self.target_id
    }
    pub fn location(&self) -> &Coord {
        &self.location
    }
    pub fn npc_id(&self) -> u32 {
        self.npc_id
    }
    pub fn npc_name(&self) -> u32 {
        self.npc_name
    }
    pub fn level(&self) -> u16 {
        self.level
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn entity_ai_aggro_detection_and_combat() {
        let mut entity = Entity::novo(1001, Coord::new(100.0, 100.0, 0.0), 210001, 210001);
        let mut characters = HashMap::new();
        let c = Character::new(1, 1, Coord::new(105.0, 100.0, 0.0)); // 5m away
        characters.insert(1, c);

        assert_eq!(entity.state, AiState::Idle);

        // Tick AI: must detect player within 15m and enter combat
        entity.tick_ai(&mut characters);
        assert_eq!(entity.state, AiState::Combat);
        assert_eq!(entity.target_id, Some(1));
    }

    #[test]
    fn entity_leash_and_reset_recovery() {
        let mut entity = Entity::novo(1001, Coord::new(100.0, 100.0, 0.0), 210001, 210001);
        entity.hp.update(-500); // Take damage
        entity.state = AiState::Combat;
        entity.target_id = Some(1);

        // Move entity far away (>50m leash)
        entity.location = Coord::new(200.0, 100.0, 0.0);

        let mut characters = HashMap::new();
        entity.tick_ai(&mut characters);

        assert_eq!(entity.state, AiState::Idle, "Entidade deve voltar ao estado Idle apos leash");
        assert_eq!(entity.location.x(), 100.0, "Entidade deve ser reposicionada no spawn");
        assert_eq!(entity.target_id, None, "Aggro deve ser resetado");
    }

    #[test]
    fn entity_loot_generation_on_death() {
        let entity = Entity::novo(1001, Coord::new(100.0, 100.0, 0.0), 210001, 210001);
        let loot = entity.generate_loot();
        assert!(!loot.is_empty(), "Monstro deve gerar tabela de loot");
        assert!(loot.iter().any(|(id, _)| *id == 182400001), "Kinah garantida no loot");
    }

    #[test]
    fn test_hate_table_taunt_and_threat_modifiers() {
        let mut entity = Entity::novo(1001, Coord::new(100.0, 100.0, 0.0), 210001, 210001);
        entity.add_hate(10, 500); // Jogador 10 causou 500 de dano
        entity.add_hate(20, 300); // Jogador 20 causou 300 de dano
        assert_eq!(entity.get_top_threat(), Some(10));

        // Templário (Jogador 20) usa Taunt (+5000)
        entity.taunt(20, 5000);
        assert_eq!(entity.get_top_threat(), Some(20));
        assert_eq!(entity.target_id, Some(20));
    }

    #[test]
    fn test_boss_phase_transitions_and_enrage() {
        let mut boss = BossAiController::new();
        assert_eq!(boss.current_phase, BossPhase::Phase1_Normal);

        // HP cai para 70% -> Fase 2 (Adds)
        assert_eq!(boss.update_phase(700, 1000), Some(BossPhase::Phase2_Adds));

        // HP cai para 40% -> Fase 3 (AoE)
        assert_eq!(boss.update_phase(400, 1000), Some(BossPhase::Phase3_AoECast));

        // HP cai para 20% -> Fase 4 (Enrage com dano 2x e speed 1.5x)
        assert_eq!(boss.update_phase(200, 1000), Some(BossPhase::Phase4_Enrage));
        assert!(boss.is_enraged);
        assert_eq!(boss.damage_multiplier, 2.0);
        assert_eq!(boss.attack_speed_multiplier, 1.5);
    }
}

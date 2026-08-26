//! Gerenciador de Efeitos Ativos e Tarefas Periódicas (EffectTask - Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashMap;
use std::time::Instant;
use crate::character::Character;
use crate::entity::Entity;
use crate::skillengine::model::abnormal_state::AbnormalStateMask;
use crate::skillengine::model::effect_model::Effect;

#[derive(Debug, Default)]
pub struct EffectTaskManager {
    pub player_effects: HashMap<u32, Vec<Effect>>,
    pub entity_effects: HashMap<u32, Vec<Effect>>,
}

impl EffectTaskManager {
    pub fn new() -> Self {
        Self {
            player_effects: HashMap::new(),
            entity_effects: HashMap::new(),
        }
    }

    /// Adiciona um efeito ativo a um jogador
    pub fn add_player_effect(&mut self, player_id: u32, effect: Effect) {
        let list = self.player_effects.entry(player_id).or_default();
        // Se já existe efeito da mesma skill, renova
        list.retain(|e| e.skill_id != effect.skill_id);
        list.push(effect);
    }

    /// Adiciona um efeito ativo a um monstro/NPC
    pub fn add_entity_effect(&mut self, entity_id: u32, effect: Effect) {
        let list = self.entity_effects.entry(entity_id).or_default();
        list.retain(|e| e.skill_id != effect.skill_id);
        list.push(effect);
    }

    /// Obtém a máscara combinada de estados anormais de um jogador
    pub fn get_player_abnormal_mask(&self, player_id: u32) -> AbnormalStateMask {
        let mut mask = AbnormalStateMask::NONE;
        if let Some(list) = self.player_effects.get(&player_id) {
            for eff in list {
                if eff.is_active {
                    mask |= eff.abnormal_state;
                }
            }
        }
        mask
    }

    /// Tick periódico de efeitos ativos: processa dano/cura ao longo do tempo e remove expirados
    pub fn tick(
        &mut self,
        now: Instant,
        characters: &mut HashMap<u32, Character>,
        entities: &mut [Entity],
    ) -> Vec<(u32, u32)> {
        let mut expired_effects = Vec::new();

        // 1. Processa efeitos de jogadores
        for (player_id, effects) in self.player_effects.iter_mut() {
            let Some(character) = characters.get_mut(player_id) else {
                continue;
            };

            effects.retain(|eff| {
                if eff.is_expired(now) || !eff.is_active {
                    expired_effects.push((*player_id, eff.skill_id));
                    false
                } else {
                    // Processa tick se aplicável
                    if eff.tick_interval_ms > 0 {
                        if let Some(next_tick) = eff.next_tick_at {
                            if now >= next_tick {
                                if eff.value < 0 {
                                    character.stats.hp.update(eff.value);
                                } else if eff.value > 0 {
                                    character.stats.hp.update(eff.value);
                                }
                            }
                        }
                    }
                    true
                }
            });
        }

        // 2. Processa efeitos de monstros/NPCs
        for (entity_id, effects) in self.entity_effects.iter_mut() {
            let Some(entity) = entities.iter_mut().find(|e| e.id() == *entity_id) else {
                continue;
            };

            effects.retain(|eff| {
                if eff.is_expired(now) || !eff.is_active {
                    false
                } else {
                    if eff.tick_interval_ms > 0 {
                        if let Some(next_tick) = eff.next_tick_at {
                            if now >= next_tick {
                                entity.hp.update(-eff.value);
                            }
                        }
                    }
                    true
                }
            });
        }

        expired_effects
    }
}

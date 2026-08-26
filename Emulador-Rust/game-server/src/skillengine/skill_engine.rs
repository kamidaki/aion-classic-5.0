//! SkillEngine - Motor Central de Habilidades e Efeitos (Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashMap;
use std::time::{Duration, Instant};

use crate::character::Character;
use crate::data::ActionType;
use crate::engine::damage::CombatEngine;
use crate::entity::Entity;
use crate::message::{client as c, server as s};
use crate::skillengine::model::abnormal_state::AbnormalStateMask;
use crate::skillengine::model::chain_skills::{ActiveChainState, ChainSkill};
use crate::skillengine::model::effect_model::Effect;
use crate::skillengine::model::skill_target_slot::SkillTargetSlot;
use crate::skillengine::model::skill_template::SkillTemplate;
use crate::skillengine::model::skill_type::{SkillElement, SkillSubType, SkillType};
use crate::skillengine::task::cast_task::CastTask;
use crate::skillengine::task::effect_task::EffectTaskManager;
use crate::{Messages, ServerUpdate};

#[derive(Debug)]
pub struct SkillEngine {
    pub templates: HashMap<u32, SkillTemplate>,
    pub chain_rules: HashMap<u32, ChainSkill>,
    pub active_chains: HashMap<u32, ActiveChainState>,
    pub cooldowns: HashMap<u32, HashMap<u32, Instant>>,
    pub casting_tasks: HashMap<u32, CastTask>,
    pub effect_manager: EffectTaskManager,
}

impl Default for SkillEngine {
    fn default() -> Self {
        Self::new()
    }
}

impl SkillEngine {
    pub fn new() -> Self {
        let mut engine = Self {
            templates: HashMap::new(),
            chain_rules: HashMap::new(),
            active_chains: HashMap::new(),
            cooldowns: HashMap::new(),
            casting_tasks: HashMap::new(),
            effect_manager: EffectTaskManager::new(),
        };

        // Popula habilidades básicas universais de Aion Classic
        engine.init_default_templates();
        engine
    }

    /// Registra habilidades clássicas no catálogo padrão
    fn init_default_templates(&mut self) {
        // Ferocious Strike (Guerreiro) -> Robust Blow -> Wrathful Blow
        self.register_template(SkillTemplate::new(
            1001,
            "Ferocious Strike I",
            SkillType::Physical,
            SkillSubType::Attack,
            0,
            2000,
            2.0,
            25,
        ));
        self.register_template(SkillTemplate::new(
            1002,
            "Robust Blow I",
            SkillType::Physical,
            SkillSubType::Attack,
            0,
            2000,
            2.0,
            35,
        ));
        self.register_template(SkillTemplate::new(
            1003,
            "Wrathful Blow I",
            SkillType::Physical,
            SkillSubType::Attack,
            0,
            3000,
            2.0,
            45,
        ));
        self.register_chain_rule(ChainSkill::new(1001, 1002, 7, 1.0));
        self.register_chain_rule(ChainSkill::new(1002, 1003, 7, 1.0));

        // Flame Bolt (Mage / Sorcerer)
        self.register_template(SkillTemplate::new(
            1401,
            "Flame Bolt I",
            SkillType::Magical,
            SkillSubType::Attack,
            1500,
            1000,
            25.0,
            50,
        ));

        // Healing Light (Priest / Cleric)
        self.register_template(SkillTemplate::new(
            1501,
            "Healing Light I",
            SkillType::Magical,
            SkillSubType::Heal,
            2000,
            1000,
            25.0,
            60,
        ));

        // Hide I (Scout / Assassin)
        self.register_template(SkillTemplate::new(
            1201,
            "Hide I",
            SkillType::Physical,
            SkillSubType::Buff,
            0,
            30000,
            0.0,
            40,
        ));

        // Stone Skin (Escudo de Sorcerer)
        self.register_template(SkillTemplate::new(
            1402,
            "Stone Skin I",
            SkillType::Magical,
            SkillSubType::Buff,
            0,
            120000,
            0.0,
            80,
        ));
    }

    pub fn register_template(&mut self, template: SkillTemplate) {
        self.templates.insert(template.skill_id, template);
    }

    pub fn register_chain_rule(&mut self, chain: ChainSkill) {
        self.chain_rules.insert(chain.pre_skill_id, chain);
    }

    /// Verifica se a habilidade está em tempo de recarga (cooldown)
    pub fn is_on_cooldown(&self, player_id: u32, skill_id: u32, now: Instant) -> bool {
        if let Some(player_cds) = self.cooldowns.get(&player_id) {
            if let Some(&cd_end) = player_cds.get(&skill_id) {
                return now < cd_end;
            }
        }
        false
    }

    /// Define o tempo de recarga para uma habilidade utilizada
    pub fn set_cooldown(&mut self, player_id: u32, skill_id: u32, cooldown_ms: u32, now: Instant) {
        if cooldown_ms > 0 {
            let cd_end = now + Duration::from_millis(cooldown_ms as u64);
            self.cooldowns
                .entry(player_id)
                .or_default()
                .insert(skill_id, cd_end);
        }
    }

    /// Inicia o processo de conjuração ou executa instantaneamente
    pub fn handle_use_skill(
        &mut self,
        caster_id: u32,
        client_id: u16,
        use_skill: &c::UseSkill,
        characters: &mut HashMap<u32, Character>,
        entities: &mut [Entity],
        restrictions: &crate::restrictions::RestrictionsManager,
        messages: &mut Messages,
    ) -> Result<(), &'static str> {
        let now = Instant::now();
        let skill_id = use_skill.skill_id as u32;

        let Some(character) = characters.get_mut(&caster_id) else {
            return Err("Personagem não encontrado");
        };

        // 1. Verificação de Cooldown
        if self.is_on_cooldown(caster_id, skill_id, now) {
            return Err("Habilidade em tempo de recarga");
        }

        // 2. Verificação de Restrições Globais
        let is_self_or_aoe = use_skill.target_id == 0 || use_skill.target_id == caster_id;
        let player_state = character.to_player_state();
        let skill_info = crate::restrictions::SkillInfo {
            skill_id,
            skill_type: crate::restrictions::SkillType::Physical,
            has_evade_effect: false,
            has_resurrect_effect: false,
            is_hide_skill: false,
            is_recall_instant: false,
            is_disabled: false,
            is_enemy_target: !is_self_or_aoe,
        };

        if let Err(restriction_err) = restrictions.can_use_skill(&player_state, &skill_info) {
            println!("WARN: [SkillEngine] Restrição bloqueou uso da skill {skill_id}: {:?}", restriction_err);
            return Err("Habilidade bloqueada por restrição");
        }

        // 3. Verificação e Consumo de MP / DP
        let mp_cost = self.templates.get(&skill_id).map(|t| t.mp_cost).unwrap_or(20);
        if character.stats.mp.current() < mp_cost {
            return Err("MP insuficiente para conjurar");
        }
        character.stats.mp.update(-(mp_cost as i32));

        // 4. Execução da Habilidade
        let cooldown_ms = self.templates.get(&skill_id).map(|t| t.cooldown_ms).unwrap_or(3000);
        self.set_cooldown(caster_id, skill_id, cooldown_ms, now);

        // Se habilitar cadeia de skills (Chain)
        if let Some(chain) = self.chain_rules.get(&skill_id) {
            self.active_chains.insert(
                caster_id,
                ActiveChainState {
                    skill_id,
                    next_skill_id: chain.next_skill_id,
                    expires_at: now + Duration::from_secs(chain.time_window_secs as u64),
                },
            );
        }

        // 5. Aplicação dos Efeitos e Envio de Pacotes de Rede
        if is_self_or_aoe {
            // Auto-buff, cura ou utilitário
            let eff = s::AbnormalEffect::new(skill_id, 30000, 1);
            messages.push_direct(
                client_id,
                ServerUpdate::new(s::Message::AbnormalStatus(s::AbnormalStatus::with_effects(
                    caster_id,
                    vec![eff.clone()],
                ))),
            );
            messages.push_others(
                client_id,
                ServerUpdate::new(s::Message::AbnormalStatusOther(
                    s::AbnormalStatusOther::with_effects(caster_id, vec![eff]),
                )),
            );
            messages.push_direct(
                client_id,
                ServerUpdate::new(s::Message::SkillPenaltyStatusOther(
                    s::SkillPenaltyStatusOther::new(caster_id, skill_id, cooldown_ms),
                )),
            );

            let skill_effect = s::SkillEffect::new(caster_id, 0, 1, 0);
            messages.push_direct(
                client_id,
                ServerUpdate::new(s::Message::SkillSucceded(s::SkillSucceded::new(
                    caster_id,
                    caster_id,
                    skill_id,
                    use_skill.skill_level as u8,
                    vec![skill_effect],
                ))),
            );

            // Registra o efeito no gerenciador
            let mut active_eff = Effect::new(
                caster_id,
                caster_id,
                skill_id,
                use_skill.skill_level as u8,
                SkillTargetSlot::Buff,
                30000,
                0,
            );
            self.effect_manager.add_player_effect(caster_id, active_eff);
        } else if let Some(entity) = entities
            .iter_mut()
            .find(|e| e.id() == use_skill.target_id && e.is_alive())
        {
            // Dano físico ou mágico contra alvo hostil
            let hit = CombatEngine::calculate_physical_hit(
                character.stats.secondary.main_hand_attack,
                1.5,
                100,
                character.stats.secondary.main_hand_accuracy,
                100,
                100,
                100,
                character.stats.secondary.main_hand_crit,
                50,
                1.5,
            );
            let damage = hit.damage.max(1);
            let is_crit = if hit.ty == crate::engine::damage::Type::Critical { 1 } else { 0 };
            entity.hp.update(-damage);

            let eff = s::SkillEffect::new(entity.id(), -damage, 0, is_crit);
            messages.broadcast.extend(
                [
                    s::Message::UseSkill(s::UseSkill::new(
                        caster_id,
                        use_skill.skill_id,
                        use_skill.skill_level,
                        use_skill.target_id,
                    )),
                    s::Message::SkillSucceded(s::SkillSucceded::new(
                        caster_id,
                        use_skill.target_id,
                        skill_id,
                        use_skill.skill_level as u8,
                        vec![eff],
                    )),
                    s::Message::SkillPenaltyStatusOther(s::SkillPenaltyStatusOther::new(
                        caster_id,
                        skill_id,
                        cooldown_ms,
                    )),
                    s::Message::HitPointOther(s::HitPointOther::new(
                        entity.id(),
                        damage,
                        entity.hp.current() as u32,
                        entity.hp.max() as u32,
                        0,
                        is_crit,
                    )),
                ]
                .map(ServerUpdate::new),
            );

            if entity.is_dead() {
                messages.broadcast.extend(
                    [
                        s::Message::Action(s::Action::new(
                            entity.id(),
                            ActionType::Die,
                            character.stats.move_speed,
                            character.id(),
                        )),
                        s::Message::Loot(s::Loot::new(entity.id(), 0)),
                    ]
                    .map(ServerUpdate::new),
                );
            }
        }

        Ok(())
    }

    /// Atualização periódica: ticks de efeitos contínuos, expiração de buffs/debuffs e correntes
    pub fn tick(
        &mut self,
        now: Instant,
        characters: &mut HashMap<u32, Character>,
        entities: &mut [Entity],
    ) {
        // 1. Limpa correntes de skills expiradas
        self.active_chains.retain(|_, chain| now <= chain.expires_at);

        // 2. Processa ticks de efeitos ativos
        self.effect_manager.tick(now, characters, entities);
    }
}

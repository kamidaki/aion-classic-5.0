//! Testes Unitários e de Integração do SkillEngine (Padrão Java Aion Classic 2.8 / 4.5)

#[cfg(test)]
pub mod tests {
    use std::collections::HashMap;
    use std::time::{Duration, Instant};

    use crate::character::Character;
    use crate::engine::Coord;
    use crate::entity::Entity;
    use crate::message::client as c;
    use crate::restrictions::RestrictionsManager;
    use crate::skillengine::effect::buff_effect::BuffEffect;
    use crate::skillengine::effect::damage_effect::{DamageEffect, SpellAttackEffect};
    use crate::skillengine::effect::dispel_effect::DispelEffect;
    use crate::skillengine::effect::effect_trait::EffectTrait;
    use crate::skillengine::effect::shield_effect::ShieldEffect;
    use crate::skillengine::model::abnormal_state::AbnormalStateMask;
    use crate::skillengine::model::chain_skills::ChainSkill;
    use crate::skillengine::model::effect_model::Effect;
    use crate::skillengine::model::skill_target_slot::{DispelCategoryType, SkillTargetSlot};
    use crate::skillengine::model::skill_type::SkillElement;
    use crate::skillengine::skill_engine::SkillEngine;
    use crate::Messages;

    #[test]
    fn test_skill_engine_cooldown_and_execution() {
        let mut engine = SkillEngine::new();
        let mut characters = HashMap::new();
        let mut entities = Vec::new();
        let restrictions = RestrictionsManager::new();
        let mut messages = Messages::new();

        let char_id = 100;
        let mut character = Character::new(char_id, 1, Coord::new(100.0, 100.0, 100.0));
        character.stats.mp.update(1000);
        characters.insert(char_id, character);

        let entity = Entity::novo(200, Coord::new(101.0, 100.0, 100.0), 210001, 210001);
        entities.push(entity);

        let use_skill = c::UseSkill {
            skill_id: 1001, // Ferocious Strike
            skill_level: 1,
            target_id: 200,
            cast_type: 0,
            x: 101.0,
            y: 100.0,
            z: 100.0,
            heading: 0,
            unknown: Vec::new(),
        };

        // Primeira execução: deve ter sucesso
        let res = engine.handle_use_skill(
            char_id,
            1,
            &use_skill,
            &mut characters,
            &mut entities,
            &restrictions,
            &mut messages,
        );
        assert!(res.is_ok());

        // Segunda execução imediata: deve falhar por cooldown
        let res_cd = engine.handle_use_skill(
            char_id,
            1,
            &use_skill,
            &mut characters,
            &mut entities,
            &restrictions,
            &mut messages,
        );
        assert!(res_cd.is_err());
        assert_eq!(res_cd.unwrap_err(), "Habilidade em tempo de recarga");
    }

    #[test]
    fn test_chain_skill_flow() {
        let mut engine = SkillEngine::new();
        let now = Instant::now();

        // Registra cadeia: Skill 1001 habilita 1002 por 7s
        engine.register_chain_rule(ChainSkill::new(1001, 1002, 7, 1.0));

        let char_id = 100;
        let chain_cond = crate::skillengine::condition::chain_condition::ChainCondition::new(1001);

        // Sem skill anterior: validação falha
        assert!(chain_cond
            .validate_chain(engine.active_chains.get(&char_id), 1002, now)
            .is_err());

        // Ativa a corrente
        engine.active_chains.insert(
            char_id,
            crate::skillengine::model::chain_skills::ActiveChainState {
                skill_id: 1001,
                next_skill_id: 1002,
                expires_at: now + Duration::from_secs(7),
            },
        );

        // Com a corrente ativa: validação passa para a skill 1002
        assert!(chain_cond
            .validate_chain(engine.active_chains.get(&char_id), 1002, now)
            .is_ok());

        // Após expiração de tempo: validação falha
        let expired_time = now + Duration::from_secs(8);
        assert!(chain_cond
            .validate_chain(engine.active_chains.get(&char_id), 1002, expired_time)
            .is_err());
    }

    #[test]
    fn test_damage_and_magic_calculations() {
        let dmg_effect = DamageEffect::new(150, 1.2, 50, 20);
        let mut eff = Effect::new(1, 2, 1001, 1, SkillTargetSlot::None, 0, 0);
        let mut entity = Entity::novo(200, Coord::new(0.0, 0.0, 0.0), 210001, 210001);

        dmg_effect.apply_to_entity(&mut eff, &mut entity);
        assert!(eff.value > 0);
        assert!(entity.hp.current() < entity.hp.max());

        let magic_effect = SpellAttackEffect::new(300, SkillElement::Fire);
        let calculated_dmg = magic_effect.calculate_magic_damage(500, 100);
        assert!(calculated_dmg > 300);
    }

    #[test]
    fn test_abnormal_state_restrictions() {
        let mask = AbnormalStateMask::SILENCE | AbnormalStateMask::STUN;
        assert!(mask.cant_cast_magic());
        assert!(mask.cant_cast_physical());
        assert!(mask.cant_move());

        let sleep_mask = AbnormalStateMask::SLEEP;
        assert!(sleep_mask.break_on_damage());
    }

    #[test]
    fn test_shield_absorption() {
        let mut shield_eff = Effect::new(1, 1, 1402, 1, SkillTargetSlot::Buff, 120000, 0);
        shield_eff.shield_capacity = 500;

        // Dano de 200: completamente absorvido pelo escudo
        let leftover1 = ShieldEffect::absorb_damage(&mut shield_eff, 200);
        assert_eq!(leftover1, 0);
        assert_eq!(shield_eff.shield_capacity, 300);
        assert!(shield_eff.is_active);

        // Dano de 400: excede capacidade restante de 300, quebra o escudo e sobra 100 de dano
        let leftover2 = ShieldEffect::absorb_damage(&mut shield_eff, 400);
        assert_eq!(leftover2, 100);
        assert_eq!(shield_eff.shield_capacity, 0);
        assert!(!shield_eff.is_active);
    }

    #[test]
    fn test_dispel_effects() {
        let dispel = DispelEffect::new(DispelCategoryType::DebuffPhysical, 2, 100);
        let mut active_effects = vec![
            Effect {
                effector_id: 1,
                effected_id: 2,
                skill_id: 2001,
                skill_level: 1,
                target_slot: SkillTargetSlot::Debuff,
                dispel_category: DispelCategoryType::DebuffPhysical,
                abnormal_state: AbnormalStateMask::POISON,
                duration_ms: 30000,
                applied_at: Instant::now(),
                next_tick_at: None,
                tick_interval_ms: 0,
                value: 50,
                shield_capacity: 0,
                is_active: true,
            },
            Effect {
                effector_id: 1,
                effected_id: 2,
                skill_id: 3001,
                skill_level: 1,
                target_slot: SkillTargetSlot::Buff,
                dispel_category: DispelCategoryType::Buff,
                abnormal_state: AbnormalStateMask::NONE,
                duration_ms: 60000,
                applied_at: Instant::now(),
                next_tick_at: None,
                tick_interval_ms: 0,
                value: 20,
                shield_capacity: 0,
                is_active: true,
            },
        ];

        let removed = dispel.process_dispel(&mut active_effects);
        assert_eq!(removed.len(), 1);
        assert_eq!(removed[0], 2001);
        assert_eq!(active_effects.len(), 1);
        assert_eq!(active_effects[0].skill_id, 3001); // Buff permanece intocado
    }

    #[test]
    fn test_buff_effect_stat_modification() {
        let buff = BuffEffect {
            attack_boost: 50,
            defense_boost: 0,
            magic_boost: 100,
            speed_boost_percent: 20.0,
            duration_ms: 60000,
        };

        let mut character = Character::new(1, 1, Coord::new(0.0, 0.0, 0.0));
        let initial_attack = character.stats.secondary.main_hand_attack;
        let initial_magic_boost = character.stats.secondary.magic_boost;
        let initial_speed = character.stats.move_speed;

        let mut eff = Effect::new(1, 1, 100, 1, SkillTargetSlot::Buff, 60000, 0);

        // Aplicação do Buff
        buff.apply_to_player(&mut eff, &mut character);
        assert_eq!(character.stats.secondary.main_hand_attack, initial_attack + 50);
        assert_eq!(character.stats.secondary.magic_boost, initial_magic_boost + 100);
        assert!(character.stats.move_speed > initial_speed);

        // Fim do Buff
        buff.end_on_player(&eff, &mut character);
        assert_eq!(character.stats.secondary.main_hand_attack, initial_attack);
        assert_eq!(character.stats.secondary.magic_boost, initial_magic_boost);
    }
}

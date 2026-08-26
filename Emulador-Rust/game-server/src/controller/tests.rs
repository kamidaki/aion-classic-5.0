//! Suíte de Testes Automatizados dos Controladores (Controllers Test Suite)

use super::*;
use crate::controller::attack::{
    AggroList, AttackResult, AttackStatus, AttackUtil, CounterSkillStatus, KillList,
    PlayerAggroList,
};
use crate::controller::effect::{ActiveEffect, EffectController, PlayerEffectController};
use crate::controller::movement::{
    CreatureMoveController, MoveController, MovementMask, NpcMoveController, PetMoveController,
    PlayerMoveController, SummonMoveController,
};
use crate::controller::observer::{
    ActionObserver, AttackCalcObserver, AttackShieldObserver, DialogObserver, FlyRingObserver,
    IActor, ItemUseObserver, ObserverType, RoadObserver, ShieldObserver,
};
use crate::engine::Coord;
use std::sync::Arc;

#[test]
fn test_player_controller_lifecycle() {
    let mut player = PlayerController::new(
        1001,
        210010000,
        Coord::new(100.0, 200.0, 50.0),
        60,
        6.0,
        5000,
        3000,
        4000,
        120,
    );

    assert_eq!(player.creature.visible.is_spawned, false);
    player.on_enter_world();
    assert_eq!(player.creature.visible.is_spawned, true);

    // DP Mechanics
    player.add_dp(2000);
    assert_eq!(player.dp, 2000);
    assert!(player.consume_dp(1500));
    assert_eq!(player.dp, 500);
    assert!(!player.consume_dp(1000)); // Insuficiente

    // Flight drain
    assert!(player.drain_fly_time(30));
    assert_eq!(player.fly_time, 90);
    player.restore_fly_time(10);
    assert_eq!(player.fly_time, 100);

    // PvP Kill
    player.on_kill_player(2002);
    assert_eq!(player.kill_list.get_kill_count(2002), 1);
    assert_eq!(player.kill_list.total_kills(), 1);

    player.on_leave_world();
    assert_eq!(player.creature.visible.is_spawned, false);
}

#[test]
fn test_monster_controller_aggro_and_leash() {
    let mut monster = MonsterController::new(
        5001,
        210001,
        210010000,
        Coord::new(0.0, 0.0, 0.0),
        0,
        4.0,
        10000,
        20.0,
        false,
    );

    // Attack monster
    let res = monster.npc.creature.on_attacked(1001, 1500);
    assert_eq!(res.damage, 1500);
    assert_eq!(monster.npc.creature.hp, 8500);
    assert_eq!(monster.npc.creature.aggro_list.get_most_hated(), Some(1001));

    // Move monster beyond leash range (leash = 50m)
    monster.npc.npc_move.update_position(Coord::new(60.0, 0.0, 0.0), 0);
    assert!(monster.check_leash());
    assert_eq!(monster.npc.creature.hp, 10000); // HP resetado no leash
    assert!(monster.npc.creature.aggro_list.is_empty());
}

#[test]
fn test_attack_util_and_status_formulas() {
    // High evasion -> Dodge
    let status = AttackUtil::calculate_physical_status(100, 500, 100, 100, 100, 100);
    assert_eq!(status, AttackStatus::Dodge);

    // High block -> Block
    let status_block = AttackUtil::calculate_physical_status(100, 100, 100, 400, 100, 100);
    assert_eq!(status_block, AttackStatus::Block);

    // Normal hit calculation
    let res = AttackUtil::calculate_final_damage(1000, AttackStatus::NormalHit, 0);
    assert_eq!(res.damage, 1000);

    // Block reduction (70% reduction -> 300 damage)
    let res_block = AttackUtil::calculate_final_damage(1000, AttackStatus::Block, 0);
    assert_eq!(res_block.damage, 300);

    // Critical boost (1.5x -> 1500 damage)
    let res_crit = AttackUtil::calculate_final_damage(1000, AttackStatus::Critical, 0);
    assert_eq!(res_crit.damage, 1500);

    // Shield absorption (1000 base, 400 shield -> 600 final)
    let res_shield = AttackUtil::calculate_final_damage(1000, AttackStatus::NormalHit, 400);
    assert_eq!(res_shield.damage, 600);
    assert_eq!(res_shield.shield_absorbed, 400);
}

#[test]
fn test_effect_controller_and_dispels() {
    let mut effect_ctrl = EffectController::new();

    let buff1 = ActiveEffect::new(101, 1, 300, false);
    let debuff1 = ActiveEffect::new(201, 1, 30, true);
    let debuff2 = ActiveEffect::new(202, 1, 60, true);

    effect_ctrl.add_effect(buff1);
    effect_ctrl.add_effect(debuff1);
    effect_ctrl.add_effect(debuff2);

    assert_eq!(effect_ctrl.container.count_buffs(), 1);
    assert_eq!(effect_ctrl.container.count_debuffs(), 2);

    // Dispel 1 debuff (Purification Spell)
    effect_ctrl.dispel_debuffs(1);
    assert_eq!(effect_ctrl.container.count_debuffs(), 1);
    assert_eq!(effect_ctrl.container.count_buffs(), 1);

    // Abnormal state flags (e.g. Stun bit 0x01, Silence bit 0x02)
    effect_ctrl.set_abnormal_state(0x01 | 0x02);
    assert!(effect_ctrl.has_abnormal_state(0x01));
    assert!(effect_ctrl.has_abnormal_state(0x02));
    effect_ctrl.unset_abnormal_state(0x01);
    assert!(!effect_ctrl.has_abnormal_state(0x01));
    assert!(effect_ctrl.has_abnormal_state(0x02));
}

#[test]
fn test_rv_controller_rift_entries() {
    let mut rift = RVController::new(
        7001,
        1,
        210010000,
        Coord::new(100.0, 100.0, 10.0),
        220010000,
        Coord::new(500.0, 500.0, 20.0),
        2, // Max 2 entries
        20,
        30,
    );

    // Level 15 player cannot use
    assert!(!rift.can_use(15));
    assert_eq!(rift.use_rift(15), None);

    // Level 25 player uses entry 1
    assert!(rift.can_use(25));
    assert_eq!(rift.use_rift(25), Some((220010000, Coord::new(500.0, 500.0, 20.0))));
    assert_eq!(rift.used_entries, 1);
    assert!(rift.is_open);

    // Level 28 player uses entry 2 (exhausts rift)
    assert!(rift.can_use(28));
    assert_eq!(rift.use_rift(28), Some((220010000, Coord::new(500.0, 500.0, 20.0))));
    assert_eq!(rift.used_entries, 2);
    assert!(!rift.is_open);

    // Third entry fails
    assert!(!rift.can_use(25));
}

#[test]
fn test_gatherable_depletion() {
    let mut gatherable = GatherableController::new(
        8001,
        1001,
        210010000,
        Coord::new(10.0, 20.0, 5.0),
        100, // Skill level 100 required
    );

    // Player with 50 skill cannot gather
    assert!(!gatherable.start_gathering(1001, 50));

    // Player with 120 skill starts gathering
    assert!(gatherable.start_gathering(1001, 120));
    assert!(!gatherable.finish_gathering(true)); // 1st success
    assert_eq!(gatherable.current_gather_count, 1);

    assert!(gatherable.start_gathering(1001, 120));
    assert!(!gatherable.finish_gathering(true)); // 2nd success
    assert_eq!(gatherable.current_gather_count, 2);

    assert!(gatherable.start_gathering(1001, 120));
    assert!(gatherable.finish_gathering(true)); // 3rd success -> Depleted!
    assert_eq!(gatherable.current_gather_count, 3);
    assert!(gatherable.is_depleted());
}

#[test]
fn test_trap_proximity_detonation() {
    let mut trap = TrapController::new(
        9001,
        1001,
        10401,
        210010000,
        Coord::new(0.0, 0.0, 0.0),
        5.0, // 5m trigger radius
        2500,
    );

    // Target at 10m does not trigger
    assert_eq!(trap.check_trigger(&Coord::new(10.0, 0.0, 0.0)), None);
    assert!(!trap.is_triggered);

    // Target steps within 3m -> Detonates!
    assert_eq!(trap.check_trigger(&Coord::new(3.0, 0.0, 0.0)), Some(2500));
    assert!(trap.is_triggered);

    // Second check does not re-trigger
    assert_eq!(trap.check_trigger(&Coord::new(1.0, 0.0, 0.0)), None);
}

#[test]
fn test_shield_controller_fortress_defense() {
    let mut shield = ShieldController::new(
        9501,
        1011,
        210010000,
        Coord::new(0.0, 0.0, 0.0),
        50.0,
        10000, // 10k shield HP
    );

    assert!(shield.is_shield_active);
    let remaining_dmg = shield.absorb_damage(4000);
    assert_eq!(remaining_dmg, 0);
    assert_eq!(shield.shield_hp, 6000);
    assert!(shield.is_shield_active);

    // Overkill damage breaks shield
    let breakthrough = shield.absorb_damage(8000);
    assert_eq!(breakthrough, 2000);
    assert_eq!(shield.shield_hp, 0);
    assert!(!shield.is_shield_active);
}

#[test]
fn test_observe_controller_shield_and_notifications() {
    let mut obs_ctrl = ObserveController::new();

    // Attach dynamic attack shield (absorbs 50% of damage up to 500 HP)
    let shield = AttackShieldObserver::new(500, 50);
    obs_ctrl.attach_shield(shield);

    // 600 damage dealt -> 50% = 300 absorbed, 300 remaining
    let (rem_dmg, absorbed) = obs_ctrl.absorb_damage_shields(600);
    assert_eq!(rem_dmg, 300);
    assert_eq!(absorbed, 300);

    // Another 600 damage -> shield has 200 HP left -> absorbs 200, 400 remaining
    let (rem_dmg2, absorbed2) = obs_ctrl.absorb_damage_shields(600);
    assert_eq!(rem_dmg2, 400);
    assert_eq!(absorbed2, 200);

    // Shield is now broken and removed
    let (rem_dmg3, absorbed3) = obs_ctrl.absorb_damage_shields(600);
    assert_eq!(rem_dmg3, 600);
    assert_eq!(absorbed3, 0);
}

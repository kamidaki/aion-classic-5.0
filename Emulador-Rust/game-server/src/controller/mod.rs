//! Camada de Controladores do Jogo (Controllers) - Padrão Java AION 4.8

pub mod visible_object;
pub mod creature;
pub mod player;
pub mod npc;
pub mod monster;
pub mod gather;
pub mod pet;
pub mod summon;
pub mod trap;
pub mod house;
pub mod movement;

pub use visible_object::VisibleObjectController;
pub use creature::CreatureController;
pub use player::PlayerController;
pub use npc::NpcController;
pub use monster::MonsterController;
pub use gather::GatherableController;
pub use pet::PetController;
pub use summon::{SummonController, SummonCommand};
pub use trap::TrapController;
pub use house::HouseController;
pub use movement::*;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_player_controller_flight_and_glide() {
        let mut pc = PlayerController::new(1001, 1, 5000, 2000, 120);
        assert!(!pc.is_flying);
        assert!(pc.start_fly());
        assert!(pc.is_flying);

        pc.tick_flight(20);
        assert_eq!(pc.flight_time_remaining, 100);

        assert!(pc.toggle_glide());
        assert!(pc.is_gliding);

        pc.stop_fly();
        assert!(!pc.is_flying);
        assert!(!pc.is_gliding);
    }

    #[test]
    fn test_monster_controller_hate_and_leash() {
        let mut mc = MonsterController::new(5001, 210001, 10000, 100.0, 100.0, 10.0);
        mc.add_hate(1001, 500);
        assert_eq!(mc.creature.target_id, Some(1001));

        // Perto do spawn -> não dá leash
        assert!(!mc.check_leash(110.0, 100.0));
        assert_eq!(mc.creature.target_id, Some(1001));

        // Longe do spawn (> 35m) -> dá leash e reseta aggro
        assert!(mc.check_leash(200.0, 100.0));
        assert!(mc.is_leashing);
        assert_eq!(mc.creature.target_id, None);
    }

    #[test]
    fn test_gatherable_controller_rates_and_exhaustion() {
        let mut gc = GatherableController::new(8001, 40001, 100, 2);
        assert!(gc.can_gather(150));
        assert!(!gc.can_gather(50));

        let chance = gc.calculate_success_chance(120);
        assert_eq!(chance, 90.0);

        assert!(gc.start_gathering(1001));
        // Primeira extração com sucesso
        assert!(!gc.finish_gathering(true));
        assert_eq!(gc.remaining_gathers, 1);

        // Segunda extração com sucesso -> nó esgotado
        assert!(gc.start_gathering(1001));
        assert!(gc.finish_gathering(true));
        assert_eq!(gc.remaining_gathers, 0);
    }

    #[test]
    fn test_movement_controllers() {
        let mut pmc = PlayerMoveController::new(100.0, 100.0, 10.0, 60, 6.0);
        // Movimento válido dentro de 1 segundo (distância <= 9.0m)
        assert!(pmc.validate_move(105.0, 100.0, 10.0, 60, 1.0));
        assert_eq!(pmc.playable_move.creature_move.x, 105.0);

        // Movimento inválido (distância 50m em 1s) -> rejeitado por speedhack check
        assert!(!pmc.validate_move(155.0, 100.0, 10.0, 60, 1.0));

        let mut nmc = NpcMoveController::new(0.0, 0.0, 0.0, 0, 3.0);
        nmc.start_chase();
        assert!(!nmc.step_towards(10.0, 0.0, 0.0, 1.0)); // andou 3m de 10m
        assert_eq!(nmc.creature_move.x, 3.0);
    }
}

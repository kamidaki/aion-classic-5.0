//! Suíte de Testes Unitários do Módulo Model

#[cfg(test)]
pub mod tests {
    use crate::engine::Coord;
    use crate::model::abyss_rank::{AbyssRankType, AbyssRankingResult};
    use crate::model::account::account::{AccountModel, MembershipType};
    use crate::model::account::account_warehouse::AccountWarehouseModel;
    use crate::model::chat_type::ChatType;
    use crate::model::craft::craft_recipe::CraftRecipeModel;
    use crate::model::gameobjects::creature::Creature;
    use crate::model::gameobjects::gatherable::GatherableModel;
    use crate::model::gameobjects::npc::NpcModel;
    use crate::model::gameobjects::player::PlayerModel;
    use crate::model::gender::Gender;
    use crate::model::items::item::ItemModel;
    use crate::model::items::item_slot::ItemSlot;
    use crate::model::items::item_storage::{ItemStorageModel, StorageType};
    use crate::model::items::manastone::ItemQuality;
    use crate::model::player_class::PlayerClass;
    use crate::model::race::Race;
    use crate::model::stats::creature_stats::CreatureStats;
    use crate::model::stats::stat_enum::StatEnum;
    use crate::model::stats::stat_modifiers::StatModifier;
    use crate::model::team::loot_rules::LootRuleType;
    use crate::model::team::player_group::PlayerGroupModel;
    use crate::model::tribe_class::TribeClass;

    #[test]
    fn test_race_and_player_class_identification() {
        assert!(Race::Elyos.is_player_race());
        assert!(Race::Asmodians.is_player_race());
        assert!(!Race::Dragon.is_player_race());
        assert!(Race::Elyos.is_enemy(&Race::Asmodians));
        assert!(Race::Elyos.is_enemy(&Race::Dragon));

        assert!(PlayerClass::Warrior.is_starting_class());
        assert!(!PlayerClass::Gladiator.is_starting_class());
        assert_eq!(PlayerClass::Gladiator.get_starting_class(), PlayerClass::Warrior);
        assert_eq!(PlayerClass::Luminess.id(), 16);
    }

    #[test]
    fn test_creature_damage_and_healing() {
        let mut creature = Creature::new(1, "Test Mob", Coord::new(100.0, 100.0, 10.0), 210010000, 1, 10, 1000, 500);
        assert_eq!(creature.current_hp, 1000);
        assert!(!creature.is_dead);

        creature.apply_damage(400);
        assert_eq!(creature.current_hp, 600);

        creature.heal_hp(200);
        assert_eq!(creature.current_hp, 800);

        creature.apply_damage(900);
        assert_eq!(creature.current_hp, 0);
        assert!(creature.is_dead);
    }

    #[test]
    fn test_creature_stats_and_modifiers() {
        let mut stats = CreatureStats::new();
        stats.set_base_stat(StatEnum::MaxHp, 5000);
        stats.set_base_stat(StatEnum::MainHandAttack, 200);

        // Adiciona flat modifier (+50 attack)
        stats.add_modifier(StatModifier::add(StatEnum::MainHandAttack, 50, 101));
        assert_eq!(stats.get_effective_stat(StatEnum::MainHandAttack), 250);

        // Adiciona percent modifier (+10% attack)
        stats.add_modifier(StatModifier::percent(StatEnum::MainHandAttack, 10, 102));
        assert_eq!(stats.get_effective_stat(StatEnum::MainHandAttack), 275);

        // Remove modificador por source_id
        stats.remove_modifiers_by_source(101);
        assert_eq!(stats.get_effective_stat(StatEnum::MainHandAttack), 220);
    }

    #[test]
    fn test_account_and_warehouse() {
        let account = AccountModel::new(10, "tester", 0);
        assert_eq!(account.membership, MembershipType::SielAura);

        let mut wh = AccountWarehouseModel::new(10, 16);
        assert!(wh.deposit_item(0, 186000030, 5).is_ok());
        assert!(wh.deposit_item(20, 186000030, 5).is_err());

        let item = wh.withdraw_item(0);
        assert_eq!(item, Some((186000030, 5)));
        assert_eq!(wh.withdraw_item(0), None);
    }

    #[test]
    fn test_player_group_management() {
        let mut group = PlayerGroupModel::new(1, 1001);
        assert_eq!(group.members.len(), 1);

        assert!(group.add_member(1002).is_ok());
        assert!(group.add_member(1003).is_ok());
        assert_eq!(group.members.len(), 3);

        assert!(group.remove_member(1002));
        assert_eq!(group.members.len(), 2);
    }

    #[test]
    fn test_inventory_storage() {
        let mut storage = ItemStorageModel::new(StorageType::Cube, 27);
        let item = ItemModel::new(1, 100000001, 1, ItemQuality::Rare);
        assert!(storage.add_item(0, item).is_ok());
        assert_eq!(storage.item_count(), 1);

        let retrieved = storage.remove_item(0);
        assert!(retrieved.is_some());
        assert_eq!(storage.item_count(), 0);
    }

    #[test]
    fn test_gatherable_harvest() {
        let mut gather = GatherableModel::new(1, "Aria", 150000001, Coord::new(0.0, 0.0, 0.0), 210010000, 1, 3);
        assert!(gather.harvest());
        assert!(gather.harvest());
        assert!(gather.harvest());
        assert!(!gather.harvest());
    }
}

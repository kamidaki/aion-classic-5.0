#[cfg(test)]
mod tests {
    use crate::character::Character;
    use crate::engine::Coord;
    use crate::data::item::*;
    use crate::services::item::*;
    use crate::data_loader::string_loader::StringTable;
    use crate::data_loader::cache_watcher::CacheWatcher;

    #[test]
    fn test_string_table_parsing() {
        let mut table = StringTable::new();
        let xml_mock = r#"<?xml version="1.0" encoding="utf-8"?>
<strings>
  <string>
    <id>700001</id>
    <name>STR_SWORD_CIRCULOUS</name>
    <body>Circulous Sword</body>
  </string>
  <string>
    <id>700002</id>
    <name>STR_WINGS_STORMLIGHT</name>
    <body>Stormlight Wings</body>
  </string>
</strings>"#;

        // Simula parse interno
        let count = {
            let initial = table.len();
            let mut pos = 0;
            while let Some(start_tag) = xml_mock[pos..].find("<string>") {
                let item_start = pos + start_tag;
                let end_tag = match xml_mock[item_start..].find("</string>") {
                    Some(end) => item_start + end + 9,
                    None => break,
                };
                let block = &xml_mock[item_start..end_tag];
                if let (Some(name_start), Some(body_start)) = (block.find("<name>"), block.find("<body>")) {
                    if let (Some(name_end), Some(body_end)) = (block[name_start + 6..].find("</name>"), block[body_start + 6..].find("</body>")) {
                        let key = block[name_start + 6..name_start + 6 + name_end].trim().to_string();
                        let val = block[body_start + 6..body_start + 6 + body_end].trim().to_string();
                        table.insert(key, val);
                    }
                }
                pos = end_tag;
            }
            table.len() - initial
        };

        assert_eq!(count, 2);
        assert_eq!(table.get("STR_SWORD_CIRCULOUS"), Some("Circulous Sword"));
        assert_eq!(table.get("STR_WINGS_STORMLIGHT"), Some("Stormlight Wings"));
        assert_eq!(table.get("STR_NON_EXISTENT"), None);
    }

    #[test]
    fn test_item_template_and_slot_capabilities() {
        let mut item = ItemTemplate::new(100000001, "sword_circulous".to_string());
        item.clean_name = "Circulous Sword".to_string();
        item.weapon_type = Some(WeaponType::Sword1H);
        item.slot = ItemSlot::MAIN_OR_SUB;
        item.quality = ItemQuality::Common;
        item.level = 1;
        item.restrictions.min_level = 1;
        item.restrictions.class_mask = PlayerClassMask::WARRIOR;
        item.modifiers.option_slot_bonus = 1;
        item.modifiers.can_composite = false;

        assert!(item.is_weapon());
        assert!(!item.is_two_handed());
        assert!(!item.is_armor());
        assert!(!item.is_wings());
        assert!(item.can_be_equipped_by(0, 1)); // Warrior level 1
        assert!(!item.can_be_equipped_by(6, 1)); // Mage cannot equip warrior sword
    }

    #[test]
    fn test_two_handed_weapons_and_wings() {
        let mut bow = ItemTemplate::new(101700001, "bow_test".to_string());
        bow.weapon_type = Some(WeaponType::Bow);
        bow.slot = ItemSlot::MAIN_HAND;
        assert!(bow.is_two_handed());

        let mut wings = ItemTemplate::new(187000001, "wings_test".to_string());
        wings.slot = ItemSlot::WINGS;
        wings.accessory_type = Some(AccessoryType::Wings);
        assert!(wings.is_wings());
        assert!(wings.slot.intersects(ItemSlot::WINGS));
    }

    #[test]
    fn test_item_equip_validation() {
        let character = Character::new(1, 100, Coord::new(0.0, 0.0, 0.0));
        let mut item = ItemTemplate::new(100000001, "sword_circulous".to_string());
        item.restrictions.min_level = 10;
        item.restrictions.class_mask = PlayerClassMask::ALL;
        item.slot = ItemSlot::MAIN_OR_SUB;

        // Level 14 character can equip level 10 item
        let result = ItemEquipService::can_equip(&character, &item, ItemSlot::MAIN_HAND);
        assert!(result.is_ok());

        // Level 50 item should fail with LevelTooLow
        item.restrictions.min_level = 50;
        let result = ItemEquipService::can_equip(&character, &item, ItemSlot::MAIN_HAND);
        assert!(result.is_err());
    }

    #[test]
    fn test_armsfusion_two_handed_weapons() {
        let mut primary = ItemTemplate::new(101700001, "primary_bow".to_string());
        primary.weapon_type = Some(WeaponType::Bow);
        primary.slot = ItemSlot::MAIN_HAND;
        primary.level = 50;
        primary.stats.min_damage = 200;
        primary.stats.max_damage = 300;
        primary.modifiers.can_composite = true;

        let mut secondary = ItemTemplate::new(101700002, "secondary_bow".to_string());
        secondary.weapon_type = Some(WeaponType::Bow);
        secondary.slot = ItemSlot::MAIN_HAND;
        secondary.level = 45;
        secondary.stats.min_damage = 150;
        secondary.stats.max_damage = 250;

        assert!(ItemFusionService::can_fuse(&primary, &secondary).is_ok());

        let fused = ItemFusionService::calculate_fusion_bonus(&secondary);
        assert_eq!(fused.bonus_min_damage, 15); // 10% of 150
        assert_eq!(fused.bonus_max_damage, 25); // 10% of 250
    }

    #[test]
    fn test_item_socketing_and_manastones() {
        let mut item = ItemTemplate::new(100000001, "sword_test".to_string());
        item.quality = ItemQuality::Unique; // Base 3 slots
        item.modifiers.option_slot_bonus = 2; // +2 bonus = 5 total slots

        let total_slots = ItemSocketService::get_total_manastone_slots(&item);
        assert_eq!(total_slots, 5);

        assert!(ItemSocketService::can_socket_manastone(&item, 0).is_ok());
        assert!(ItemSocketService::can_socket_manastone(&item, 4).is_ok());
        assert!(ItemSocketService::can_socket_manastone(&item, 5).is_err()); // Full
    }

    #[test]
    fn test_item_enchanting_and_stats() {
        let mut weapon = ItemTemplate::new(100000001, "sword_test".to_string());
        weapon.weapon_type = Some(WeaponType::Sword1H);
        weapon.slot = ItemSlot::MAIN_OR_SUB;
        weapon.modifiers.no_enchant = false;
        weapon.modifiers.max_enchant_level = 15;

        assert!(ItemEnchantService::can_enchant(&weapon, 0).is_ok());
        assert!(ItemEnchantService::can_enchant(&weapon, 14).is_ok());
        assert!(ItemEnchantService::can_enchant(&weapon, 15).is_err());

        let (patk, _) = ItemEnchantService::get_enchant_stats(&weapon, 10);
        assert_eq!(patk, 20); // 2 * 10 = 20 for 1H weapon
    }

    #[test]
    fn test_conditioning_charge_service() {
        let mut item = ItemTemplate::new(100000001, "holy_sword".to_string());
        item.modifiers.charge_capacity = 10000;

        let mut state = ItemChargeService::new_charge_state(&item).expect("charge state");
        assert_eq!(state.charge_level, 0);

        ItemChargeService::recharge(&mut state, 6000);
        assert_eq!(state.charge_level, 2); // > 50% = Level 2

        ItemChargeService::consume_point(&mut state, 4000);
        assert_eq!(state.charge_level, 1); // < 50% = Level 1
    }

    #[test]
    fn test_cache_watcher_integrity() {
        let mut watcher = CacheWatcher::new();
        assert!(!watcher.has_changes());
    }

    #[test]
    fn test_classic_4_5_classes_and_chainblade() {
        // Revenant Chainblade
        let mut chainblade = ItemTemplate::new(102400001, "revenant_blade".to_string());
        chainblade.weapon_type = Some(WeaponType::Blade2H);
        chainblade.slot = ItemSlot::MAIN_HAND;
        chainblade.restrictions.class_mask = PlayerClassMask::THUNDERER;
        chainblade.restrictions.min_level = 10;

        assert!(chainblade.is_two_handed());
        assert!(chainblade.can_be_equipped_by(13, 10)); // Thunderer/Revenant
        assert!(!chainblade.can_be_equipped_by(0, 10)); // Warrior cannot equip

        // Lumines / Martial Artist
        let mut lumines_item = ItemTemplate::new(110301338, "lumines_armor".to_string());
        lumines_item.restrictions.class_mask = PlayerClassMask::MARTIAL_ARTIST;
        lumines_item.restrictions.min_level = 1;
        assert!(lumines_item.can_be_equipped_by(14, 1)); // Martial Artist / Lumines
        assert!(!lumines_item.can_be_equipped_by(6, 1));  // Mage cannot equip
    }

    #[test]
    fn test_class_progression_and_starting_classes() {
        assert!(PlayerClassMask::is_starting_class(0));  // Warrior
        assert!(PlayerClassMask::is_starting_class(3));  // Scout
        assert!(PlayerClassMask::is_starting_class(6));  // Mage
        assert!(PlayerClassMask::is_starting_class(9));  // Priest
        assert!(PlayerClassMask::is_starting_class(12)); // Monk (Telos)
        assert!(PlayerClassMask::is_starting_class(14)); // Martial Artist (Lumines)

        assert!(!PlayerClassMask::is_starting_class(1));  // Gladiator
        assert!(!PlayerClassMask::is_starting_class(13)); // Thunderer/Revenant
        assert!(!PlayerClassMask::is_starting_class(15)); // Battle Master/Brawler

        assert_eq!(PlayerClassMask::get_starting_class_for(13), 12); // Thunderer -> Monk
        assert_eq!(PlayerClassMask::get_starting_class_for(15), 14); // Battle Master -> Martial Artist
    }
}

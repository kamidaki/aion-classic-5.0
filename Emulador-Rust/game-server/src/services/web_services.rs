//! Serviços Web, Loja In-Game (Black Cloud Traders), Daeva Pass, Roupeiro e Presença Diária

use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct DaevaPass {
    pub season_id: u32,
    pub points: u32,
    pub level: u8,
    pub max_level: u8,
    pub is_premium: bool,
    pub claimed_free: Vec<u8>,
    pub claimed_premium: Vec<u8>,
}

impl DaevaPass {
    pub const POINTS_PER_LEVEL: u32 = 100;

    pub fn new(season_id: u32, is_premium: bool) -> Self {
        Self {
            season_id,
            points: 0,
            level: 1,
            max_level: 45,
            is_premium,
            claimed_free: Vec::new(),
            claimed_premium: Vec::new(),
        }
    }

    pub fn add_points(&mut self, amount: u32) -> u8 {
        self.points += amount;
        let new_level = ((self.points / Self::POINTS_PER_LEVEL) + 1).min(self.max_level as u32) as u8;
        let leveled_up = new_level > self.level;
        self.level = new_level;
        if leveled_up { self.level } else { 0 }
    }

    pub fn claim_reward(&mut self, level: u8, premium: bool) -> Option<u32> {
        if level > self.level {
            return None;
        }

        if premium {
            if !self.is_premium || self.claimed_premium.contains(&level) {
                return None;
            }
            self.claimed_premium.push(level);
            Some(188000000 + level as u32) // ID de Recompensa Premium
        } else {
            if self.claimed_free.contains(&level) {
                return None;
            }
            self.claimed_free.push(level);
            Some(187000000 + level as u32) // ID de Recompensa Free
        }
    }
}

#[derive(Debug, Clone)]
pub struct Wardrobe {
    pub character_id: u32,
    pub unlocked_skins: Vec<u32>,
    pub applied_skins: HashMap<u8, u32>,
}

impl Wardrobe {
    pub fn new(character_id: u32) -> Self {
        Self {
            character_id,
            unlocked_skins: Vec::new(),
            applied_skins: HashMap::new(),
        }
    }

    pub fn register_skin(&mut self, item_id: u32) -> bool {
        if !self.unlocked_skins.contains(&item_id) {
            self.unlocked_skins.push(item_id);
            true
        } else {
            false
        }
    }

    pub fn apply_skin(&mut self, slot: u8, item_id: u32) -> bool {
        if self.unlocked_skins.contains(&item_id) {
            self.applied_skins.insert(slot, item_id);
            true
        } else {
            false
        }
    }

    pub fn remove_skin(&mut self, slot: u8) -> bool {
        self.applied_skins.remove(&slot).is_some()
    }
}

#[derive(Debug, Clone)]
pub struct AtreianPassport {
    pub cycle_month: u8,
    pub login_days: u8,
    pub claimed_days: Vec<u8>,
}

impl AtreianPassport {
    pub fn new(cycle_month: u8) -> Self {
        Self {
            cycle_month,
            login_days: 1,
            claimed_days: Vec::new(),
        }
    }

    pub fn record_login(&mut self) {
        if self.login_days < 28 {
            self.login_days += 1;
        }
    }

    pub fn claim_day(&mut self, day: u8) -> Option<u32> {
        if day <= self.login_days && !self.claimed_days.contains(&day) && day <= 28 {
            self.claimed_days.push(day);
            Some(186000000 + day as u32) // Caixa diária de presença
        } else {
            None
        }
    }
}

#[derive(Debug, Clone)]
pub struct ShopItem {
    pub item_id: u32,
    pub price_toll: u32,
    pub category: &'static str,
}

#[derive(Debug, Clone, Default)]
pub struct BlackCloudShop {
    pub items: HashMap<u32, ShopItem>,
}

impl BlackCloudShop {
    pub fn new() -> Self {
        let mut items = HashMap::new();
        items.insert(
            187000100,
            ShopItem {
                item_id: 187000100,
                price_toll: 500,
                category: "Popular",
            },
        );
        items.insert(
            187000101,
            ShopItem {
                item_id: 187000101,
                price_toll: 1200,
                category: "Cosmetics",
            },
        );
        Self { items }
    }

    pub fn buy_item(&self, player_toll: u32, item_id: u32) -> Result<(u32, u32), &'static str> {
        let item = self.items.get(&item_id).ok_or("Item nao encontrado na loja")?;
        if player_toll < item.price_toll {
            return Err("Toll / Quna insuficiente");
        }
        let remaining_toll = player_toll - item.price_toll;
        Ok((item.price_toll, remaining_toll))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn daeva_pass_points_levels_and_claims() {
        let mut pass = DaevaPass::new(1, true);
        assert_eq!(pass.level, 1);

        // Add 250 points -> Should reach level 3
        let lvl = pass.add_points(250);
        assert_eq!(lvl, 3);
        assert_eq!(pass.level, 3);

        // Claim free level 1
        assert_eq!(pass.claim_reward(1, false), Some(187000001));
        // Double claim fails
        assert_eq!(pass.claim_reward(1, false), None);

        // Claim premium level 1 and 2
        assert_eq!(pass.claim_reward(1, true), Some(188000001));
        assert_eq!(pass.claim_reward(2, true), Some(188000002));

        // Claim level 5 (not unlocked yet) fails
        assert_eq!(pass.claim_reward(5, false), None);
    }

    #[test]
    fn wardrobe_skin_unlock_and_slot_assignment() {
        let mut wardrobe = Wardrobe::new(100);

        assert!(wardrobe.register_skin(110000001));
        assert!(!wardrobe.register_skin(110000001), "Skin ja cadastrada");

        // Cannot apply unregistered skin
        assert!(!wardrobe.apply_skin(1, 999999999));

        // Apply registered skin to chest slot (1)
        assert!(wardrobe.apply_skin(1, 110000001));
        assert_eq!(wardrobe.applied_skins.get(&1), Some(&110000001));

        // Remove skin
        assert!(wardrobe.remove_skin(1));
        assert_eq!(wardrobe.applied_skins.get(&1), None);
    }

    #[test]
    fn atreian_passport_daily_login_and_rewards() {
        let mut passport = AtreianPassport::new(8);
        assert_eq!(passport.login_days, 1);

        // Claim day 1
        assert_eq!(passport.claim_day(1), Some(186000001));
        assert_eq!(passport.claim_day(1), None);

        // Cannot claim day 2 yet
        assert_eq!(passport.claim_day(2), None);

        // Next day login
        passport.record_login();
        assert_eq!(passport.login_days, 2);
        assert_eq!(passport.claim_day(2), Some(186000002));
    }

    #[test]
    fn test_black_cloud_shop_purchases() {
        let shop = BlackCloudShop::new();
        let (cost, rem) = shop.buy_item(2000, 187000100).expect("deve comprar");
        assert_eq!(cost, 500);
        assert_eq!(rem, 1500);

        // Insufficient toll
        assert!(shop.buy_item(100, 187000101).is_err());
    }
}

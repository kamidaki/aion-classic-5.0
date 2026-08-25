//! Upgrades e Potencializadores / Conditioning / Augmentation do Aion Classic.

#[derive(Debug, Clone, Default)]
pub struct UpgradeStep {
    pub enchant_count: u32,
    pub rate: u32,             // ex: 10000 = 100%
    pub result_item: String,
    pub result_count: u32,
    pub required_kinah: u64,
    pub required_ap: u64,
}

#[derive(Debug, Clone, Default)]
pub struct ItemUpgradeTemplate {
    pub id: u32,
    pub name: String,
    pub upgrade_item_name: String,
    pub steps: Vec<UpgradeStep>,
}

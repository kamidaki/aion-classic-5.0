pub mod slot;
pub mod quality;
pub mod weapon;
pub mod armor;
pub mod accessory;
pub mod stats;
pub mod restrictions;
pub mod set_item;
pub mod dye;
pub mod upgrade;
pub mod compose;
pub mod template;
pub mod inventory;

pub use slot::ItemSlot;
pub use quality::ItemQuality;
pub use weapon::WeaponType;
pub use armor::ArmorType;
pub use accessory::AccessoryType;
pub use stats::{AttackType, ItemStats};
pub use restrictions::{GenderPermitted, ItemRestrictions, PlayerClassMask, RacePermitted};
pub use set_item::{SetBonus, SetItemTemplate};
pub use dye::{DyeColorTemplate, RgbColor};
pub use upgrade::{ItemUpgradeTemplate, UpgradeStep};
pub use compose::ItemComposeTemplate;
pub use template::{ItemCategory, ItemModifiers, ItemTemplate};
pub use inventory::{ItemInventario, POSICAO_INVISIVEL};

#[cfg(test)]
pub mod tests;

//! Pacotes Client de Inventário e Equipamentos (CM)

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct UseItem {
    pub item_obj_id: u32,
    pub target_obj_id: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EquipItem {
    pub item_obj_id: u32,
    pub slot: u8,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct UnequipItem {
    pub slot: u8,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SplitItem {
    pub item_obj_id: u32,
    pub amount: u32,
    pub destination_slot: u8,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeleteItem {
    pub item_obj_id: u32,
}

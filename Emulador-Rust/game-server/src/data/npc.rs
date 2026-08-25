#[repr(u32)]
#[derive(Debug, Clone, Copy)]
pub enum Id {
    SpringOutlaw = 210484,
    LakeSpirit = 210660,
    TahabataPyrelord = 217166,
    StarvedMosbear = 210564,
}

#[repr(u8)]
#[derive(Debug, Clone, Copy)]
pub enum State {
    Alive = 0x41,
    DeadNoLoot = 0x07,
}

#[repr(u32)]
#[derive(Debug, Clone, Copy)]
pub enum Name {
    SprigOutlaw = 300623,
    StarvedMosbear = 300703,
}

#[repr(u8)]
#[derive(Debug, Clone, Copy)]
pub enum Type {
    Attackable = 0,
    Peace = 2,
    Aggressive = 8,
    Invulernable = 10,
    Friend = 38,
    Support = 54,
}

#[derive(Debug, Clone)]
pub struct NpcShopItem {
    pub item_template_id: u32,
    pub infinite_stock: bool,
    pub stock: u32,
    pub buy_price: u64,
}

#[derive(Debug, Clone)]
pub struct NpcTemplate {
    pub npc_id: u32,
    pub dialog_id: u32,
    pub shop_items: Vec<NpcShopItem>,
}

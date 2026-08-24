use super::{
    character::{Character, Hp},
    data::npc,
    engine::{
        damage::{Hit, Type},
        Coord,
    },
    message::server as s,
    TICK_RATE,
};

#[derive(Debug)]
pub struct Entity {
    id: u32,
    target_id: Option<u32>,
    location: Coord,
    npc_id: u32,
    npc_name: u32,
    level: u16,
    pub hp: Hp,
    max_hp: i32,
    attack_sequence: u8,
    // Ticks
    attack_speed: f32,
    attack_cooldown: f32,
}
impl Entity {
    /// Construtor a partir dos enums escritos a mao, que existem para os poucos NPCs que o
    /// codigo referencia por nome.
    pub fn new(
        id: u32,
        location: Coord,
        npc_id: npc::Id,
        npc_name: npc::Name,
    ) -> Self {
        Self::novo(id, location, npc_id as u32, npc_name as u32)
    }

    /// Construtor a partir dos numeros crus, que e o que vem da tabela de spawns extraida da
    /// captura -- 530 NPCs distintos, longe demais para caber num enum.
    pub fn novo(
        id: u32,
        location: Coord,
        npc_id: u32,
        npc_name: u32,
    ) -> Self {
        Self {
            id,
            location,
            npc_id,
            npc_name,
            target_id: None,
            attack_speed: const { 1.750 * TICK_RATE },
            attack_cooldown: const { 1.750 * TICK_RATE },
            attack_sequence: 0,
            level: 0x0D,
            hp: Hp::new(1817),
            max_hp: 1817,
        }
    }

    pub fn is_dead(&self) -> bool {
        self.hp.current() <= 0
    }
    pub fn is_alive(&self) -> bool {
        self.hp.current() >= 0
    }

    pub fn attack(&mut self, character: &mut Character) -> Option<Vec<Hit>> {
        // If attack not on cooldown
        if self.attack_cooldown >= 0. {
            self.attack_cooldown -= 1.;
            return None;
        }

        // If in range
        if self.location.distance(character.location()) > 5. {
            return None;
        }

        self.attack_cooldown = self.attack_speed;
        Some(self.calculate_damage(character))
    }

    pub fn set_taget(&mut self, target_id: u32) -> s::NpcChangedTarget {
        self.target_id = Some(target_id);
        s::NpcChangedTarget::new(target_id, self.id)
    }

    pub fn clear_target(&mut self) {
        self.target_id = None;
    }

    fn calculate_damage(&mut self, character: &mut Character) -> Vec<Hit> {
        let dmg = 128;
        let hits = vec![Hit::new(dmg, Type::MainHand)];
        character.stats.hp.update(-dmg);
        self.attack_sequence = self.attack_sequence.wrapping_add(1);

        hits
    }

    pub fn id(&self) -> u32 {
        self.id
    }
    pub fn target_id(&self) -> Option<u32> {
        self.target_id
    }
    pub fn location(&self) -> &Coord {
        &self.location
    }
    pub fn npc_id(&self) -> u32 {
        self.npc_id
    }
    pub fn npc_name(&self) -> u32 {
        self.npc_name
    }
    pub fn level(&self) -> u16 {
        self.level
    }
}

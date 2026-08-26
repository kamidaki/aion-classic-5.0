//! Atributos e estatísticas de combate de itens no Aion Classic.

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum AttackType {
    #[default]
    Physical,
    Magical,
}

#[derive(Debug, Clone, Default)]
pub struct ItemStats {
    // Estatísticas de Ataque
    pub min_damage: u32,
    pub max_damage: u32,
    pub attack_type: AttackType,
    pub attack_delay: u32,        // ms (ex: 1400 = 1.4s)
    pub hit_count: u8,
    pub attack_range: f32,        // metros (ex: 1.5m para espadas, 25m para arcos)
    pub hit_accuracy: i32,
    pub critical: i32,
    pub magical_skill_boost: i32, // Magic Boost / Poder Mágico
    pub magical_hit_accuracy: i32,// Magic Accuracy

    // Estatísticas de Defesa
    pub physical_defend: i32,
    pub magical_defend: i32,
    pub magic_resist: i32,
    pub parry: i32,               // Aparar
    pub block: i32,               // Bloqueio com Escudo
    pub damage_reduce: i32,       // Redução de Dano do Escudo
    pub dodge: i32,               // Esquiva

    // Atributos Vitais e Movimento
    pub max_hp: i32,
    pub max_mp: i32,
    pub speed: i32,               // Bônus de velocidade em %
    pub fly_speed: i32,           // Bônus de velocidade de voo em %
    pub fly_time: i32,            // Segundos adicionais de voo
    pub pvp_attack_ratio: f32,    // % bônus de dano PvP
    pub pvp_defend_ratio: f32,    // % redução de dano recebido em PvP
}

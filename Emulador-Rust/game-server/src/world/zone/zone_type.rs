#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum ZoneType {
    Pvp,
    NoFly,
    Fly,
    Water,
    Lava,
    Safe,
    Breath,
    AbyssCore,
    Material,
    ItemUse,
    Siege,
}

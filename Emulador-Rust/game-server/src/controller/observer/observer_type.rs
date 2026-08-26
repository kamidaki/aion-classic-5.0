//! Tipos e Enums de Observers do Jogo (ObserverType - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum ObserverType {
    Move,
    Attack,
    Attacked,
    SkillUse,
    Die,
    Equip,
    Dot,
    ItemUse,
    Dialog,
    FlyRing,
    Collision,
    All,
}

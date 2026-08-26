//! Controlador de Voo e Planagem (FlyController - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum FlyState {
    #[default]
    None,
    Flying,
    Gliding,
    Falling,
}

pub struct FlyController {
    pub player_id: u32,
    pub state: FlyState,
    pub fly_speed: f32,
    pub glide_speed: f32,
}

impl FlyController {
    pub fn new(player_id: u32) -> Self {
        Self {
            player_id,
            state: FlyState::None,
            fly_speed: 9.0,
            glide_speed: 12.0,
        }
    }

    pub fn start_flying(&mut self) {
        self.state = FlyState::Flying;
    }

    pub fn start_gliding(&mut self) {
        self.state = FlyState::Gliding;
    }

    pub fn end_flight(&mut self) {
        self.state = FlyState::None;
    }

    pub fn is_flying(&self) -> bool {
        self.state == FlyState::Flying
    }

    pub fn is_gliding(&self) -> bool {
        self.state == FlyState::Gliding
    }
}

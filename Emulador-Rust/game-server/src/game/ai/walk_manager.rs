//! Gerenciador de Rotas de Patrulha (WalkManager)

#[derive(Debug, Clone)]
pub struct WalkManager {
    pub waypoints: Vec<(f32, f32, f32)>,
    pub current_index: usize,
    pub is_reverse: bool,
    pub pause_time_seconds: f32,
    pub current_pause_timer: f32,
    pub is_paused: bool,
}

impl WalkManager {
    pub fn new(waypoints: Vec<(f32, f32, f32)>, pause_time_seconds: f32) -> Self {
        Self {
            waypoints,
            current_index: 0,
            is_reverse: false,
            pause_time_seconds,
            current_pause_timer: 0.0,
            is_paused: false,
        }
    }

    pub fn get_current_waypoint(&self) -> Option<(f32, f32, f32)> {
        self.waypoints.get(self.current_index).copied()
    }

    pub fn advance_to_next_waypoint(&mut self) -> Option<(f32, f32, f32)> {
        if self.waypoints.is_empty() {
            return None;
        }

        if !self.is_reverse {
            if self.current_index + 1 < self.waypoints.len() {
                self.current_index += 1;
            } else {
                self.is_reverse = true;
                if self.current_index > 0 {
                    self.current_index -= 1;
                }
            }
        } else {
            if self.current_index > 0 {
                self.current_index -= 1;
            } else {
                self.is_reverse = false;
                if self.waypoints.len() > 1 {
                    self.current_index = 1;
                }
            }
        }

        self.is_paused = true;
        self.current_pause_timer = self.pause_time_seconds;
        self.get_current_waypoint()
    }

    pub fn tick_pause(&mut self, dt: f32) -> bool {
        if self.is_paused {
            self.current_pause_timer -= dt;
            if self.current_pause_timer <= 0.0 {
                self.is_paused = false;
                true // Pausa finalizada, pronto para andar
            } else {
                false // Ainda em pausa
            }
        } else {
            true
        }
    }
}

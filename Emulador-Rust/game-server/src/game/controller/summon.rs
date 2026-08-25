//! SummonController - Gerenciador de invocações (Espíritos de Spiritmaster)

use super::creature::CreatureController;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SummonCommand {
    Attack,
    Follow,
    Stay,
    Release,
}

#[derive(Debug, Clone)]
pub struct SummonController {
    pub creature: CreatureController,
    pub master_id: u32,
    pub current_command: SummonCommand,
}

impl SummonController {
    pub fn new(obj_id: u32, master_id: u32, max_hp: i32) -> Self {
        Self {
            creature: CreatureController::new(obj_id, max_hp, 1000),
            master_id,
            current_command: SummonCommand::Follow,
        }
    }

    pub fn execute_command(&mut self, cmd: SummonCommand, target_id: Option<u32>) {
        self.current_command = cmd;
        match cmd {
            SummonCommand::Attack => {
                self.creature.set_target(target_id);
                self.creature.is_in_combat = true;
            }
            SummonCommand::Follow => {
                self.creature.set_target(None);
                self.creature.is_in_combat = false;
            }
            SummonCommand::Stay => {
                self.creature.set_target(None);
            }
            SummonCommand::Release => {
                self.creature.is_dead = true;
            }
        }
    }
}

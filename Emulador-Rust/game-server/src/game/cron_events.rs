//! Agendador Cron Assíncrono, Sieges de Fortalezas, Conquista de Bases e Chefes de Raide Mundial

use super::engine::Coord;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CronAction {
    StartSiege { fortress_id: u32 },
    EndSiege { fortress_id: u32 },
    RecalculateAbyssRanks,
    DailyReset,
    SpawnWorldRaid { boss_id: u32 },
}

#[derive(Debug, Clone)]
pub struct CronTask {
    pub task_id: u32,
    pub name: String,
    pub interval_ticks: u64,
    pub last_run_tick: u64,
    pub action: CronAction,
}

#[derive(Debug, Default)]
pub struct CronScheduler {
    next_task_id: u32,
    tasks: Vec<CronTask>,
}

impl CronScheduler {
    pub fn new() -> Self {
        Self {
            next_task_id: 1,
            tasks: Vec::new(),
        }
    }

    pub fn schedule_task(&mut self, name: &str, interval_ticks: u64, action: CronAction, start_tick: u64) -> u32 {
        let task_id = self.next_task_id;
        self.next_task_id += 1;

        self.tasks.push(CronTask {
            task_id,
            name: name.to_string(),
            interval_ticks,
            last_run_tick: start_tick,
            action,
        });

        task_id
    }

    pub fn tick(&mut self, current_tick: u64) -> Vec<CronAction> {
        let mut triggered = Vec::new();

        for task in &mut self.tasks {
            if current_tick >= task.last_run_tick + task.interval_ticks {
                task.last_run_tick = current_tick;
                triggered.push(task.action.clone());
            }
        }

        triggered
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OutpostBase {
    pub base_id: u32,
    pub name: String,
    pub controlling_race: Option<u8>, // 0: Elyos, 1: Asmodian, None: Balaur/Neutral
    pub commander_hp: i32,
}

impl OutpostBase {
    pub fn new(base_id: u32, name: &str) -> Self {
        Self {
            base_id,
            name: name.to_string(),
            controlling_race: None, // Starts neutral / Balaur
            commander_hp: 250_000,
        }
    }

    pub fn capture(&mut self, winning_race: u8) {
        self.controlling_race = Some(winning_race);
        self.commander_hp = 250_000;
    }
}

#[derive(Debug, Clone)]
pub struct WorldRaidBoss {
    pub boss_id: u32,
    pub name: String,
    pub map_id: u32,
    pub location: Coord,
    pub hp: i64,
    pub max_hp: i64,
    pub is_spawned: bool,
}

impl WorldRaidBoss {
    pub fn new(boss_id: u32, name: &str, map_id: u32, location: Coord, max_hp: i64) -> Self {
        Self {
            boss_id,
            name: name.to_string(),
            map_id,
            location,
            hp: max_hp,
            max_hp,
            is_spawned: false,
        }
    }

    pub fn spawn(&mut self) {
        self.is_spawned = true;
        self.hp = self.max_hp;
    }

    pub fn despawn(&mut self) {
        self.is_spawned = false;
    }

    pub fn take_damage(&mut self, dmg: i64) -> bool {
        if !self.is_spawned {
            return false;
        }

        self.hp = (self.hp - dmg).max(0);
        if self.hp == 0 {
            self.is_spawned = false;
            true // Abatido com sucesso
        } else {
            false
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cron_scheduler_fires_at_intervals() {
        let mut scheduler = CronScheduler::new();
        scheduler.schedule_task("DailyReset", 1000, CronAction::DailyReset, 0);
        scheduler.schedule_task("KrotanSiege", 500, CronAction::StartSiege { fortress_id: 1211 }, 0);

        // Tick 200: no events
        assert_eq!(scheduler.tick(200).len(), 0);

        // Tick 500: Siege fires
        let triggered = scheduler.tick(500);
        assert_eq!(triggered, vec![CronAction::StartSiege { fortress_id: 1211 }]);

        // Tick 1000: Siege and DailyReset fire
        let triggered = scheduler.tick(1000);
        assert_eq!(triggered.len(), 2);
    }

    #[test]
    fn outpost_base_capture_and_reinforcements() {
        let mut base = OutpostBase::new(21, "Inggison Base 21");
        assert_eq!(base.controlling_race, None);

        // Elyos (0) defeats base commander
        base.capture(0);
        assert_eq!(base.controlling_race, Some(0));

        // Asmodians (1) conquer base
        base.capture(1);
        assert_eq!(base.controlling_race, Some(1));
    }

    #[test]
    fn world_raid_boss_spawn_and_damage() {
        let mut sunayaka = WorldRaidBoss::new(
            219901,
            "Enraged Sunayaka",
            600010000,
            Coord::new(500.0, 500.0, 100.0),
            10_000_000,
        );

        assert!(!sunayaka.is_spawned);
        sunayaka.spawn();
        assert!(sunayaka.is_spawned);

        // Deal 4M damage
        assert!(!sunayaka.take_damage(4_000_000));
        assert_eq!(sunayaka.hp, 6_000_000);

        // Fatal damage
        assert!(sunayaka.take_damage(6_000_000));
        assert_eq!(sunayaka.hp, 0);
        assert!(!sunayaka.is_spawned);
    }
}

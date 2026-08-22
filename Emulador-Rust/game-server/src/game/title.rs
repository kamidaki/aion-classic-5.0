use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct TitleTemplate {
    pub id: u16,
    pub name: &'static str,
    pub hp_bonus: i32,
    pub mp_bonus: i32,
    pub speed_percent: f32,
    pub flight_speed_percent: f32,
    pub physical_attack: i32,
    pub magic_boost: i32,
    pub physical_crit: i32,
}

#[derive(Debug, Clone, Default)]
pub struct TitleService {
    pub titles: HashMap<u16, TitleTemplate>,
}

impl TitleService {
    pub fn new() -> Self {
        let mut titles = HashMap::new();

        titles.insert(
            1,
            TitleTemplate {
                id: 1,
                name: "Poeta's Protector",
                hp_bonus: 20,
                mp_bonus: 20,
                speed_percent: 0.03,
                flight_speed_percent: 0.0,
                physical_attack: 1,
                magic_boost: 5,
                physical_crit: 2,
            },
        );

        titles.insert(
            2,
            TitleTemplate {
                id: 2,
                name: "Treehugger",
                hp_bonus: 40,
                mp_bonus: 0,
                speed_percent: 0.04,
                flight_speed_percent: 0.02,
                physical_attack: 2,
                magic_boost: 0,
                physical_crit: 5,
            },
        );

        titles.insert(
            50,
            TitleTemplate {
                id: 50,
                name: "Aion's Chosen",
                hp_bonus: 250,
                mp_bonus: 250,
                speed_percent: 0.05,
                flight_speed_percent: 0.05,
                physical_attack: 8,
                magic_boost: 35,
                physical_crit: 15,
            },
        );

        Self { titles }
    }

    pub fn get_title(&self, id: u16) -> Option<&TitleTemplate> {
        self.titles.get(&id)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_title_lookup() {
        let service = TitleService::new();
        let t = service.get_title(1).expect("titulo deve existir");
        assert_eq!(t.name, "Poeta's Protector");
        assert_eq!(t.hp_bonus, 20);
        assert_eq!(t.physical_attack, 1);
    }
}

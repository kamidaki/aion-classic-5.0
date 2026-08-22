use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct SimulatedItem {
    pub item_id: u32,
    pub count: u32,
    pub slot: u8,
    pub is_equipped: bool,
}

#[derive(Debug, Clone)]
pub struct SimulatedCharacter {
    pub char_id: u32,
    pub name: String,
    pub class_id: u8,
    pub level: u8,
    pub map_id: u32,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub heading: u8,
    pub hp: u32,
    pub max_hp: u32,
    pub mp: u32,
    pub max_mp: u32,
    pub kinah: u64,
    pub inventory: HashMap<u32, SimulatedItem>,
    pub active_target: Option<u32>,
    pub skill_cooldowns: HashMap<u16, u64>, // skill_id -> cooldown_end_tick
    pub is_flying: bool,
    pub is_gliding: bool,
}

impl SimulatedCharacter {
    pub fn new(char_id: u32, name: &str, class_id: u8, level: u8, map_id: u32) -> Self {
        Self {
            char_id,
            name: name.to_string(),
            class_id,
            level,
            map_id,
            x: 100.0,
            y: 100.0,
            z: 200.0,
            heading: 0,
            hp: 1500,
            max_hp: 1500,
            mp: 1200,
            max_mp: 1200,
            kinah: 50_000,
            inventory: HashMap::new(),
            active_target: None,
            skill_cooldowns: HashMap::new(),
            is_flying: false,
            is_gliding: false,
        }
    }

    pub fn move_to(&mut self, new_x: f32, new_y: f32, new_z: f32, heading: u8) {
        self.x = new_x;
        self.y = new_y;
        self.z = new_z;
        self.heading = heading;
    }

    pub fn jump_and_glide(&mut self) {
        self.is_gliding = true;
    }

    pub fn select_target(&mut self, target_id: u32) {
        self.active_target = Some(target_id);
    }

    pub fn clear_target(&mut self) {
        self.active_target = None;
    }

    pub fn cast_skill(
        &mut self,
        skill_id: u16,
        target_id: u32,
        mp_cost: u32,
        cooldown_ticks: u64,
        current_tick: u64,
    ) -> Result<u32, &'static str> {
        if self.mp < mp_cost {
            return Err("MP insuficiente");
        }
        if let Some(&cd_end) = self.skill_cooldowns.get(&skill_id) {
            if current_tick < cd_end {
                return Err("Habilidade em recarga (cooldown)");
            }
        }

        self.mp -= mp_cost;
        self.skill_cooldowns.insert(skill_id, current_tick + cooldown_ticks);
        self.active_target = Some(target_id);

        // Dano simulado da habilidade
        let damage = (skill_id as u32 * 5) + (self.level as u32 * 10);
        Ok(damage)
    }

    pub fn physical_attack(&self, target_id: u32) -> u32 {
        let base_damage = (self.level as u32 * 12) + 50;
        base_damage
    }

    pub fn take_damage(&mut self, amount: u32) -> bool {
        if amount >= self.hp {
            self.hp = 0;
            true // Morreu
        } else {
            self.hp -= amount;
            false
        }
    }

    pub fn heal(&mut self, amount: u32) {
        self.hp = (self.hp + amount).min(self.max_hp);
    }

    pub fn add_item(&mut self, item_id: u32, count: u32) {
        let next_slot = (self.inventory.len() as u8) + 1;
        let entry = self
            .inventory
            .entry(item_id)
            .or_insert(SimulatedItem {
                item_id,
                count: 0,
                slot: next_slot,
                is_equipped: false,
            });
        entry.count += count;
    }

    pub fn remove_item(&mut self, item_id: u32, count: u32) -> bool {
        if let Some(entry) = self.inventory.get_mut(&item_id) {
            if entry.count >= count {
                entry.count -= count;
                if entry.count == 0 {
                    self.inventory.remove(&item_id);
                }
                return true;
            }
        }
        false
    }

    pub fn equip_item(&mut self, item_id: u32) -> Result<(), &'static str> {
        let item = self.inventory.get_mut(&item_id).ok_or("Item inexistente no inventario")?;
        item.is_equipped = true;
        Ok(())
    }

    pub fn use_potion(&mut self, potion_id: u32, hp_heal: u32, mp_heal: u32) -> Result<(), &'static str> {
        if !self.remove_item(potion_id, 1) {
            return Err("Pocao nao encontrada");
        }
        self.heal(hp_heal);
        self.mp = (self.mp + mp_heal).min(self.max_mp);
        Ok(())
    }

    pub fn execute_gm_command(&mut self, command: &str) -> String {
        let parts: Vec<&str> = command.split_whitespace().collect();
        if parts.is_empty() {
            return "Comando vazio".to_string();
        }

        match parts[0] {
            ".setlevel" => {
                if let Some(lvl_str) = parts.get(1) {
                    if let Ok(lvl) = lvl_str.parse::<u8>() {
                        self.level = lvl.clamp(1, 65);
                        self.max_hp = (self.level as u32 * 200) + 1000;
                        self.hp = self.max_hp;
                        return format!("Nivel alterado para {}", self.level);
                    }
                }
                "Uso: .setlevel <1-65>".to_string()
            }
            ".teleport" => {
                if parts.len() >= 4 {
                    if let (Ok(x), Ok(y), Ok(z)) = (
                        parts[1].parse::<f32>(),
                        parts[2].parse::<f32>(),
                        parts[3].parse::<f32>(),
                    ) {
                        self.move_to(x, y, z, 0);
                        return format!("Teletransportado para ({:.1}, {:.1}, {:.1})", x, y, z);
                    }
                }
                "Uso: .teleport <x> <y> <z>".to_string()
            }
            ".goto" => {
                if let Some(dest) = parts.get(1) {
                    if let Some((map_id, x, y, z)) = crate::game::social::resolve_goto_location(dest) {
                        self.map_id = map_id;
                        self.move_to(x, y, z, 0);
                        return format!("Teletransportado via .goto para {} (map: {}, x: {:.1}, y: {:.1}, z: {:.1})", dest, map_id, x, y, z);
                    }
                }
                "Uso: .goto <poeta|sanctum|verteron|ishalgen|pandaemonium|altgard|abyss|inggison|gelkmaros>".to_string()
            }
            ".givekinah" => {
                if let Some(amt_str) = parts.get(1) {
                    if let Ok(amt) = amt_str.parse::<u64>() {
                        self.kinah = self.kinah.saturating_add(amt);
                        return format!("Adicionado {} Kinah. Saldo total: {}", amt, self.kinah);
                    }
                }
                "Uso: .givekinah <quantidade>".to_string()
            }
            ".spawn" => {
                if let Some(npc_id_str) = parts.get(1) {
                    return format!("NPC {} invocado com sucesso na posicao do jogador", npc_id_str);
                }
                "Uso: .spawn <npc_id>".to_string()
            }
            _ => format!("Comando GM desconhecido: {}", parts[0]),
        }
    }
}

/// Motor de execucao de testes automatizados de gameplay
pub struct GameplayTestRunner;

impl GameplayTestRunner {
    pub fn run_all_gameplay_scenarios() -> Vec<(&'static str, bool, String)> {
        let mut results = Vec::new();

        // 1. Criacao e ciclo de vida
        let mut player = SimulatedCharacter::new(1001, "AionTester", 1, 1, 210010000);
        results.push((
            "Character Lifecycle & Initialization",
            player.level == 1 && player.map_id == 210010000 && player.hp == 1500,
            format!("Char {} criado com sucesso no mapa {}", player.name, player.map_id),
        ));

        // 2. Movimentacao, Voo e Glide
        player.move_to(500.0, 600.0, 350.0, 45);
        player.jump_and_glide();
        results.push((
            "Continuous Movement & Gliding",
            player.x == 500.0 && player.y == 600.0 && player.is_gliding,
            format!("Movido para ({}, {}) com planar ativo", player.x, player.y),
        ));

        // 3. Selecao de alvo e combate
        player.select_target(210500); // Target NPC / Monster
        let dmg = player.physical_attack(210500);
        results.push((
            "Target Selection & Physical Combat",
            player.active_target == Some(210500) && dmg > 0,
            format!("Alvo selecionado 210500 e dano gerado: {}", dmg),
        ));

        // 4. Magias e Cooldowns
        let cast_res = player.cast_skill(1001, 210500, 50, 10, 100);
        assert!(cast_res.is_ok());
        let cd_blocked = player.cast_skill(1001, 210500, 50, 10, 105);
        results.push((
            "Skill Casting & Cooldown Throttling",
            cast_res.is_ok() && cd_blocked.is_err(),
            format!("Habilidade conjurada com dano {} e bloqueio de CD ativo", cast_res.unwrap()),
        ));

        // 5. Dano e Cura com Consumiveis
        player.add_item(160000001, 5); // 5 Minor Recovery Potions
        let died = player.take_damage(500);
        let pot_res = player.use_potion(160000001, 300, 100);
        results.push((
            "Damage Mitigation & Consumables Usage",
            !died && pot_res.is_ok() && player.hp == 1300,
            format!("Vida apos dano e pocao: {}/{}", player.hp, player.max_hp),
        ));

        // 6. Drops e Gestao do Cube
        player.add_item(100100500, 1); // Greatsword drop
        let equip_res = player.equip_item(100100500);
        results.push((
            "Monster Drop & Cube Item Equipment",
            equip_res.is_ok() && player.inventory.get(&100100500).unwrap().is_equipped,
            "Item dropado, armazenado no Cube e equipado no slot principal".to_string(),
        ));

        // 7. Comandos Administrativos GM
        let gm1 = player.execute_gm_command(".setlevel 65");
        let gm2 = player.execute_gm_command(".givekinah 5000000");
        let gm3 = player.execute_gm_command(".teleport 1322.0 1511.0 568.0");
        results.push((
            "GM Administrative Engine Commands",
            player.level == 65 && player.kinah == 5_050_000 && player.x == 1322.0,
            format!("GM: {}; {}; {}", gm1, gm2, gm3),
        ));

        // 8. Viagem Multi-Mapa com .goto
        let goto_poeta = player.execute_gm_command(".goto poeta");
        let poeta_ok = player.map_id == 210010000;
        let _goto_sanctum = player.execute_gm_command(".goto sanctum");
        let sanctum_ok = player.map_id == 110010000;
        let _goto_abyss = player.execute_gm_command(".goto abyss");
        let abyss_ok = player.map_id == 400010000;
        let goto_pandae = player.execute_gm_command(".goto pandaemonium");
        let pandae_ok = player.map_id == 120010000;
        results.push((
            "Multi-Map Teleportation via .goto Command",
            poeta_ok && sanctum_ok && abyss_ok && pandae_ok,
            format!("Teleportes validados: Poeta ({}), Sanctum, Abyss e Pandaemonium ({})", goto_poeta, goto_pandae),
        ));

        results
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_all_gameplay_scenarios_pass() {
        let results = GameplayTestRunner::run_all_gameplay_scenarios();
        for (name, success, info) in results {
            assert!(success, "Cenario falhou: {} - {}", name, info);
        }
    }
}

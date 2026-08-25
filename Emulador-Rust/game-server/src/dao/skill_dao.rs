use rusqlite::{params, Connection, Result};

pub struct SkillDao;

impl SkillDao {
    /// Skills iniciais de nível 1 por classe
    pub fn initial_skills_for_class(class_id: u32) -> Vec<(u32, u8)> {
        match class_id {
            1 | 2 => vec![(1, 1), (2, 1), (3, 1), (10, 1)],
            3 | 4 | 5 => vec![(20, 1), (21, 1), (22, 1), (25, 1)],
            6 | 7 | 8 => vec![(30, 1), (31, 1), (32, 1), (35, 1)],
            9 | 10 | 11 => vec![(40, 1), (41, 1), (42, 1), (45, 1)],
            _ => vec![(1, 1), (2, 1)],
        }
    }

    /// Salva as skills ativas do personagem
    pub fn salvar_skills(conn: &Connection, char_id: u32, skills: &[(u32, u8)]) -> Result<()> {
        let mut stmt = conn.prepare(
            "INSERT INTO character_skills (character_id, skill_id, skill_level)
             VALUES (?1, ?2, ?3)
             ON CONFLICT(character_id, skill_id) DO UPDATE SET skill_level = excluded.skill_level"
        )?;
        for &(skill_id, skill_level) in skills {
            stmt.execute(params![char_id as i64, skill_id as i64, skill_level as i64])?;
        }
        Ok(())
    }

    /// Carrega as skills do personagem
    pub fn carregar_skills(conn: &Connection, char_id: u32) -> Result<Vec<(u32, u8)>> {
        let mut stmt = conn.prepare(
            "SELECT skill_id, skill_level FROM character_skills WHERE character_id = ?1"
        )?;
        let rows = stmt.query_map(params![char_id as i64], |row| {
            let sid: i64 = row.get(0)?;
            let lvl: i64 = row.get(1)?;
            Ok((sid as u32, lvl as u8))
        })?;
        let mut res = Vec::new();
        for r in rows {
            res.push(r?);
        }
        Ok(res)
    }
}

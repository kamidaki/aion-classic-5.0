//! SpatialService - Streaming de Entidades e Broadcast de Movimento (Padrão Java AION)

use std::collections::{HashMap, HashSet};
use crate::game::character::Character;
use crate::game::engine::Coord;
use crate::game::entity::Entity;
use crate::game::message::{client as c, server as s};
use crate::game::{Messages, ServerUpdate};

pub const VISAO_PADRAO: f32 = 100.0;
pub const PASSO_DO_STREAM: f32 = 20.0;

pub fn raio_de_visao() -> f32 {
    std::env::var("AION_VISAO")
        .ok()
        .and_then(|v| v.trim().parse().ok())
        .unwrap_or(VISAO_PADRAO)
}

pub struct SpatialService;

impl SpatialService {
    /// Processa a movimentação de um personagem e atualiza o streaming espacial de NPCs
    pub fn handle_move(
        character_id: u32,
        client_id: u16,
        move_new: &c::MoveNew,
        characters: &mut HashMap<u32, Character>,
        npcs_em_cena: &mut HashMap<u32, (HashSet<u32>, Coord)>,
        entities: &[Entity],
        put_npc: &HashMap<u32, Vec<u8>>,
        messages: &mut Messages,
    ) {
        let Some(character) = characters.get_mut(&character_id) else {
            return;
        };

        let s_move_new = s::Message::MoveNew(move_new.calculate(character.id()));
        character.set_location(move_new.location());
        let aqui = *character.location();
        let id = character.id();

        messages.push_others(client_id, ServerUpdate::new(s_move_new));

        // NPC entra e sai de cena conforme o personagem anda. So recalcula depois de PASSO_DO_STREAM metros
        let andou = match npcs_em_cena.get(&id) {
            Some((_, de_onde)) => {
                let dx = aqui.x() - de_onde.x();
                let dy = aqui.y() - de_onde.y();
                let dz = aqui.z() - de_onde.z();
                dx * dx + dy * dy + dz * dz >= PASSO_DO_STREAM * PASSO_DO_STREAM
            }
            None => true,
        };

        if andou {
            let (entraram, sairam) =
                Self::atualiza_npcs_em_cena(id, client_id, aqui, npcs_em_cena, entities, put_npc, messages);
            if entraram + sairam > 0 {
                println!("INFO: cena: +{entraram} -{sairam} NPCs");
            }
        }
    }

    /// Popula a cena de quem acabou de entrar no mundo
    pub fn povoa_cena(
        character_id: u32,
        client_id: u16,
        aqui: Coord,
        npcs_em_cena: &mut HashMap<u32, (HashSet<u32>, Coord)>,
        entities: &[Entity],
        put_npc: &HashMap<u32, Vec<u8>>,
        messages: &mut Messages,
    ) {
        npcs_em_cena.remove(&character_id);
        let (enviados, _) =
            Self::atualiza_npcs_em_cena(character_id, client_id, aqui, npcs_em_cena, entities, put_npc, messages);
        println!(
            "INFO: {enviados} NPCs em cena de {} (raio {:.0}m)",
            entities.len(),
            raio_de_visao()
        );
    }

    /// Manda os NPCs que entraram no alcance e remove os que sairam
    pub fn atualiza_npcs_em_cena(
        character_id: u32,
        client_id: u16,
        aqui: Coord,
        npcs_em_cena: &mut HashMap<u32, (HashSet<u32>, Coord)>,
        entities: &[Entity],
        put_npc: &HashMap<u32, Vec<u8>>,
        messages: &mut Messages,
    ) -> (usize, usize) {
        let raio = raio_de_visao();
        let perto: HashSet<u32> = entities
            .iter()
            .filter(|e| {
                let la = e.location();
                let dx = la.x() - aqui.x();
                let dy = la.y() - aqui.y();
                let dz = la.z() - aqui.z();
                dx * dx + dy * dy + dz * dz <= raio * raio
            })
            .map(|e| e.id())
            .collect();

        let em_cena = match npcs_em_cena.get(&character_id) {
            Some((c, _)) => c.clone(),
            None => HashSet::new(),
        };

        let entraram: Vec<u32> = perto.difference(&em_cena).copied().collect();
        let sairam: Vec<u32> = em_cena.difference(&perto).copied().collect();

        for id in &sairam {
            messages.push_direct(
                client_id,
                ServerUpdate::new(s::Message::RemoveObject(s::RemoveObject::new(*id))),
            );
        }
        for id in &entraram {
            let Some(entity) = entities.iter().find(|e| e.id() == *id) else {
                continue;
            };
            let msg = match put_npc.get(id) {
                Some(p) => s::Message::Bruto(s::Bruto::new(
                    crate::game::message::capturado::PUT_NPC_OPCODE,
                    p.clone(),
                )),
                None => s::Message::PutNpc(s::PutNpc::new(entity)),
            };
            messages.push_direct(client_id, ServerUpdate::new(msg));
        }

        let contagem = (entraram.len(), sairam.len());
        npcs_em_cena.insert(character_id, (perto, aqui));
        contagem
    }
}

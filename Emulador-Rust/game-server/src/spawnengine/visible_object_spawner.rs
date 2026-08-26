//! VisibleObjectSpawner - Instanciador Especializado de Entidades Visíveis (Padrão Java Aion Classic 2.8 / 4.5)

use crate::engine::Coord;
use crate::entity::Entity;
use crate::spawnengine::types::{
    RiftSpawnTemplate, SpawnTemplate, StaticDoor, StaticDoorTemplate, StaticObject,
    StaticObjectTemplate,
};

pub struct VisibleObjectSpawner;

impl VisibleObjectSpawner {
    /// Spawna um NPC / Monstro no mundo
    pub fn spawn_npc(template: &SpawnTemplate, entity_id: u32) -> Entity {
        let mut entity = Entity::novo(
            entity_id,
            Coord::new(template.x, template.y, template.z),
            template.npc_id,
            template.name_id,
        );

        // Se for chefe ou elite, ajusta atributos de acordo com o template
        if template.npc_id >= 210000 && template.npc_id <= 220000 {
            // HP/Level base para criaturas normais/elites
            entity.set_level(20);
        }

        entity
    }

    /// Spawna um ponto de coleta (Gatherable / Material de Coleta)
    pub fn spawn_gatherable(template: &SpawnTemplate, entity_id: u32) -> Entity {
        let mut entity = Entity::novo(
            entity_id,
            Coord::new(template.x, template.y, template.z),
            template.npc_id,
            template.name_id,
        );
        entity.set_level(1);
        entity
    }

    /// Spawna uma porta estática (StaticDoor)
    pub fn spawn_static_door(template: &StaticDoorTemplate) -> StaticDoor {
        StaticDoor {
            door_id: template.door_id,
            world_id: template.world_id,
            x: template.x,
            y: template.y,
            z: template.z,
            is_open: template.is_open,
            door_type: template.door_type,
        }
    }

    /// Spawna um objeto estático (StaticObject - Baú, Obelisco de Bind, Correio)
    pub fn spawn_static_object(template: &StaticObjectTemplate) -> StaticObject {
        StaticObject {
            object_id: template.object_id,
            world_id: template.world_id,
            x: template.x,
            y: template.y,
            z: template.z,
            object_type: template.object_type,
        }
    }

    /// Spawna um portal de Fenda Dimensional (Rift Portal)
    pub fn spawn_rift(template: &RiftSpawnTemplate, entity_id: u32) -> Entity {
        Entity::novo(
            entity_id,
            Coord::new(template.x, template.y, template.z),
            template.rift_id,
            template.rift_id,
        )
    }

    /// Spawna uma armadilha de jogador (Ranger / Assassin Trap)
    pub fn spawn_trap(
        npc_id: u32,
        name_id: u32,
        location: Coord,
        _owner_id: u32,
        entity_id: u32,
    ) -> Entity {
        let mut entity = Entity::novo(entity_id, location, npc_id, name_id);
        entity.set_level(1);
        entity
    }

    /// Spawna um servo/totem de invocação (Spiritmaster / Chanter Servant)
    pub fn spawn_servant(
        npc_id: u32,
        name_id: u32,
        location: Coord,
        _owner_id: u32,
        entity_id: u32,
    ) -> Entity {
        Entity::novo(entity_id, location, npc_id, name_id)
    }

    /// Spawna uma pedra de ressurreição pessoal (Kisk)
    pub fn spawn_kisk(
        npc_id: u32,
        name_id: u32,
        location: Coord,
        _owner_id: u32,
        entity_id: u32,
    ) -> Entity {
        Entity::novo(entity_id, location, npc_id, name_id)
    }
}

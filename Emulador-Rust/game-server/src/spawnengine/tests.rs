#[cfg(test)]
mod tests {
    use std::collections::HashMap;
    use std::time::{Duration, Instant};

    use crate::engine::Coord;
    use crate::spawnengine::instance_rift_spawn_manager::InstanceRiftSpawnManager;
    use crate::spawnengine::spawn_engine::SpawnEngine;
    use crate::spawnengine::static_door_spawn_manager::StaticDoorSpawnManager;
    use crate::spawnengine::static_object_spawn_manager::StaticObjectSpawnManager;
    use crate::spawnengine::temporary_spawn_engine::TemporarySpawnEngine;
    use crate::spawnengine::types::{
        RiftSpawnTemplate, SpawnTemplate, StaticDoorTemplate, StaticObjectTemplate,
        TemporarySpawnInfo, WalkerPoint, WalkerRoute,
    };
    use crate::spawnengine::walker_formator::WalkerFormator;

    #[test]
    fn test_spawn_engine_add_and_respawn() {
        let mut engine = SpawnEngine::new();
        let mut entities = Vec::new();
        let mut put_npc = HashMap::new();

        // Adiciona spawn no mundo 210010000 (Poeta)
        let entity = engine.add_new_spawn(210010000, 210001, 210001, 100.0, 200.0, 300.0, 45, 1);
        assert_eq!(entity.npc_id(), 210001);
        entities.push(entity.clone());

        // Mata a entidade e agenda respawn
        engine.schedule_respawn(entity.id(), 1);

        // Tick imediato: ainda não passou o tempo
        engine.tick(Instant::now(), &mut entities, &mut put_npc);
        assert_eq!(entities.len(), 1);

        // Tick após 2 segundos: o monstro deve renascer
        engine.tick(
            Instant::now() + Duration::from_secs(2),
            &mut entities,
            &mut put_npc,
        );
        assert_eq!(entities.len(), 2);
    }

    #[test]
    fn test_static_doors() {
        let mut door_mgr = StaticDoorSpawnManager::new();
        door_mgr.register_template(StaticDoorTemplate {
            door_id: 101,
            world_id: 210010000,
            x: 1500.0,
            y: 1200.0,
            z: 200.0,
            is_open: false,
            door_type: 1,
        });

        assert_eq!(door_mgr.total_doors(), 1);
        let door = door_mgr.get_door(101).expect("Porta deve existir");
        assert!(!door.is_open);

        // Abre a porta
        assert!(door_mgr.set_door_state(101, true));
        assert!(door_mgr.get_door(101).unwrap().is_open);
    }

    #[test]
    fn test_static_objects() {
        let mut obj_mgr = StaticObjectSpawnManager::new();
        obj_mgr.register_template(StaticObjectTemplate {
            object_id: 5001,
            world_id: 220010000,
            x: 500.0,
            y: 600.0,
            z: 100.0,
            object_type: 2, // Caixa de correio / Postbox
        });

        assert_eq!(obj_mgr.total_objects(), 1);
        let obj = obj_mgr.get_object(5001).expect("Objeto deve existir");
        assert_eq!(obj.object_type, 2);
    }

    #[test]
    fn test_instance_rifts() {
        let mut rift_mgr = InstanceRiftSpawnManager::new();
        rift_mgr.register_rift_template(RiftSpawnTemplate {
            rift_id: 1,
            world_id: 210020000,      // Eltnen
            dest_world_id: 220020000, // Morheim
            dest_x: 200.0,
            dest_y: 300.0,
            dest_z: 400.0,
            x: 1000.0,
            y: 1000.0,
            z: 200.0,
            min_level: 20,
            max_level: 28,
            max_entries: 12,
            duration_secs: 3600,
        });

        let rift_entity = rift_mgr.open_rift(1, 0x8000_1000).expect("Rift deve abrir");
        assert_eq!(rift_entity.id(), 0x8000_1000);
        assert_eq!(rift_mgr.active_rift_count(), 1);

        // Jogador level 15 tenta usar (muito baixo)
        let err_low = rift_mgr.use_rift(1, 15);
        assert!(err_low.is_err());

        // Jogador level 50 tenta usar (muito alto)
        let err_high = rift_mgr.use_rift(1, 50);
        assert!(err_high.is_err());

        // Jogador level 25 usa com sucesso
        let success = rift_mgr.use_rift(1, 25);
        assert!(success.is_ok());
        let (dest_map, dest_pos) = success.unwrap();
        assert_eq!(dest_map, 220020000);
        assert_eq!(dest_pos, Coord::new(200.0, 300.0, 400.0));
    }

    #[test]
    fn test_temporary_day_night_spawns() {
        let mut temp_engine = TemporarySpawnEngine::new();
        let mut template = SpawnTemplate::new(1, 210500, 210500, 210010000, 100.0, 100.0, 100.0, 0, 0);
        // Spawn noturno: 22h às 06h
        template.temporary = Some(TemporarySpawnInfo::new(22, 6, 1.0));
        temp_engine.register_temporary_template(template);

        let mut next_id = 0x8000_2000;
        let mut id_gen = || {
            let id = next_id;
            next_id += 1;
            id
        };

        // Às 14h (dia): nenhum spawn ativo
        let (despawned, spawned) = temp_engine.on_hour_change(14, &mut id_gen);
        assert_eq!(despawned.len(), 0);
        assert_eq!(spawned.len(), 0);
        assert_eq!(temp_engine.active_count(), 0);

        // Às 23h (noite): monstro spawna
        let (despawned, spawned) = temp_engine.on_hour_change(23, &mut id_gen);
        assert_eq!(despawned.len(), 0);
        assert_eq!(spawned.len(), 1);
        assert_eq!(temp_engine.active_count(), 1);

        // Às 08h (manhã): monstro despawna
        let (despawned, spawned) = temp_engine.on_hour_change(8, &mut id_gen);
        assert_eq!(despawned.len(), 1);
        assert_eq!(spawned.len(), 0);
        assert_eq!(temp_engine.active_count(), 0);
    }

    #[test]
    fn test_walker_patrol_route() {
        let mut walker_mgr = WalkerFormator::new();
        let route = WalkerRoute::new(
            "poeta_patrol_1",
            vec![
                WalkerPoint::new(10.0, 0.0, 0.0, 0, 1),
                WalkerPoint::new(20.0, 0.0, 0.0, 0, 2),
            ],
            true,
        );
        walker_mgr.register_route(route);

        let mut entity = crate::entity::Entity::novo(100, Coord::new(0.0, 0.0, 0.0), 210001, 210001);
        assert!(walker_mgr.assign_route(100, "poeta_patrol_1"));

        let mut entities = vec![entity];
        walker_mgr.tick_walkers(&mut entities, Instant::now());

        // A entidade deve ter se movido em direção a x = 10.0
        assert!(entities[0].location().x() > 0.0);
    }
}

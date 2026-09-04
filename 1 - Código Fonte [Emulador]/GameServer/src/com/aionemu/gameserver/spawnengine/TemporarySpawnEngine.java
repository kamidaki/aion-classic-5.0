package com.aionemu.gameserver.spawnengine;

import com.aionemu.gameserver.model.TaskId;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.VisibleObject;
import com.aionemu.gameserver.model.templates.spawns.SpawnGroup;
import com.aionemu.gameserver.model.templates.spawns.SpawnTemplate;
import com.aionemu.gameserver.model.templates.spawns.TemporarySpawn;

import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;

public class TemporarySpawnEngine {

    private static final CopyOnWriteArrayList<SpawnGroup> temporarySpawns = new CopyOnWriteArrayList<>();
    private static final Map<SpawnGroup, Set<Integer>> tempSpawnInstanceMap = new ConcurrentHashMap<>();

    public static void spawnAll() {
        spawn(true);
    }

    public static void onHourChange() {
        despawn();
        spawn(false);
    }

    private static void despawn() {
        for (SpawnGroup spawn : temporarySpawns) {
            for (SpawnTemplate template : spawn.getSpawnTemplates()) {
                if (template.getTemporarySpawn().canDespawn()) {
                    VisibleObject object = template.getVisibleObject();
                    if (object == null) {
                        continue;
                    }
                    if (object instanceof Npc npc) {
                        if (!npc.getLifeStats().isAlreadyDead() && template.hasPool()) {
                            spawn.setTemplateUse(npc.getInstanceId(), template, false);
                        }
                        npc.getController().cancelTask(TaskId.RESPAWN);
                    }
                    if (object.isSpawned()) {
                        object.getController().onDelete();
                    }
                }
            }
        }
    }

    private static void spawn(boolean startCheck) {
        for (SpawnGroup spawn : temporarySpawns) {
            Set<Integer> instances = tempSpawnInstanceMap.get(spawn);
            if (instances == null) {
                continue;
            }
            if (spawn.hasPool()) {
                TemporarySpawn temporarySpawn = spawn.geTemporarySpawn();
                if (temporarySpawn.canSpawn() || (startCheck && spawn.getRespawnTime() != 0 && temporarySpawn.isInSpawnTime())) {
                    for (Integer instanceId : instances) {
                        spawn.resetTemplates(instanceId);
                        for (int pool = 0; pool < spawn.getPool(); pool++) {
                            SpawnTemplate template = spawn.getRndTemplate(instanceId);
                            SpawnEngine.spawnObject(template, instanceId);
                        }
                    }
                }
            } else {
                for (SpawnTemplate template : spawn.getSpawnTemplates()) {
                    TemporarySpawn temporarySpawn = template.getTemporarySpawn();
                    if (temporarySpawn.canSpawn() || (startCheck && !template.isNoRespawn() && temporarySpawn.isInSpawnTime())) {
                        for (Integer instanceId : instances) {
                            SpawnEngine.spawnObject(template, instanceId);
                        }
                    }
                }
            }
        }
    }

    /**
     * @param spawn
     * @param instanceId
     */
    public static void addSpawnGroup(SpawnGroup spawn, int instanceId) {
        temporarySpawns.addIfAbsent(spawn);
        tempSpawnInstanceMap.computeIfAbsent(spawn, _ -> ConcurrentHashMap.newKeySet()).add(instanceId);
    }
}


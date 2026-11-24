package com.aionemu.gameserver.model.templates.spawns.riftspawns;

import com.aionemu.gameserver.model.templates.spawns.SpawnGroup;
import com.aionemu.gameserver.model.templates.spawns.SpawnSpotTemplate;
import com.aionemu.gameserver.model.templates.spawns.SpawnTemplate;

/**
 * @author Lost Academy Team & Durak
 */
public class RiftSpawnTemplate extends SpawnTemplate {

	private int id;

	public RiftSpawnTemplate(SpawnGroup spawnGroup, SpawnSpotTemplate spot) {
		super(spawnGroup, spot);
	}

	public int getId() {
		return id;
	}

	public void setId(int id) {
		this.id = id;
	}

}

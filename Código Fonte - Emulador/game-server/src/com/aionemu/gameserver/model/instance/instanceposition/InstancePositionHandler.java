package com.aionemu.gameserver.model.instance.instanceposition;

import com.aionemu.gameserver.model.gameobjects.player.Player;

/**
 * @author Lost Academy Team & Durak
 */
public interface InstancePositionHandler {

	void initialize(int mapId, int instanceId);

	void port(Player player, int zone, int position);
}

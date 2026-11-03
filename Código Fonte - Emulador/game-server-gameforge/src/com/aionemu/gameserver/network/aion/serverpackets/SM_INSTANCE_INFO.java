package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.Arrays;
import java.util.Collection;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.PortalCooldown;
import com.aionemu.gameserver.model.templates.InstanceCooltime;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_INSTANCE_INFO extends AionServerPacket {

	private byte updateType; // 0 = reset existing data and write new info, 1 = update team info (leader is always first), 2 = add/overwrite data without resetting other
	private Collection<Player> players; // list of players for which their cooldown info will be sent (as of 4.7 there are client bugs which can crash it on 4+ players)
	private Integer[] instanceIds; // list of instances for which the data should be updated

	public SM_INSTANCE_INFO(byte updateType, Player player, Integer... instanceId) {
		this(updateType, Arrays.asList(player), instanceId);
	}

	public SM_INSTANCE_INFO(byte updateType, Collection<Player> players, Integer... instanceId) {
		this.updateType = updateType;
		this.players = players;
		this.instanceIds =  instanceId.length > 0 ? instanceId : DataManager.INSTANCE_COOLTIME_DATA.getInstanceCooltimes().keySet().toArray(new Integer[0]);
	}

	@Override
	protected void writeImpl(AionConnection con) {
		int cooldownId = instanceIds.length == 1 ? DataManager.INSTANCE_COOLTIME_DATA.getInstanceCooltimeByWorldId(instanceIds[0]).getId() : 0;
		// 5.0 Classic header: 9 bytes (wire verified against packet [098])
		writeC(updateType);
		writeC(cooldownId);
		writeD(0);
		writeC(1);
		writeH(players.size());

		for (Player player : players) {
			writeD(player.getObjectId());
			writeH(instanceIds.length);
			for (int worldId : instanceIds) {
				PortalCooldown cooldown = player.getPortalCooldownList().getPortalCooldown(worldId);
				InstanceCooltime cooltime = DataManager.INSTANCE_COOLTIME_DATA.getInstanceCooltimeByWorldId(worldId);
				// 5.0 Classic entry: exactly 22 bytes (5 ints + 1 short)
				writeD(cooltime.getId());
				writeD(0);
				writeD(cooldown == null ? 0 : (int) (cooldown.getReuseTime() - System.currentTimeMillis()) / 1000);
				writeD(cooldown == null ? 0 : cooldown.getEnterCount());
				writeD(0);
				writeH(0);
			}
			writeS(player.getName());
		}
	}
}

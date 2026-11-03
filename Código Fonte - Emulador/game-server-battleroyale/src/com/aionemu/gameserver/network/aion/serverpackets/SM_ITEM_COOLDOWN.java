package com.aionemu.gameserver.network.aion.serverpackets;
 
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import com.aionemu.gameserver.model.items.ItemCooldown;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_ITEM_COOLDOWN extends AionServerPacket {

	private final Map<Integer, ItemCooldown> cooldowns;

	public SM_ITEM_COOLDOWN(Map<Integer, ItemCooldown> cooldowns) {
		this.cooldowns = cooldowns;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		if (cooldowns == null || cooldowns.isEmpty()) {
			writeH(0);
			return;
		}
		long currentTime = System.currentTimeMillis();
		List<Map.Entry<Integer, ItemCooldown>> active = new ArrayList<>();
		for (Map.Entry<Integer, ItemCooldown> entry : cooldowns.entrySet()) {
			if (entry.getValue() != null && entry.getValue().getReuseTime() > currentTime) {
				active.add(entry);
			}
		}
		writeH(active.size());
		for (Map.Entry<Integer, ItemCooldown> entry : active) {
			writeH(entry.getKey());
			int left = (int) Math.max(0, (entry.getValue().getReuseTime() - currentTime) / 1000);
			writeD(left);
			writeD(entry.getValue().getUseDelay());
		}
	}
}

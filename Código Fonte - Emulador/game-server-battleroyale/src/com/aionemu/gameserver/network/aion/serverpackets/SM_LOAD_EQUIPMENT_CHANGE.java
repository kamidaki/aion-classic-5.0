package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.Map.Entry;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.equipmentset.EquipmentSetting;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

public class SM_LOAD_EQUIPMENT_CHANGE extends AionServerPacket {

	private final Player player;

	public SM_LOAD_EQUIPMENT_CHANGE(Player player) {
		this.player = player;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(player.getPlayerEquipSettingList().size());
		for (Entry<Integer, EquipmentSetting> entry : player.getPlayerEquipSettingList().entrySet()) {
			writeD(entry.getKey());
			entry.getValue().getObjIds().forEach(this::writeD);
		}
	}
}

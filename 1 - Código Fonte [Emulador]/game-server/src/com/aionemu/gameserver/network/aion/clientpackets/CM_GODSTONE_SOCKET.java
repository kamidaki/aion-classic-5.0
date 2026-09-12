package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.item.ItemSocketService;

/**
 * Socketing of a godstone. Classic 5.0 sends it from the game menu window, with no NPC involved, as the target weapon
 * followed by the godstone (measured on the official server).
 *
 * @author Lost Academy Team & Durak
 */
public class CM_GODSTONE_SOCKET extends AionClientPacket {

	private int weaponObjectId;
	private int stoneObjectId;

	public CM_GODSTONE_SOCKET(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		weaponObjectId = readD();
		stoneObjectId = readD();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		Item weapon = player.getInventory().getItemByObjId(weaponObjectId);
		if (weapon == null) {
			boolean isEquipped = player.getEquipment().getEquippedItemByObjId(weaponObjectId) != null;
			sendPacket(isEquipped ? SM_SYSTEM_MESSAGE.STR_GIVE_ITEM_PROC_CANNOT_GIVE_PROC_TO_EQUIPPED_ITEM()
				: SM_SYSTEM_MESSAGE.STR_GIVE_ITEM_PROC_NO_TARGET_ITEM());
			return;
		}
		ItemSocketService.socketGodstone(player, weapon, stoneObjectId);
	}
}

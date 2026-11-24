package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.item.ItemSocketService;

/**
 * Godstone removal through the Classic 5.0 option clear window (game menu, no NPC). An item holds a single godstone, so
 * the client sends only the item (measured on the official server).
 *
 * @author Lost Academy Team & Durak
 */
public class CM_GODSTONE_CLEAR extends AionClientPacket {

	private int itemObjectId;

	public CM_GODSTONE_CLEAR(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		itemObjectId = readD();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		Item item = player.getEquipment().getEquippedItemByObjId(itemObjectId);
		if (item == null && (item = player.getInventory().getItemByObjId(itemObjectId)) == null) {
			sendPacket(SM_SYSTEM_MESSAGE.STR_GIVE_ITEM_PROC_CLEAR_NOT_FIND());
			return;
		}
		ItemSocketService.clearGodstone(player, item);
	}
}

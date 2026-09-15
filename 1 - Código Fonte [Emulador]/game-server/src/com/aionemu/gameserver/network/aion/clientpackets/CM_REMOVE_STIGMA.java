package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_UPDATE_PLAYER_APPEARANCE;
import com.aionemu.gameserver.services.StigmaService;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * CM_REMOVE_STIGMA (0x003C / 0x136) - Classic 5.0 Stigma window unequip request (4 bytes [D itemObjId]).
 *
 * @author Lost Academy Team & Durak
 */
public class CM_REMOVE_STIGMA extends AionClientPacket {

	private int itemObjId;

	public CM_REMOVE_STIGMA(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		itemObjId = readD();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player == null)
			return;

		Item item = player.getEquipment().getEquippedItemByObjId(itemObjId);
		if (item == null)
			return;

		if (!StigmaService.checkUnequip(player, item))
			return;

		Item resultItem = player.getEquipment().unEquipItem(itemObjId, item.getEquipmentSlot(), (byte) 0);
		if (resultItem == null && player.getInventory().isFull()) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_UI_INVENTORY_FULL());
			return;
		}

		PacketSendUtility.broadcastPacket(player,
			new SM_UPDATE_PLAYER_APPEARANCE(player.getObjectId(), player.getEquipment().getEquippedForAppearance()), true);
	}
}

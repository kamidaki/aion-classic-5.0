package com.aionemu.gameserver.model.templates.item.actions;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.Persistable.PersistentState;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_UPDATE_PLAYER_APPEARANCE;
import com.aionemu.gameserver.services.item.ItemPacketService;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * @author Lost Academy Team & Durak
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "DyeAction")
public class DyeAction extends AbstractItemAction {

	@XmlAttribute(name = "color")
	protected String color;
	@XmlAttribute
	private Integer minutes;

	@Override
	public boolean canAct(Player player, Item parentItem, Item targetItem, Object... params) {
		if (targetItem == null) { // nothing to dye
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_ITEM_COLOR_ERROR());
			return false;
		}
		return true;
	}

	@Override
	public void act(Player player, Item parentItem, Item targetItem, Object... params) {
		if (targetItem != null)
			dyeItem(player, parentItem, targetItem);
	}

	private void dyeItem(Player player, Item parentItem, Item targetItem) {
		if (!targetItem.getItemSkinTemplate().isItemDyePermitted())
			return;
		if (!player.getInventory().decreaseByObjectId(parentItem.getObjectId(), 1))
			return;
		targetItem.setItemColor(getColor());
		if (minutes != null)
			targetItem.setColorExpireTime((int) (System.currentTimeMillis() / 1000 + minutes * 60));
		else
			targetItem.setColorExpireTime(0);
		if (targetItem.getItemColor() == null) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_ITEM_COLOR_REMOVE_SUCCEED(targetItem.getL10n()));
		} else {
			PacketSendUtility.sendPacket(player,
				SM_SYSTEM_MESSAGE.STR_ITEM_COLOR_CHANGE_SUCCEED(targetItem.getL10n(), parentItem.getL10n()));
		}

		// item is equipped, so need broadcast packet
		if (player.getEquipment().getEquippedItemByObjId(targetItem.getObjectId()) != null) {
			PacketSendUtility.broadcastPacket(player,
				new SM_UPDATE_PLAYER_APPEARANCE(player.getObjectId(), player.getEquipment().getEquippedForAppearance()), true);
			player.getEquipment().setPersistentState(PersistentState.UPDATE_REQUIRED);
		} else { // item is not equipped
			player.getInventory().setPersistentState(PersistentState.UPDATE_REQUIRED);
		}

		ItemPacketService.updateItemAfterInfoChange(player, targetItem);
	}

	public Integer getColor() {
		return color.equals("no") ? null : Integer.parseInt(color, 16);
	}
}

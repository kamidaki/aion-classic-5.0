package com.aionemu.gameserver.services.player;

import com.aionemu.gameserver.dao.PlayerWardrobeDAO;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.DescriptionId;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.WardrobeEntry;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.model.templates.item.actions.DyeAction;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_UPDATE_PLAYER_APPEARANCE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_USER_CLASSIC_WARDROBE_DATA_UPDATED;
import com.aionemu.gameserver.network.aion.serverpackets.SM_USER_CLASSIC_WARDROBE_INFO_UPDATED;
import com.aionemu.gameserver.network.aion.serverpackets.SM_USER_CLASSIC_WARDROBE_LOAD;
import com.aionemu.gameserver.services.item.ItemPacketService;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.idfactory.IDFactory;

public class PlayerWardrobeService {

	public void onEnterWorld(Player player) {
		PlayerWardrobeDAO.loadWardrobe(player);
		PacketSendUtility.sendPacket(player, new SM_USER_CLASSIC_WARDROBE_LOAD(player));
	}

	public void onExtendWardrobe(Player player, int unk) {
		ItemTemplate template = DataManager.ITEM_DATA.getItemTemplate(186000166);
		if (player.getInventory().decreaseByItemId(186000166, 1)) {
			player.getCommonData().setWardrobeSlot(player.getCommonData().getWardrobeSlot() + 1);
			PacketSendUtility.sendPacket(player, new SM_USER_CLASSIC_WARDROBE_INFO_UPDATED(unk));
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1401551));
			if (template != null) {
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1400333, new DescriptionId(template.getNameId())));
			}
		}
	}

	public void onRegisterItem(Player player, int objectId) {
		Item skin = player.getInventory().getItemByObjId(objectId);
		if (skin != null && player.getInventory().decreaseByObjectId(objectId, 1)) {
			WardrobeEntry entry = new WardrobeEntry(IDFactory.getInstance().nextId(), skin.getItemId(), 0, false);
			player.getPlayerWardrobe().put(entry.getObjectId(), entry);
			PlayerWardrobeDAO.addItem(player, entry);
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1401541, new DescriptionId(skin.getItemTemplate().getNameId())));
			PacketSendUtility.sendPacket(player, new SM_USER_CLASSIC_WARDROBE_DATA_UPDATED(1, entry));
		}
	}

	public void onReskin(Player player, int objectId, int itemObj) {
		Item item = player.getInventory().getItemByObjId(itemObj);
		WardrobeEntry entry = player.getPlayerWardrobe().get(objectId);
		if (item != null && entry != null && player.getInventory().tryDecreaseKinah(14125)) {
			item.setItemSkinTemplate(entry.getItemSkinTemplate());
			item.setItemColor(entry.getColor());
			ItemPacketService.updateItemAfterInfoChange(player, item);
			PacketSendUtility.broadcastPacket(player, new SM_UPDATE_PLAYER_APPEARANCE(player.getObjectId(), player.getEquipment().getEquippedForAppearance()), true);
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1300483, new DescriptionId(item.getItemTemplate().getNameId())));
		}
	}

	public void onLikeEntry(Player player, int objectId, boolean like) {
		WardrobeEntry entry = player.getPlayerWardrobe().get(objectId);
		if (entry != null) {
			entry.setLiked(like);
			PlayerWardrobeDAO.updateItem(player, entry);
			if (like) {
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1401543, new DescriptionId(entry.getItemSkinTemplate().getNameId())));
			}
			PacketSendUtility.sendPacket(player, new SM_USER_CLASSIC_WARDROBE_DATA_UPDATED(4, entry));
		}
	}

	public void onApplyDye(Player player, int skinObj, int dyeObj) {
		WardrobeEntry entry = player.getPlayerWardrobe().get(skinObj);
		Item colorObject = player.getInventory().getItemByObjId(dyeObj);
		if (entry != null && colorObject != null && player.getInventory().decreaseByObjectId(dyeObj, 1)) {
			if (colorObject.getItemTemplate().getActions() != null &&
					colorObject.getItemTemplate().getActions().getItemActions() != null &&
					!colorObject.getItemTemplate().getActions().getItemActions().isEmpty()) {
				Object action = colorObject.getItemTemplate().getActions().getItemActions().get(0);
				if (action instanceof DyeAction) {
					DyeAction color = (DyeAction) action;
					if (color.getColor() == null) {
						entry.setColor(0);
						PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1401566, new DescriptionId(entry.getItemSkinTemplate().getNameId())));
					} else {
						int rgb = color.getColor();
						int bgra = 0xFF | ((rgb & 0xFF) << 24) | ((rgb & 0xFF00) << 8) | ((rgb & 0xFF0000) >>> 8);
						entry.setColor(bgra);
						PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1401565, new DescriptionId(entry.getItemSkinTemplate().getNameId()), new DescriptionId(colorObject.getNameId())));
					}
					PacketSendUtility.sendPacket(player, new SM_USER_CLASSIC_WARDROBE_DATA_UPDATED(3, entry));
					PlayerWardrobeDAO.updateItem(player, entry);
				}
			}
		}
	}

	public void onDelete(Player player, int objectId) {
		WardrobeEntry entry = player.getPlayerWardrobe().get(objectId);
		if (entry != null) {
			PlayerWardrobeDAO.deleteItem(player, entry);
			player.getPlayerWardrobe().remove(objectId);
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1401542, new DescriptionId(entry.getItemSkinTemplate().getNameId())));
			PacketSendUtility.sendPacket(player, new SM_USER_CLASSIC_WARDROBE_DATA_UPDATED(2, entry));
		}
	}

	public static PlayerWardrobeService getInstance() {
		return SingletonHolder.instance;
	}

	private static class SingletonHolder {
		protected static final PlayerWardrobeService instance = new PlayerWardrobeService();
	}
}

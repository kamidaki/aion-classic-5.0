package com.aionemu.gameserver.services;

import com.aionemu.gameserver.dao.InventoryDAO;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.Persistable.PersistentState;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.item.ItemPacketService;
import com.aionemu.gameserver.services.item.ItemSocketService;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * @author Lost Academy Team & Durak
 */
public class ArmsfusionService {

	public static void fusionWeapons(Player player, int mainWeaponObjId, int fuseWeaponObjId) {
		Item mainWeapon = player.getInventory().getItemByObjId(mainWeaponObjId);
		Item fuseWeapon = player.getInventory().getItemByObjId(fuseWeaponObjId);

		// Fusioned weapons must have same type
		if (mainWeapon.getItemTemplate().getItemGroup() != fuseWeapon.getItemTemplate().getItemGroup()) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_COMPOUND_ERROR_DIFFERENT_TYPE());
			return;
		}

		// Second weapon must have inferior or equal lvl. in relation to first weapon
		if (fuseWeapon.getItemTemplate().getLevel() > mainWeapon.getItemTemplate().getLevel()) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_COMPOUND_ERROR_MAIN_REQUIRE_HIGHER_LEVEL());
			return;
		}

		mainWeapon.setFusionedItem(fuseWeapon);
		ItemSocketService.copyFusionStones(fuseWeapon, mainWeapon);
		mainWeapon.setPersistentState(PersistentState.UPDATE_REQUIRED);
		InventoryDAO.store(mainWeapon, player);

		ItemPacketService.updateItemAfterInfoChange(player, mainWeapon);
		PacketSendUtility.sendPacket(player,
				SM_SYSTEM_MESSAGE.STR_COMPOUND_SUCCESS(mainWeapon.getL10n(), fuseWeapon.getL10n()));
	}

	public static void breakWeapons(Player player, int weaponToBreakUniqueId) {
		Item weaponToBreak = player.getInventory().getItemByObjId(weaponToBreakUniqueId);

		if (!weaponToBreak.hasFusionedItem()) {
			PacketSendUtility.sendPacket(player,
					SM_SYSTEM_MESSAGE.STR_DECOMPOUND_ERROR_NOT_AVAILABLE(weaponToBreak.getL10n()));
			return;
		}

		weaponToBreak.setFusionedItem(null);
		InventoryDAO.store(weaponToBreak, player);
		ItemPacketService.updateItemAfterInfoChange(player, weaponToBreak);
		PacketSendUtility.sendPacket(player,
				SM_SYSTEM_MESSAGE.STR_COMPOUNDED_ITEM_DECOMPOUND_SUCCESS(weaponToBreak.getL10n()));
	}
}

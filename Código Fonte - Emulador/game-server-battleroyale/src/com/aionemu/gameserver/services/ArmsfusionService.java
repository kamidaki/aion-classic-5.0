package com.aionemu.gameserver.services;

import java.util.Collections;

import com.aionemu.gameserver.dao.InventoryDAO;
import com.aionemu.gameserver.dao.ItemStoneListDAO;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.Persistable.PersistentState;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.items.ManaStone;
import com.aionemu.gameserver.model.items.storage.StorageType;
import com.aionemu.gameserver.model.templates.item.ItemQuality;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.network.aion.serverpackets.SM_INVENTORY_UPDATE_ITEM;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_UPDATE_PLAYER_APPEARANCE;
import com.aionemu.gameserver.services.item.ItemFactory;
import com.aionemu.gameserver.services.item.ItemPacketService;
import com.aionemu.gameserver.services.item.ItemSocketService;
import com.aionemu.gameserver.services.trade.PricesService;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.audit.AuditLogger;
import com.aionemu.gameserver.utils.idfactory.IDFactory;

/**
 * @author Lost Academy Team & Durak
 */
public class ArmsfusionService {

	public static void fusionWeapons(Player player, int mainWeaponObjId, int fuseWeaponObjId) {
		Item mainWeapon = player.getInventory().getItemByObjId(mainWeaponObjId);
		if (mainWeapon == null) {
			mainWeapon = player.getEquipment().getEquippedItemByObjId(mainWeaponObjId);
		}
		Item fuseWeapon = player.getInventory().getItemByObjId(fuseWeaponObjId);
		if (fuseWeapon == null) {
			fuseWeapon = player.getEquipment().getEquippedItemByObjId(fuseWeaponObjId);
		}

		if (mainWeapon == null || fuseWeapon == null) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_COMPOUND_ITEM_NO_TARGET_ITEM());
			AuditLogger.log(player, "tried to fuse weapons he doesn't have (obj IDs:" + mainWeaponObjId + ", " + fuseWeaponObjId + ")");
			return;
		}

		if (!mainWeapon.getItemTemplate().isCanFuse() || !fuseWeapon.getItemTemplate().isCanFuse()) {
			Item item = mainWeapon.getItemTemplate().isCanFuse() ? mainWeapon : fuseWeapon;
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_COMPOUND_ERROR_NOT_AVAILABLE(item.getL10n()));
			AuditLogger.log(player,
				"tried to fuse item " + fuseWeapon.getItemId() + " onto " + mainWeapon.getItemId() + " (" + item.getItemId() + " isn't fusible)");
			return;
		}

		long basePricePerLevelSquared = getBasePricePerLevelSquared(mainWeapon.getItemTemplate().getItemQuality());
		int level = mainWeapon.getItemTemplate().getLevel();
		long price = PricesService.getPriceForService(basePricePerLevelSquared * level * level, player.getRace());

		if (player.getInventory().getKinah() < price) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_COMPOUND_ERROR_NOT_ENOUGH_MONEY(mainWeapon.getL10n(), fuseWeapon.getL10n()));
			return;
		}

		if (mainWeapon.getTemporaryExchangeTime() != 0) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_COMPOUND_ERROR_TEMPORARY_EXCHANGE_ITEM());
			return;
		}

		// Fusioned weapons must be not fusioned
		if (mainWeapon.hasFusionedItem() || fuseWeapon.hasFusionedItem()) {
			Item item = mainWeapon.hasFusionedItem() ? mainWeapon : fuseWeapon;
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_COMPOUND_ERROR_NOT_AVAILABLE(item.getL10n()));
			return;
		}

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

		// You can not combine Conditioning and Augmenting
		if (mainWeapon.getImprovement() != null && fuseWeapon.getImprovement() != null) {
			if (mainWeapon.getImprovement().getChargeWay() != fuseWeapon.getImprovement().getChargeWay()) {
				PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_COMPOUND_ERROR_NOT_COMPARABLE_ITEM());
				return;
			}
		}

		if (fuseWeapon.isEquipped()) {
			player.getEquipment().unEquipItem(fuseWeapon.getObjectId(), false);
		}
		Item fusionPart = newFusionPart(fuseWeapon);
		if (fusionPart == null)
			return;
		if (!player.getInventory().decreaseByObjectId(fuseWeaponObjId, 1)) {
			IDFactory.getInstance().releaseId(fusionPart.getObjectId());
			return;
		}
		mainWeapon.setFusionedItem(fusionPart);
		ItemSocketService.copyFusionStones(fuseWeapon, mainWeapon);
		mainWeapon.setPersistentState(PersistentState.UPDATE_REQUIRED);
		InventoryDAO.store(mainWeapon, player);
		if (mainWeapon.hasFusionStones()) {
			ItemStoneListDAO.save(Collections.singletonList(mainWeapon));
		}

		if (mainWeapon.isEquipped()) {
			player.getEquipment().notifyItemUnequip(mainWeapon);
			player.getEquipment().notifyItemEquipped(mainWeapon);
			player.getLifeStats().updateCurrentStats();
			player.getGameStats().updateStatsAndSpeedVisually();
			PacketSendUtility.sendPacket(player,
				new SM_INVENTORY_UPDATE_ITEM(player, mainWeapon, ItemPacketService.ItemUpdateType.EQUIP_UNEQUIP));
			PacketSendUtility.broadcastPacket(player,
				new SM_UPDATE_PLAYER_APPEARANCE(player.getObjectId(), player.getEquipment().getEquippedForAppearance()), true);
		}

		ItemPacketService.updateItemAfterInfoChange(player, mainWeapon);
		if (mainWeapon.isEquipped()) {
			PacketSendUtility.sendPacket(player,
				new SM_INVENTORY_UPDATE_ITEM(player, mainWeapon, ItemPacketService.ItemUpdateType.EQUIP_UNEQUIP));
		}
		player.getInventory().decreaseKinah(price);
		PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_COMPOUND_SUCCESS(mainWeapon.getL10n(), fuseWeapon.getL10n()));
	}

	/**
	 * The fused weapon's own row is deleted and its object ID released on the next inventory save, so the fused part needs an ID of its own
	 * (the same thing Item's constructor does when a fused weapon is loaded). Keeping the released ID made the next new item (e.g. a
	 * looted manastone) share it with the fused part, and the client drew that item in the fusion slot.
	 */
	public static Item newFusionPart(Item fuseWeapon) {
		Item fusionPart = ItemFactory.newItem(fuseWeapon.getItemTemplate().getTemplateId());
		if (fusionPart == null)
			return null;
		if (fuseWeapon.getBonusStatsId() > 0)
			fusionPart.setBonusStats(fuseWeapon.getBonusStatsId(), false);
		if (fuseWeapon.getOptionalSockets() > 0)
			fusionPart.setOptionalSockets(fuseWeapon.getOptionalSockets());
		if (fuseWeapon.getEnchantLevel() > 0)
			fusionPart.setEnchantLevel(fuseWeapon.getEnchantLevel());
		return fusionPart;
	}

	private static long getBasePricePerLevelSquared(ItemQuality rarity) {
		switch (rarity) {
			case JUNK:
			case COMMON:
				return 200;
			case RARE:
				return 250;
			case LEGEND:
			case LEGENDARY:
				return 300;
			case UNIQUE:
				return 400;
			case EPIC:
				return 500;
			case MYTHIC:
			default:
				return 600;
		}
	}

	public static Item unfuseWeapon(Player player, Item mainWeapon) {
		if (player.getInventory().isFull()) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_UI_INVENTORY_FULL());
			return null;
		}

		ItemTemplate fusedTemplate = mainWeapon.getFusionedItemTemplate();
		if (fusedTemplate == null) {
			return null;
		}

		Item unfusedItem = mainWeapon.getFusionedItem();
		int fusedEnchant = mainWeapon.getFusionedItemEnchant();
		if (unfusedItem == null) {
			unfusedItem = ItemFactory.newItem(fusedTemplate.getTemplateId());
			if (unfusedItem == null) {
				return null;
			}
			int fusedBonusStats = mainWeapon.getFusionedItemBonusStatsId();
			int fusedSockets = mainWeapon.getFusionedItemOptionalSockets();
			if (fusedBonusStats > 0) {
				unfusedItem.setBonusStats(fusedBonusStats, false);
			}
			if (fusedSockets > 0) {
				unfusedItem.setOptionalSockets(fusedSockets);
			}
		}

		// Clear any existing stones on unfusedItem and synchronize with mainWeapon's current fusion stones
		ItemSocketService.removeAllManastone(player, unfusedItem);
		if (mainWeapon.hasFusionStones()) {
			for (ManaStone ms : mainWeapon.getFusionStones()) {
				ItemSocketService.addManaStone(unfusedItem, ms.getItemId(), false);
			}
		}

		// Classic 5.0: The secondary weapon retains its enchant level intact
		if (fusedEnchant > 0) {
			unfusedItem.setEnchantLevel(fusedEnchant);
		}

		// Fusion stone and fused bonus stats can only be ended while the fusion data below is still intact
		if (mainWeapon.isEquipped())
			player.getEquipment().notifyItemUnequip(mainWeapon);

		// Clear fusion stones from main weapon
		ItemSocketService.removeAllFusionStone(player, mainWeapon);

		// Clear fusion from main weapon
		mainWeapon.setFusionedItem(null);
		mainWeapon.setPersistentState(PersistentState.UPDATE_REQUIRED);
		InventoryDAO.store(mainWeapon, player);

		// Return secondary item to inventory
		unfusedItem.setEquipped(false);
		unfusedItem.setEquipmentSlot(0);
		unfusedItem.setPersistentState(PersistentState.NEW);
		player.getInventory().add(unfusedItem);
		InventoryDAO.store(unfusedItem, player);
		if (unfusedItem.hasManaStones()) {
			ItemStoneListDAO.save(Collections.singletonList(unfusedItem));
		}

		// Recalculate stats and visuals if equipped
		if (mainWeapon.isEquipped()) {
			player.getEquipment().notifyItemEquipped(mainWeapon);
			player.getLifeStats().updateCurrentStats();
			player.getGameStats().updateStatsAndSpeedVisually();
			PacketSendUtility.sendPacket(player,
				new SM_INVENTORY_UPDATE_ITEM(player, mainWeapon, ItemPacketService.ItemUpdateType.EQUIP_UNEQUIP));
			PacketSendUtility.broadcastPacket(player, new SM_UPDATE_PLAYER_APPEARANCE(player.getObjectId(), player.getEquipment().getEquippedForAppearance()), true);
		}

		ItemPacketService.updateItemAfterInfoChange(player, mainWeapon);
		if (mainWeapon.isEquipped()) {
			PacketSendUtility.sendPacket(player,
				new SM_INVENTORY_UPDATE_ITEM(player, mainWeapon, ItemPacketService.ItemUpdateType.EQUIP_UNEQUIP));
		}
		PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_COMPOUNDED_ITEM_DECOMPOUND_SUCCESS(mainWeapon.getL10n()));

		return unfusedItem;
	}

	public static void breakWeapons(Player player, int weaponToBreakUniqueId) {
		Item weaponToBreak = player.getInventory().getItemByObjId(weaponToBreakUniqueId);
		if (weaponToBreak == null) {
			weaponToBreak = player.getEquipment().getEquippedItemByObjId(weaponToBreakUniqueId);
		}

		if (weaponToBreak == null) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_DECOMPOUND_ITEM_NO_TARGET_ITEM());
			return;
		}

		if (!weaponToBreak.hasFusionedItem()) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_DECOMPOUND_ERROR_NOT_AVAILABLE(weaponToBreak.getL10n()));
			return;
		}

		unfuseWeapon(player, weaponToBreak);
	}
}

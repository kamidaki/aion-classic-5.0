package com.aionemu.gameserver.services;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.configs.main.CustomConfig;
import com.aionemu.gameserver.dao.InventoryDAO;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.Persistable.PersistentState;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.items.ManaStone;
import com.aionemu.gameserver.model.items.storage.IStorage;
import com.aionemu.gameserver.model.items.storage.StorageType;
import com.aionemu.gameserver.model.stats.listeners.ItemEquipmentListener;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.services.item.ItemPacketService;
import com.aionemu.gameserver.services.item.ItemService;
import com.aionemu.gameserver.services.item.ItemSocketService;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * WeaponFusionSplitService - Classic 5.0.
 * Splits weapon fusions stored by legacy pre-5.0 systems on login.
 */
public class WeaponFusionSplitService {

	private static final Logger log = LoggerFactory.getLogger(WeaponFusionSplitService.class);

	private static final StorageType[] SEARCHED_STORAGES = { StorageType.CUBE, StorageType.REGULAR_WAREHOUSE,
		StorageType.ACCOUNT_WAREHOUSE };

	public static void onPlayerLogin(Player player) {
		if (!CustomConfig.SPLIT_STORED_WEAPON_FUSIONS) {
			return;
		}
		List<Item> fusedItems = collectFusedItems(player);
		if (fusedItems.isEmpty()) {
			return;
		}
		int splitCount = 0;
		int postponedCount = 0;
		for (Item fusedItem : fusedItems) {
			if (split(player, fusedItem)) {
				splitCount++;
			} else {
				postponedCount++;
			}
		}
		if (splitCount > 0) {
			log.info("[FUSAO] " + splitCount + " arma(s) fundida(s) separada(s) para " + player.getName());
			PacketSendUtility.sendMessage(player, "Suas armas fundidas foram separadas: a arma secundaria voltou para o inventario.");
		}
		if (postponedCount > 0) {
			log.warn("[FUSAO] " + postponedCount + " arma(s) de " + player.getName() + " nao puderam ser separadas: inventario cheio");
			PacketSendUtility.sendMessage(player, "Libere espaco no inventario para separar o restante das suas armas fundidas.");
		}
	}

	private static List<Item> collectFusedItems(Player player) {
		Map<Integer, Item> fusedItems = new LinkedHashMap<>();
		for (Item item : player.getEquipment().getEquippedItems()) {
			if (item.hasFusionedItem()) {
				fusedItems.put(item.getObjectId(), item);
			}
		}
		for (StorageType storageType : SEARCHED_STORAGES) {
			IStorage storage = player.getStorage(storageType.getId());
			if (storage == null) {
				continue;
			}
			for (Item item : storage.getItems()) {
				if (item.hasFusionedItem()) {
					fusedItems.put(item.getObjectId(), item);
				}
			}
		}
		return new ArrayList<>(fusedItems.values());
	}

	private static boolean split(Player player, Item item) {
		ItemTemplate secondaryTemplate = item.getFusionedItemTemplate();
		if (secondaryTemplate == null) {
			return false;
		}
		List<Integer> stoneIds = new ArrayList<>();
		if (item.hasFusionStones()) {
			for (ManaStone stone : item.getFusionStones()) {
				stoneIds.add(stone.getItemId());
			}
		}
		if (player.getInventory().getFreeSlots() < 1 + stoneIds.size()) {
			return false;
		}
		boolean equipped = item.isEquipped();
		if (equipped) {
			ItemEquipmentListener.onItemUnequipment(item, player);
		}
		item.setFusionedItem(null);
		ItemSocketService.removeAllFusionStone(player, item);
		item.setEnchantLevel(0);
		item.setPersistentState(PersistentState.UPDATE_REQUIRED);
		InventoryDAO.store(item, player);
		if (equipped) {
			ItemEquipmentListener.onItemEquipment(item, player);
			player.getGameStats().updateStatsAndSpeedVisually();
		}
		ItemPacketService.updateItemAfterInfoChange(player, item);
		ItemService.addItem(player, secondaryTemplate.getTemplateId(), 1);
		for (Integer stoneId : stoneIds) {
			ItemService.addItem(player, stoneId, 1);
		}
		return true;
	}
}

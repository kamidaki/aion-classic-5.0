package com.aionemu.gameserver.services;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.trade.RepurchaseList;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.restrictions.PlayerRestrictions;
import com.aionemu.gameserver.services.item.ItemService;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.audit.AuditLogger;

/**
 * @author Lost Academy Team & Durak
 */
public class RepurchaseService {

	private Map<Integer, Set<Item>> repurchaseItems = new ConcurrentHashMap<>();

	private RepurchaseService() {
	}

	/**
	 * Save items for repurchase for this player
	 */
	public void addRepurchaseItems(Player player, List<Item> items) {
		if (player == null || items == null || items.isEmpty())
			return;
		repurchaseItems.computeIfAbsent(player.getObjectId(), k -> ConcurrentHashMap.newKeySet()).addAll(items);
	}

	/**
	 * Delete all repurchase items for this player
	 */
	public void removeRepurchaseItems(Player player) {
		if (player != null)
			repurchaseItems.remove(player.getObjectId());
	}

	public Set<Item> getRepurchaseItems(int playerObjectId) {
		return repurchaseItems.getOrDefault(playerObjectId, Collections.emptySet());
	}

	public boolean canRepurchase(Player player, int itemObjectId) {
		if (player == null)
			return false;
		return getRepurchaseItems(player.getObjectId()).stream().anyMatch(item -> item.getObjectId() == itemObjectId);
	}

	public void repurchaseFromShop(Player player, RepurchaseList repurchaseList) {
		if (player == null || !PlayerRestrictions.canTrade(player) || repurchaseList == null) {
			return;
		}
		Set<Item> items = repurchaseItems.get(player.getObjectId());
		if (items == null || items.isEmpty()) {
			return;
		}
		synchronized (items) {
			for (int itemObjectId : repurchaseList.getRepurchaseItems()) {
				if (player.getInventory().isFull()) {
					PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_MSG_DICE_INVEN_ERROR());
					break;
				}

				Item repurchaseItem = items.stream().filter(item -> item.getObjectId() == itemObjectId).findAny().orElse(null);
				if (repurchaseItem != null) {
					if (player.getInventory().tryDecreaseKinah(repurchaseItem.getRepurchasePrice())) {
						ItemService.addItem(player, repurchaseItem);
						items.remove(repurchaseItem);
					} else {
						AuditLogger.log(player, "tried to repurchase item " + repurchaseItem.getItemId() + ", count: " + repurchaseItem.getItemCount()
								+ " without kinah");
					}
				}
			}
			if (items.isEmpty()) {
				repurchaseItems.remove(player.getObjectId());
			}
		}
	}

	public static RepurchaseService getInstance() {
		return SingletonHolder.INSTANCE;
	}

	private static class SingletonHolder {

		protected static final RepurchaseService INSTANCE = new RepurchaseService();
	}

}

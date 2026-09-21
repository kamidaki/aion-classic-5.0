package com.aionemu.gameserver.services.item;

import static com.aionemu.gameserver.services.item.ItemPacketService.*;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

import com.aionemu.gameserver.GameServer;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.Persistable.PersistentState;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.items.storage.IStorage;
import com.aionemu.gameserver.model.items.storage.StorageType;
import com.aionemu.gameserver.model.templates.item.Stigma;
import com.aionemu.gameserver.model.templates.item.Stigma.StigmaKind;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_UPDATE_PLAYER_APPEARANCE;
import com.aionemu.gameserver.services.LegionService;
import com.aionemu.gameserver.services.StigmaService;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * @author Lost Academy Team & Durak
 */
public class ItemMoveService {

	private static final Logger log = LoggerFactory.getLogger(ItemMoveService.class);

	public static void moveItem(Player player, int itemObjId, byte sourceStorageType, byte destinationStorageType, short slot) {
		if (player.isTrading() || GameServer.isShuttingDownSoon()) {
			if (GameServer.isShuttingDownSoon())
				PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_MSG_DISABLE("Shutdown Progress"));
			return;
		}

		// Classic 5.0 Stigma window move: Cube (0) -> Stigma (58)
		if (destinationStorageType == StorageType.STIGMA.getId()) {
			Item item = player.getInventory().getItemByObjId(itemObjId);
			if (item == null)
				return;
			if (!item.getItemTemplate().isStigma()) {
				log.warn(player + " tried to move non-stigma item " + itemObjId + " to STIGMA storage");
				sendItemUnlockPacket(player, item);
				return;
			}
			long slotMask = getStigmaSlotMask(player, item, slot);
			if (slotMask == 0) {
				log.warn(player + " no available or valid stigma slot for item " + itemObjId + " (requested slot: " + slot + ")");
				sendItemUnlockPacket(player, item);
				return;
			}
			Item equipped = player.getEquipment().equipItem(itemObjId, slotMask);
			if (equipped == null) {
				sendItemUnlockPacket(player, item);
			} else {
				PacketSendUtility.broadcastPacket(player,
					new SM_UPDATE_PLAYER_APPEARANCE(player.getObjectId(), player.getEquipment().getEquippedForAppearance()), true);
			}
			return;
		}

		// Classic 5.0 Stigma window move: Stigma (58) -> Cube (0) or between Stigma slots
		if (sourceStorageType == StorageType.STIGMA.getId()) {
			Item item = player.getEquipment().getEquippedItemByObjId(itemObjId);
			if (item == null)
				return;
			if (destinationStorageType == StorageType.CUBE.getId()) {
				if (!StigmaService.checkUnequip(player, item))
					return;
				Item resultItem = player.getEquipment().unEquipItem(itemObjId, item.getEquipmentSlot(), (byte) 0);
				if (resultItem == null && player.getInventory().isFull()) {
					PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_UI_INVENTORY_FULL());
					return;
				}
				PacketSendUtility.broadcastPacket(player,
					new SM_UPDATE_PLAYER_APPEARANCE(player.getObjectId(), player.getEquipment().getEquippedForAppearance()), true);
			} else if (destinationStorageType == StorageType.STIGMA.getId()) {
				long targetMask = getStigmaSlotMask(player, item, slot);
				if (targetMask != 0 && targetMask != item.getEquipmentSlot()) {
					if (!StigmaService.checkUnequip(player, item))
						return;
					player.getEquipment().unEquipItem(itemObjId, item.getEquipmentSlot(), (byte) 0);
					Item reequipped = player.getEquipment().equipItem(itemObjId, targetMask);
					if (reequipped != null) {
						PacketSendUtility.broadcastPacket(player,
							new SM_UPDATE_PLAYER_APPEARANCE(player.getObjectId(), player.getEquipment().getEquippedForAppearance()), true);
					}
				}
			}
			return;
		}
		IStorage sourceStorage = player.getStorage(sourceStorageType);
		if (sourceStorage == null) {
			log.error(player + " tried to move itemObjId " + itemObjId + " from unknown sourceStorageType: " + sourceStorageType);
			return;
		}
		Item item = sourceStorage.getItemByObjId(itemObjId);
		if (item == null)
			return;

		IStorage targetStorage = player.getStorage(destinationStorageType);
		if (targetStorage == null) {
			log.error(player + " tried to move itemObjId " + itemObjId + " to unknown destinationStorageType: " + destinationStorageType);
			return;
		}

		if (sourceStorageType == destinationStorageType) {
			if (item.getEquipmentSlot() != slot)
				moveInSameStorage(sourceStorage, item, slot);
			return;
		}
		if (ItemRestrictionService.isItemRestrictedTo(player, item, targetStorage.getStorageType())
			|| ItemRestrictionService.isItemRestrictedFrom(player, item, sourceStorage.getStorageType())
			|| player.isTrading()
			|| GameServer.isShuttingDownSoon()) {
			sendItemUnlockPacket(player, item);
			if (GameServer.isShuttingDownSoon())
				PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_MSG_DISABLE("Shutdown Progress"));
			return;
		}

		if (sourceStorageType == StorageType.LEGION_WAREHOUSE.getId() || destinationStorageType == StorageType.LEGION_WAREHOUSE.getId()) {
			if (player.getLegion() == null || player.getLegion().getLegionWarehouse().getCurrentUser() != player.getObjectId()) {
				sendItemUnlockPacket(player, item);
				return;
			}
			LegionService.getInstance().addWHItemHistory(player, item.getItemId(), item.getItemCount(), sourceStorage, targetStorage);
		}
		if (slot == -1) {
			if (item.getItemTemplate().isStackable()) {
				for (Item targetStack : targetStorage.getItemsByItemId(item.getItemId())) {
					ItemSplitService.mergeStacks(sourceStorage, targetStorage, item, targetStack, item.getItemCount());
					if (item.getItemCount() == 0) {
						return;
					}
				}
			}
		}
		if (targetStorage.isFull()) {
			PacketSendUtility.sendPacket(player, targetStorage.getStorageIsFullMessage());
			sendItemUnlockPacket(player, item);
			return;
		}
		sourceStorage.remove(item);
		sendItemDeletePacket(player, sourceStorage.getStorageType(), item, ItemDeleteType.MOVE);
		item.setEquipmentSlot(slot);
		targetStorage.add(item);
	}

	private static void moveInSameStorage(IStorage storage, Item item, short slot) {
		if (item.getItemTemplate().isStackable()) {
			Item targetItem = null;
			for (Item it : storage.getItems()) {
				if (it.getEquipmentSlot() == slot) {
					targetItem = it;
					break;
				}
			}
			if (targetItem != null && targetItem.getItemId() == item.getItemId()) {
				ItemSplitService.mergeStacks(storage, storage, item, targetItem, item.getItemCount());
				return;
			}
		}
		storage.setPersistentState(PersistentState.UPDATE_REQUIRED);
		item.setEquipmentSlot(slot);
		item.setPersistentState(PersistentState.UPDATE_REQUIRED);
	}

	public static void switchItemsInStorages(Player player, byte sourceStorageType, int sourceItemObjId, byte replaceStorageType, int replaceItemObjId) {
		IStorage sourceStorage = player.getStorage(sourceStorageType);
		IStorage replaceStorage = player.getStorage(replaceStorageType);

		Item sourceItem = sourceStorage.getItemByObjId(sourceItemObjId);
		if (sourceItem == null)
			return;

		Item replaceItem = replaceStorage.getItemByObjId(replaceItemObjId);
		if (replaceItem == null)
			return;

		// restrictions checks
		if (ItemRestrictionService.isItemRestrictedFrom(player, sourceItem, sourceStorage.getStorageType())
			|| ItemRestrictionService.isItemRestrictedFrom(player, replaceItem, replaceStorage.getStorageType())
			|| ItemRestrictionService.isItemRestrictedTo(player, sourceItem, replaceStorage.getStorageType())
			|| ItemRestrictionService.isItemRestrictedTo(player, replaceItem, sourceStorage.getStorageType())
			|| player.isTrading() 
			|| GameServer.isShuttingDownSoon()) {
			sendItemUnlockPacket(player, sourceItem);
			sendItemUnlockPacket(player, replaceItem);
			if (GameServer.isShuttingDownSoon())
				PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_MSG_DISABLE("Shutdown Progress"));
			return;
		}

		if (sourceStorageType == StorageType.LEGION_WAREHOUSE.getId() || replaceStorageType == StorageType.LEGION_WAREHOUSE.getId()) {
			if (player.getLegion() == null || player.getLegion().getLegionWarehouse().getCurrentUser() != player.getObjectId()) {
				sendItemUnlockPacket(player, sourceItem);
				sendItemUnlockPacket(player, replaceItem);
				return;
			}
		}

		if (sourceItem.getItemId() == replaceItem.getItemId() && sourceItem.getItemTemplate().isStackable()) {
			ItemSplitService.mergeStacks(sourceStorage, replaceStorage, sourceItem, replaceItem, sourceItem.getItemCount());
			return;
		}

		long sourceSlot = sourceItem.getEquipmentSlot();
		long replaceSlot = replaceItem.getEquipmentSlot();

		sourceItem.setEquipmentSlot(replaceSlot);
		replaceItem.setEquipmentSlot(sourceSlot);

		sourceStorage.remove(sourceItem);
		replaceStorage.remove(replaceItem);

		// correct UI update order is 1)delete items 2) add items
		sendItemDeletePacket(player, sourceStorage.getStorageType(), sourceItem, ItemDeleteType.MOVE);
		sendItemDeletePacket(player, replaceStorage.getStorageType(), replaceItem, ItemDeleteType.MOVE);
		sourceStorage.add(replaceItem);
		replaceStorage.add(sourceItem);
	}

	private static long getStigmaSlotMask(Player player, Item item, short slot) {
		Stigma stigma = item.getItemTemplate().getStigma();
		boolean isGreater = stigma != null && stigma.getKind() == StigmaKind.GREATER;

		if (slot >= 0 && slot <= 12) {
			long requestedMask = StigmaService.getStigmaSlotMask(slot);
			if (requestedMask != 0 && player.getEquipment().getEquippedItemBySlot(requestedMask) == null) {
				return requestedMask;
			}
		}

		return StigmaService.findFreeStigmaSlot(player, isGreater);
	}
}

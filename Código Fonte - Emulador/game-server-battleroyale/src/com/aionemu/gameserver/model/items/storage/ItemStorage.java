package com.aionemu.gameserver.model.items.storage;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

import com.aionemu.gameserver.model.gameobjects.Item;

/**
 * @author Lost Academy Team & Durak
 */
public class ItemStorage {

	public static final long FIRST_AVAILABLE_SLOT = 65535L;

	private final Map<Integer, Item> items = new ConcurrentHashMap<>();
	private final StorageType storageType;
	private int limit;

	public ItemStorage(StorageType storageType) {
		this.storageType = storageType;
		this.limit = storageType.getLimit();
	}

	public List<Item> getItems() {
		return new ArrayList<>(items.values());
	}

	public int getLimit() {
		return limit;
	}

	public void setLimit(int limit) {
		this.limit = limit;
	}

	public int getRowLength() {
		return storageType.getLength();
	}

	public Item getFirstItemById(int itemId) {
		for (Item item : items.values()) {
			if (item.getItemTemplate().getTemplateId() == itemId) {
				return item;
			}
		}
		return null;
	}

	public List<Item> getItemsById(int itemId) {
		List<Item> temp = new ArrayList<>();
		for (Item item : items.values()) {
			if (item.getItemTemplate().getTemplateId() == itemId) {
				temp.add(item);
			}
		}
		return temp;
	}

	public Item getItemByObjId(int itemObjId) {
		return items.get(itemObjId);
	}

	public long getSlotIdByItemId(int itemId) {
		for (Item item : items.values()) {
			if (item.getItemTemplate().getTemplateId() == itemId) {
				return item.getEquipmentSlot();
			}
		}
		return -1;
	}

	public Item getItemBySlotId(short slotId) {
		for (Item item : getCubeItems()) {
			if (item.getEquipmentSlot() == slotId) {
				return item;
			}
		}
		return null;
	}

	public Item getSpecialItemBySlotId(short slotId) {
		for (Item item : getSpecialCubeItems()) {
			if (item.getEquipmentSlot() == slotId) {
				return item;
			}
		}
		return null;
	}

	public long getSlotIdByObjId(int objId) {
		Item item = getItemByObjId(objId);
		if (item != null)
			return item.getEquipmentSlot();
		else
			return -1;
	}

	public long getNextFreeSlot() {
		java.util.Set<Long> usedSlots = new java.util.HashSet<>();
		for (Item it : items.values()) {
			long s = it.getEquipmentSlot();
			if (s >= 0 && s < FIRST_AVAILABLE_SLOT) {
				usedSlots.add(s);
			}
		}
		for (long i = 0; i < limit; i++) {
			if (!usedSlots.contains(i)) {
				return i;
			}
		}
		return 0;
	}

	public boolean putItem(Item item) {
		boolean slotOccupied = items.values().stream().anyMatch(i -> i.getEquipmentSlot() == item.getEquipmentSlot() && i.getObjectId() != item.getObjectId());
		if (item.getEquipmentSlot() == FIRST_AVAILABLE_SLOT || item.getEquipmentSlot() < 0 || item.getEquipmentSlot() >= FIRST_AVAILABLE_SLOT || slotOccupied) {
			item.setEquipmentSlot(getNextFreeSlot());
		}
		return items.putIfAbsent(item.getObjectId(), item) == null;
	}

	public Item removeItem(int objId) {
		return items.remove(objId);
	}

	public boolean isFull() {
		return getCubeItems().size() >= limit;
	}

	public boolean isFullSpecialCube() {
		return getSpecialCubeItems().size() >= storageType.getSpecialLimit();
	}

	public List<Item> getSpecialCubeItems() {
		return items.values().stream().filter(i -> i.getItemTemplate().getExtraInventoryId() > 0).collect(Collectors.toList());
	}

	public List<Item> getCubeItems() {
		return items.values().stream().filter(i -> i.getItemTemplate().getExtraInventoryId() < 1).collect(Collectors.toList());
	}

	public int getFreeSlots() {
		return limit - getCubeItems().size();
	}

	public int getSpecialCubeFreeSlots() {
		return storageType.getSpecialLimit() - getSpecialCubeItems().size();
	}

	public int size() {
		return items.size();
	}

}

package com.aionemu.gameserver.model.gameobjects.player;

import static com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE.*;

import java.util.*;
import java.util.stream.Collectors;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.controllers.observer.ItemUseObserver;
import com.aionemu.gameserver.dao.InventoryDAO;
import com.aionemu.gameserver.dao.ItemStoneListDAO;
import com.aionemu.gameserver.model.ActionState;
import com.aionemu.gameserver.model.EmotionType;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.TaskId;
import com.aionemu.gameserver.model.actions.PlayerMode;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.Persistable;
import com.aionemu.gameserver.model.gameobjects.Summon;
import com.aionemu.gameserver.model.gameobjects.state.CreatureState;
import com.aionemu.gameserver.model.items.ItemSlot;
import com.aionemu.gameserver.model.items.ItemStone;
import com.aionemu.gameserver.model.items.ManaStone;
import com.aionemu.gameserver.model.items.storage.StorageType;
import com.aionemu.gameserver.model.stats.listeners.ItemEquipmentListener;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.model.templates.item.ItemUseLimits;
import com.aionemu.gameserver.model.templates.item.enums.ItemGroup;
import com.aionemu.gameserver.model.templates.item.enums.ItemSubType;
import com.aionemu.gameserver.model.templates.itemset.ItemSetTemplate;
import com.aionemu.gameserver.network.aion.serverpackets.*;
import com.aionemu.gameserver.questEngine.QuestEngine;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.services.ArmsfusionService;
import com.aionemu.gameserver.services.StigmaService;
import com.aionemu.gameserver.services.item.ItemFactory;
import com.aionemu.gameserver.services.item.ItemPacketService;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemAddType;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemDeleteType;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemUpdateType;
import com.aionemu.gameserver.services.item.ItemSocketService;
import com.aionemu.gameserver.skillengine.effect.WeaponDualEffect;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.ThreadPoolManager;
import com.aionemu.gameserver.utils.audit.AuditLogger;
import com.aionemu.gameserver.utils.stats.AbyssRankEnum;

/**
 * @author Lost Academy Team & Durak
 */
public class Equipment implements Persistable {

	private static final Logger log = LoggerFactory.getLogger(Equipment.class);

	private final SortedMap<Long, Item> equipment = Collections.synchronizedSortedMap(new TreeMap<>());
	private final Player owner;
	private PersistentState persistentState = PersistentState.UPDATED;

	public Equipment(Player player) {
		this.owner = player;
	}

	/**
	 * @return item or null in case of failure
	 */
	public Item equipItem(int itemUniqueId, long slot) {
		return equipItem(itemUniqueId, slot, (byte) 0);
	}

	public Item equipItem(int itemUniqueId, long slot, byte subSlot) {
		Item item = owner.getInventory().getItemByObjId(itemUniqueId);
		if (item == null || item.isEquipped())
			return null;

		if (item.getTuneCount() < 0) {
			item.setTuneCount(0);
		}

		ItemTemplate itemTemplate = item.getItemTemplate();

		// Default slot if none specified
		if (slot == 0) {
			if (itemTemplate.isStigma()) {
				slot = StigmaService.findFreeStigmaSlot(owner, itemTemplate.isGreaterStigma());
				if (slot == 0) {
					PacketSendUtility.sendPacket(owner, STR_STIGMA_SLOT_IS_NOT_OPENED());
					return null;
				}
			} else {
				slot = itemTemplate.getItemSlot();
			}
		} else if (itemTemplate.isStigma() && Long.bitCount(slot) > 1) {
			slot = StigmaService.findFreeStigmaSlot(owner, itemTemplate.isGreaterStigma());
			if (slot == 0) {
				PacketSendUtility.sendPacket(owner, STR_STIGMA_SLOT_IS_NOT_OPENED());
				return null;
			}
		}

		// Resolve combo slot masks to specific single slots:
		if (itemTemplate.getItemGroup() == ItemGroup.POWER_SHARDS) {
			if (slot == ItemSlot.POWER_SHARD_LEFT.getSlotIdMask()) {
				slot = ItemSlot.POWER_SHARD_LEFT.getSlotIdMask();
			} else if (slot == ItemSlot.POWER_SHARD_RIGHT.getSlotIdMask()) {
				slot = ItemSlot.POWER_SHARD_RIGHT.getSlotIdMask();
			} else if (subSlot == 1) {
				slot = ItemSlot.POWER_SHARD_LEFT.getSlotIdMask();
			} else if (getMainHandPowerShard() == null) {
				slot = ItemSlot.POWER_SHARD_RIGHT.getSlotIdMask();
			} else if (getOffHandPowerShard() == null) {
				slot = ItemSlot.POWER_SHARD_LEFT.getSlotIdMask();
			} else {
				slot = ItemSlot.POWER_SHARD_RIGHT.getSlotIdMask();
			}
		} else if ((slot & ItemSlot.RING_RIGHT_OR_LEFT.getSlotIdMask()) != 0) {
			boolean hasLeftRing = equipment.get(ItemSlot.RING_LEFT.getSlotIdMask()) != null;
			boolean hasRightRing = equipment.get(ItemSlot.RING_RIGHT.getSlotIdMask()) != null;
			if (slot == ItemSlot.RING_RIGHT.getSlotIdMask() || subSlot == 1) {
				slot = ItemSlot.RING_RIGHT.getSlotIdMask();
			} else if (!hasLeftRing) {
				slot = ItemSlot.RING_LEFT.getSlotIdMask();
			} else if (!hasRightRing) {
				slot = ItemSlot.RING_RIGHT.getSlotIdMask();
			} else {
				slot = ItemSlot.RING_LEFT.getSlotIdMask();
			}
		} else if ((slot & ItemSlot.EARRING_RIGHT_OR_LEFT.getSlotIdMask()) != 0) {
			boolean hasLeftEar = equipment.get(ItemSlot.EARRINGS_LEFT.getSlotIdMask()) != null;
			boolean hasRightEar = equipment.get(ItemSlot.EARRINGS_RIGHT.getSlotIdMask()) != null;
			if (slot == ItemSlot.EARRINGS_RIGHT.getSlotIdMask() || subSlot == 1) {
				slot = ItemSlot.EARRINGS_RIGHT.getSlotIdMask();
			} else if (!hasLeftEar) {
				slot = ItemSlot.EARRINGS_LEFT.getSlotIdMask();
			} else if (!hasRightEar) {
				slot = ItemSlot.EARRINGS_RIGHT.getSlotIdMask();
			} else {
				slot = ItemSlot.EARRINGS_LEFT.getSlotIdMask();
			}
		} else if (itemTemplate.getItemGroup() == ItemGroup.ARCAMANT) {
			slot = ItemSlot.ARCAMANT.getSlotIdMask();
		} else if (itemTemplate.getItemGroup() == ItemGroup.SHIELD) {
			slot = ItemSlot.SUB_HAND.getSlotIdMask();
		} else if (itemTemplate.isWeapon()) {
			boolean isDualWielder = WeaponDualEffect.hasDualWieldEffect(owner);
			boolean is2H = itemTemplate.isTwoHandWeapon();
			boolean isSubHandTarget = (subSlot == 1 || slot == ItemSlot.SUB_HAND.getSlotIdMask());

			// Classic 5.0 Auto-Fusion: Only two-handed weapons can be fused!
			if (isSubHandTarget && is2H) {
				Item mainWeapon = equipment.get(ItemSlot.MAIN_HAND.getSlotIdMask());
				if (mainWeapon == null) {
					mainWeapon = equipment.get(ItemSlot.MAIN_OFF_HAND.getSlotIdMask());
				}
				if (mainWeapon != null && mainWeapon.getItemTemplate().isTwoHandWeapon()) {
					return autoFuseWeapon(item);
				}
			}

			if (is2H) {
				slot = ItemSlot.MAIN_OR_SUB.getSlotIdMask();
			} else if (itemTemplate.isOneHandWeapon()) {
				if (!isDualWielder) {
					slot = ItemSlot.MAIN_HAND.getSlotIdMask();
				} else {
					if (isSubHandTarget) {
						slot = ItemSlot.SUB_HAND.getSlotIdMask();
					} else if (slot == ItemSlot.MAIN_OR_SUB.getSlotIdMask() || slot == 0) {
						if (equipment.get(ItemSlot.MAIN_HAND.getSlotIdMask()) == null) {
							slot = ItemSlot.MAIN_HAND.getSlotIdMask();
						} else if (equipment.get(ItemSlot.SUB_HAND.getSlotIdMask()) == null) {
							slot = ItemSlot.SUB_HAND.getSlotIdMask();
						} else {
							slot = ItemSlot.MAIN_HAND.getSlotIdMask();
						}
					}
				}
			}
		}

		if (!itemTemplate.isClassSpecific(owner.getPlayerClass())) {
			PacketSendUtility.sendPacket(owner, STR_CANNOT_USE_ITEM_INVALID_CLASS());
			return null;
		}
		// don't allow to wear items of not allowed level
		int requiredLevel = itemTemplate.getRequiredLevel(owner.getPlayerClass());
		if (requiredLevel == -1 || requiredLevel > owner.getLevel()) {
			PacketSendUtility.sendPacket(owner, STR_CANNOT_USE_ITEM_TOO_LOW_LEVEL_MUST_BE_THIS_LEVEL(item.getL10n(), requiredLevel));
			return null;
		}

		byte levelRestrict = itemTemplate.getMaxLevelRestrict(owner.getPlayerClass());
		if (levelRestrict != 0 && owner.getLevel() > levelRestrict) {
			PacketSendUtility.sendPacket(owner, STR_CANNOT_USE_ITEM_TOO_HIGH_LEVEL(levelRestrict, itemTemplate.getL10n()));
			return null;
		}

		if (itemTemplate.getRace() != Race.PC_ALL && itemTemplate.getRace() != owner.getRace()) {
			PacketSendUtility.sendPacket(owner, STR_CANNOT_USE_ITEM_INVALID_RACE());
			return null;
		}

		ItemUseLimits limits = itemTemplate.getUseLimits();
		if (limits.getGenderPermitted() != null && limits.getGenderPermitted() != owner.getGender()) {
			PacketSendUtility.sendPacket(owner, STR_CANNOT_USE_ITEM_INVALID_GENDER());
			return null;
		}

		if (!verifyRankLimits(item)) {
			PacketSendUtility.sendPacket(owner, STR_CANNOT_USE_ITEM_INVALID_RANK(AbyssRankEnum.getRankL10n(owner.getRace(), limits.getMinRank())));
			return null;
		}

		if (!checkInventorySlots(slot)) {
			PacketSendUtility.sendPacket(owner, STR_UI_INVENTORY_FULL());
			return null;
		}

		if (!checkAvailableEquipSkills(item))
			return null;

		ItemSlot[] targetSlots = ItemSlot.getSlotsFor(slot);
		if (targetSlots.length == 0) {
			log.warn("Unknown target slot " + slot + " for " + item);
			return null;
		}

		if (targetSlots.length == 2 && !itemTemplate.isTwoHandWeapon() || targetSlots.length > 2) {
			AuditLogger.log(owner, "tried to equip " + item + " in slots: " + Arrays.toString(targetSlots));
			return null;
		}

		if ((ItemSlot.MAIN_OFF_OR_SUB_OFF.getSlotIdMask() & slot) != 0) { // offhand slots cannot be directly populated on client side
			AuditLogger.log(owner, "tried to equip " + item + " directly in offhand slot");
			return null;
		}

		long validSlotMask = itemTemplate.getItemSlot();
		if (validSlotMask == 0) // e.g. arrows, which cannot be equipped anymore
			return null;
		if ((validSlotMask & slot) != slot) { // invalid slot provided for the item
			AuditLogger.log(owner, "tried to equip " + item + " in invalid slot(s): " + Arrays.toString(targetSlots));
			return null;
		}

		if (!StigmaService.checkEquip(owner, item, slot))
			return null;

		if (itemTemplate.isSoulBound() && !item.isSoulBound()) {
			soulBindItem(owner, item, slot);
			return null;
		}
		return equip(slot, item);
	}

	private boolean checkInventorySlots(long itemSlotToEquip) {
		if (owner.getInventory().isFull() && ItemSlot.isTwoHandedWeapon(itemSlotToEquip)) { // weapon slot(s)
			for (ItemSlot slot : ItemSlot.getSlotsFor(itemSlotToEquip)) {
				Item equippedWeaponOrShield = equipment.get(slot.getSlotIdMask());
				if (equippedWeaponOrShield == null || equippedWeaponOrShield.getItemTemplate().isTwoHandWeapon())
					return true;
			}
			return false; // two weapons would need to be unequipped, but there is no free slot
		}
		return true;
	}

	private boolean checkDualWieldRestriction(Item item, long slot) {
		if (item.getItemTemplate().isOneHandWeapon() && (slot & ItemSlot.LEFT_HAND.getSlotIdMask()) == slot && !WeaponDualEffect.hasDualWieldEffect(owner))
			return false;
		return true;
	}

	private Item equip(long itemSlotToEquip, Item item) {
		if (item.getTuneCount() < 0) {
			item.setTuneCount(0);
		}

		ItemSlot[] targetSlots = ItemSlot.getSlotsFor(itemSlotToEquip);

		synchronized (this) {
			// do unequip of necessary items
			unEquip(getUnequipSlots(itemSlotToEquip));
			owner.getInventory().remove(item);
			// equip target item
			for (ItemSlot slot : targetSlots)
				equipment.put(slot.getSlotIdMask(), item);
			item.setEquipped(true);
			item.setEquipmentSlot(itemSlotToEquip);
			ItemPacketService.updateItemAfterEquip(owner, item);
			if (item.getItemTemplate().isStigma()) {
				// Classic 5.0: ao equipar estigma, remove visualmente do Cubo e adiciona na janela de Estigmas (Storage 58)
				PacketSendUtility.sendPacket(owner, new SM_DELETE_ITEM(item.getObjectId(), ItemDeleteType.MOVE));
				PacketSendUtility.sendPacket(owner, new SM_WAREHOUSE_ADD_ITEM(item, StorageType.STIGMA.getId(), owner, ItemAddType.ALL_SLOT));
				PacketSendUtility.sendPacket(owner, SM_CUBE_UPDATE.cubeSize(StorageType.CUBE, owner));
				StigmaService.onEquip(owner, item);
			}

			// update stats
			notifyItemEquipped(item);
			owner.getLifeStats().updateCurrentStats();
			owner.getGameStats().updateStatsAndSpeedVisually();
			setPersistentState(PersistentState.UPDATE_REQUIRED);
			QuestEngine.getInstance().onEquipItem(new QuestEnv(null, owner, 0), item.getItemId());

			return item;
		}
	}

	private long getUnequipSlots(long itemSlotToEquip) {
		if (itemSlotToEquip == ItemSlot.MAIN_HAND.getSlotIdMask() || itemSlotToEquip == ItemSlot.SUB_HAND.getSlotIdMask()) {
			Item equippedItem = equipment.get(itemSlotToEquip);
			if (equippedItem != null && equippedItem.getItemTemplate().isTwoHandWeapon()) {
				return ItemSlot.MAIN_OR_SUB.getSlotIdMask(); // two-handed occupies two slots, so we need to unequip both
			}
			Item mainHand = equipment.get(ItemSlot.MAIN_HAND.getSlotIdMask());
			if (mainHand != null && mainHand.getItemTemplate().isTwoHandWeapon()) {
				return ItemSlot.MAIN_OR_SUB.getSlotIdMask();
			}
		} else if (itemSlotToEquip == ItemSlot.MAIN_OFF_HAND.getSlotIdMask() || itemSlotToEquip == ItemSlot.SUB_OFF_HAND.getSlotIdMask()) {
			Item equippedItem = equipment.get(itemSlotToEquip);
			if (equippedItem != null && equippedItem.getItemTemplate().isTwoHandWeapon()) {
				return ItemSlot.MAIN_OFF_OR_SUB_OFF.getSlotIdMask();
			}
			Item mainOff = equipment.get(ItemSlot.MAIN_OFF_HAND.getSlotIdMask());
			if (mainOff != null && mainOff.getItemTemplate().isTwoHandWeapon()) {
				return ItemSlot.MAIN_OFF_OR_SUB_OFF.getSlotIdMask();
			}
		}
		return itemSlotToEquip;
	}

	public void notifyItemEquipped(Item item) {
		ItemEquipmentListener.onItemEquipment(item, owner);
		owner.getObserveController().notifyItemEquip(item, owner);
		tryUpdateSummonStats();
	}

	public void notifyItemUnequip(Item item) {
		ItemEquipmentListener.onItemUnequipment(item, owner);
		owner.getObserveController().notifyItemUnEquip(item, owner);
		tryUpdateSummonStats();
	}

	private void tryUpdateSummonStats() {
		Summon summon = owner.getSummon();
		if (summon != null) {
			summon.getGameStats().updateStatsAndSpeedVisually();
		}
	}

	/**
	 * Called when CM_EQUIP_ITEM packet arrives with action 1
	 * 
	 * @return item or null in case of failure
	 */
	public Item unEquipItem(int itemObjId, byte subSlot) {
		return unEquipItem(itemObjId, 0, true, subSlot);
	}

	public Item unEquipItem(int itemObjId) {
		return unEquipItem(itemObjId, 0, true, (byte) 0);
	}

	public Item unEquipItem(int itemObjId, boolean checkFullInventory) {
		return unEquipItem(itemObjId, 0, checkFullInventory, (byte) 0);
	}

	public Item unEquipItem(int itemObjId, boolean checkFullInventory, byte subSlot) {
		return unEquipItem(itemObjId, 0, checkFullInventory, subSlot);
	}

	public Item unEquipItem(int itemObjId, long slot, byte subSlot) {
		return unEquipItem(itemObjId, slot, true, subSlot);
	}

	public Item unEquipItem(int itemObjId, long slot, boolean checkFullInventory, byte subSlot) {
		// if inventory is full unequip action is disabled
		if (checkFullInventory && owner.getInventory().isFull())
			return null;

		synchronized (this) {
			// Classic 5.0 Un-fuse:
			if (subSlot == 1) {
				Item mainWeapon = equipment.get(ItemSlot.MAIN_HAND.getSlotIdMask());
				if (mainWeapon == null) {
					mainWeapon = equipment.get(ItemSlot.MAIN_OFF_HAND.getSlotIdMask());
				}
				if (mainWeapon != null && mainWeapon.hasFusionedItem() && (itemObjId == 0 || mainWeapon.getObjectId() == itemObjId
					|| (mainWeapon.getFusionedItem() != null && mainWeapon.getFusionedItem().getObjectId() == itemObjId))) {
					return autoUnfuseWeapon(mainWeapon);
				}
			}

			Item itemToUnequip = getEquippedItemByObjId(itemObjId);
			if (itemToUnequip == null && slot > 0) {
				itemToUnequip = equipment.get(slot);
			}
			if (itemToUnequip == null || !itemToUnequip.isEquipped())
				return null;

			// Classic 5.0: If main-hand weapon has a fused secondary weapon, un-fuse first so secondary weapon is restored to inventory!
			if (itemToUnequip.hasFusionedItem()) {
				if (owner.getInventory().getFreeSlots() < 2) {
					PacketSendUtility.sendPacket(owner, STR_UI_INVENTORY_FULL());
					return null;
				}
				autoUnfuseWeapon(itemToUnequip);
			}

			// Looks very odd - but its retail like: unequip off-hand weapon or shield when main hand is unequipped
			if (itemToUnequip.getEquipmentSlot() == ItemSlot.MAIN_HAND.getSlotIdMask()) {
				Item ohWeapon = equipment.get(ItemSlot.SUB_HAND.getSlotIdMask());
				if (ohWeapon != null && (ohWeapon.getItemTemplate().isWeapon() || ohWeapon.getItemTemplate().getItemGroup() == ItemGroup.SHIELD)) {
					if (owner.getInventory().getFreeSlots() < 2) {
						return null;
					}
					unEquip(ItemSlot.SUB_HAND.getSlotIdMask());
				}
			} else if (itemToUnequip.getEquipmentSlot() == ItemSlot.MAIN_OFF_HAND.getSlotIdMask()) {
				Item ohWeapon = equipment.get(ItemSlot.SUB_OFF_HAND.getSlotIdMask());
				if (ohWeapon != null && (ohWeapon.getItemTemplate().isWeapon() || ohWeapon.getItemTemplate().getItemGroup() == ItemGroup.SHIELD)) {
					if (owner.getInventory().getFreeSlots() < 2) {
						return null;
					}
					unEquip(ItemSlot.SUB_OFF_HAND.getSlotIdMask());
				}
			}

			// if unequip power shard
			if (itemToUnequip.getItemTemplate().getItemGroup() == ItemGroup.POWER_SHARDS) {
				owner.unsetState(CreatureState.POWERSHARD);
				PacketSendUtility.sendPacket(owner, new SM_EMOTION(owner, EmotionType.POWERSHARD_OFF, 0, 0));
			}

			unEquip(itemToUnequip.getEquipmentSlot());

			if (itemToUnequip.getItemTemplate().isStigma()) { // official order: S 0x1D with the empty slot, then the skill messages and removals
				PacketSendUtility.sendPacket(owner, new SM_DELETE_WAREHOUSE_ITEM(StorageType.STIGMA.getId(), itemToUnequip.getObjectId(), ItemDeleteType.MOVE));
				PacketSendUtility.sendPacket(owner, new SM_INVENTORY_ADD_ITEM(itemToUnequip, owner, ItemAddType.ALL_SLOT));
				PacketSendUtility.sendPacket(owner, new SM_INVENTORY_UPDATE_ITEM(owner, itemToUnequip, ItemUpdateType.EQUIP_UNEQUIP));
				PacketSendUtility.sendPacket(owner, SM_CUBE_UPDATE.cubeSize(StorageType.CUBE, owner));
				StigmaService.removeStigmaSkills(owner, itemToUnequip, true);
			}

			return itemToUnequip;
		}
	}

	private Item autoFuseWeapon(Item fuseWeapon) {
		Item mainWeapon = equipment.get(ItemSlot.MAIN_HAND.getSlotIdMask());
		if (mainWeapon == null) {
			mainWeapon = equipment.get(ItemSlot.MAIN_OFF_HAND.getSlotIdMask());
		}
		if (mainWeapon == null) {
			PacketSendUtility.sendPacket(owner, STR_COMPOUND_ITEM_NO_TARGET_ITEM());
			return null;
		}

		if (!mainWeapon.getItemTemplate().isCanFuse() || !fuseWeapon.getItemTemplate().isCanFuse()) {
			Item nonFusible = !mainWeapon.getItemTemplate().isCanFuse() ? mainWeapon : fuseWeapon;
			PacketSendUtility.sendPacket(owner, STR_COMPOUND_ERROR_NOT_AVAILABLE(nonFusible.getL10n()));
			return null;
		}

		if (mainWeapon.hasFusionedItem()) {
			PacketSendUtility.sendPacket(owner, STR_COMPOUND_ERROR_NOT_AVAILABLE(mainWeapon.getL10n()));
			return null;
		}

		if (mainWeapon.getItemTemplate().getItemGroup() != fuseWeapon.getItemTemplate().getItemGroup()) {
			PacketSendUtility.sendPacket(owner, STR_COMPOUND_ERROR_DIFFERENT_TYPE());
			return null;
		}

		if (fuseWeapon.getItemTemplate().getLevel() > mainWeapon.getItemTemplate().getLevel()) {
			PacketSendUtility.sendPacket(owner, STR_COMPOUND_ERROR_MAIN_REQUIRE_HIGHER_LEVEL());
			return null;
		}

		// Perform fusion directly without NPC and without Kinah
		owner.getInventory().remove(fuseWeapon);
		fuseWeapon.setPersistentState(PersistentState.DELETED);
		InventoryDAO.store(fuseWeapon, owner);
		ItemPacketService.sendItemDeletePacket(owner, StorageType.CUBE, fuseWeapon, ItemDeleteType.MOVE);

		mainWeapon.setFusionedItem(fuseWeapon);
		ItemSocketService.copyFusionStones(fuseWeapon, mainWeapon);
		mainWeapon.setPersistentState(PersistentState.UPDATE_REQUIRED);
		InventoryDAO.store(mainWeapon, owner);
		if (mainWeapon.hasFusionStones()) {
			ItemStoneListDAO.save(Collections.singletonList(mainWeapon));
		}

		notifyItemUnequip(mainWeapon);
		notifyItemEquipped(mainWeapon);
		owner.getLifeStats().updateCurrentStats();
		owner.getGameStats().updateStatsAndSpeedVisually();

		PacketSendUtility.sendPacket(owner, new SM_INVENTORY_UPDATE_ITEM(owner, mainWeapon, ItemUpdateType.EQUIP_UNEQUIP));
		ItemPacketService.updateItemAfterInfoChange(owner, mainWeapon);
		PacketSendUtility.sendPacket(owner, new SM_INVENTORY_UPDATE_ITEM(owner, mainWeapon, ItemUpdateType.EQUIP_UNEQUIP));
		PacketSendUtility.sendPacket(owner, STR_COMPOUND_SUCCESS(mainWeapon.getL10n(), fuseWeapon.getL10n()));
		PacketSendUtility.broadcastPacket(owner, new SM_UPDATE_PLAYER_APPEARANCE(owner.getObjectId(), getEquippedForAppearance()), true);
		return mainWeapon;
	}

	private Item autoUnfuseWeapon(Item mainWeapon) {
		return ArmsfusionService.unfuseWeapon(owner, mainWeapon);
	}

	public void equipItemForMacros(int itemUniqueId, long slot) {
		Item item = owner.getInventory().getItemByObjId(itemUniqueId);
		ItemSlot[] allSlots = ItemSlot.getSlotsFor(slot);
		if (item == null || allSlots == null || allSlots.length == 0) {
			return;
		}

		synchronized (this) {
			try {
				owner.getInventory().remove(item);
			} catch (Exception e) {
				log.error("equipItemForMacros error removing item from inventory", e);
				return;
			}

			if (equipment.get(allSlots[0].getSlotIdMask()) != null) {
				log.error("CHECKPOINT : putting item to already equipped slot. Info slot: " + slot + " new item: "
						+ item.getItemTemplate().getTemplateId() + " old item: "
						+ equipment.get(allSlots[0].getSlotIdMask()).getItemTemplate().getTemplateId());
				return;
			}

			for (ItemSlot eSlot : allSlots) {
				equipment.put(eSlot.getSlotIdMask(), item);
			}

			if (item.getItemTemplate().getItemGroup() == ItemGroup.POWER_SHARDS) {
				owner.setState(CreatureState.POWERSHARD);
				PacketSendUtility.sendPacket(owner, new SM_EMOTION(owner, EmotionType.POWERSHARD_ON, 0, 0));
			}

			item.setEquipped(true);
			item.setEquipmentSlot(slot);
			ItemPacketService.updateItemAfterEquip(owner, item);
			// update stats
			if ((item.getEquipmentSlot() & ItemSlot.MAIN_OFF_OR_SUB_OFF.getSlotIdMask()) == 0) {
				notifyItemEquipped(item);
			}
			owner.getLifeStats().updateCurrentStats();
			setPersistentState(PersistentState.UPDATE_REQUIRED);
		}
	}

	public void equipItemForMacros(int itemUniqueId, int slot) {
		equipItemForMacros(itemUniqueId, (long) slot);
	}

	public void unEquipItemForMacros(int itemUniqueId) {
		Item itemToUnequip = null;
		synchronized (this) {
			for (Item item : equipment.values()) {
				if (item.getObjectId() == itemUniqueId) {
					itemToUnequip = item;
					break;
				}
			}

			if (itemToUnequip == null) {
				return;
			}

			if (itemToUnequip.getItemTemplate().getEquipmentType() == null) {
				log.error("unEquipItemForMacros EquipmentType null");
				return;
			}

			if (itemToUnequip.getItemTemplate().getItemGroup() == ItemGroup.POWER_SHARDS) {
				owner.unsetState(CreatureState.POWERSHARD);
				PacketSendUtility.sendPacket(owner, new SM_EMOTION(owner, EmotionType.POWERSHARD_OFF, 0, 0));
			}

			ItemSlot[] allSlots = ItemSlot.getSlotsFor(itemToUnequip.getEquipmentSlot());
			if (allSlots == null || allSlots.length == 0) {
				return;
			}
			Item item = equipment.remove(allSlots[0].getSlotIdMask());

			if (allSlots.length > 1) {
				if (!item.getItemTemplate().isTwoHandWeapon()) {
					equipment.put(allSlots[0].getSlotIdMask(), item);
					throw new IllegalArgumentException("slot can not be composite!");
				}
				equipment.remove(allSlots[1].getSlotIdMask());
			}

			item.setEquipped(false);
			item.setEquipmentSlot(com.aionemu.gameserver.model.items.storage.ItemStorage.FIRST_AVAILABLE_SLOT);
			setPersistentState(PersistentState.UPDATE_REQUIRED);
			notifyItemUnequip(item);
			owner.getLifeStats().updateCurrentStats();
			owner.getGameStats().updateStatsAndSpeedVisually();
			owner.getInventory().put(item);
		}
	}

	/**
	 * @param slot
	 *          - Must be composite for dual weapons
	 */
	private void unEquip(long slot) {
		boolean updateStats = false;
		ItemSlot[] allSlots = ItemSlot.getSlotsFor(slot);
		for (ItemSlot itemSlot : allSlots) {
			Item item = equipment.remove(itemSlot.getSlotIdMask());
			if (item == null || !item.isEquipped()) // check isEquipped to avoid duplicate notifyUnequip, since two handed weapons occupy two slots
				continue;
			if (item.hasFusionedItem()) {
				autoUnfuseWeapon(item);
			}
			updateStats = true;
			item.setEquipped(false);
			item.setEquipmentSlot(com.aionemu.gameserver.model.items.storage.ItemStorage.FIRST_AVAILABLE_SLOT);
			owner.getInventory().put(item);
			setPersistentState(PersistentState.UPDATE_REQUIRED);
			notifyItemUnequip(item);
		}
		if (updateStats) {
			owner.getLifeStats().updateCurrentStats();
			owner.getGameStats().updateStatsAndSpeedVisually();
		}
	}

	private void unequip(Item item) {
		if (item.getItemTemplate().isTwoHandWeapon()) {
			for (ItemSlot slot : ItemSlot.getSlotsFor(item.getEquipmentSlot()))
				equipment.remove(slot.getSlotIdMask());
		} else {
			equipment.remove(item.getEquipmentSlot());
		}
		item.setEquipped(false);
	}

	private boolean checkAvailableEquipSkills(Item item) {
		if (item.getItemTemplate().isArmor() || item.getItemTemplate().isWeapon())
			return true;

		int[] requiredSkills = item.getItemTemplate().getRequiredSkills();
		if (requiredSkills.length == 0) // if no skills required - validate as true
			return true;

		for (int skill : requiredSkills) {
			if (owner.getSkillList().isSkillPresent(skill))
				return true;
		}

		return false;
	}

	public Item getEquippedItemBySlot(long slot) {
		return equipment.get(slot);
	}

	public Item getEquippedItemByObjId(int itemObjId) {
		synchronized (equipment) {
			for (Item item : equipment.values()) {
				if (item.getObjectId() == itemObjId)
					return item;
				if (item.hasFusionedItem() && item.getFusionedItem() != null && item.getFusionedItem().getObjectId() == itemObjId)
					return item;
			}
		}
		return null;
	}

	public List<Item> getEquippedItemsByItemId(int value) {
		List<Item> equippedItemsById = new ArrayList<>();
		synchronized (equipment) {
			for (Item item : equipment.values()) {
				if (item.getItemTemplate().getTemplateId() == value)
					equippedItemsById.add(item);
			}
		}
		return equippedItemsById;
	}

	public List<Item> getEquippedItems() {
		synchronized (equipment) {
			return equipment.values().stream().distinct().collect(Collectors.toList());
		}
	}

	public Set<Integer> getEquippedItemIds() {
		synchronized (equipment) {
			return equipment.values().stream().map(Item::getItemId).collect(Collectors.toSet());
		}
	}

	public List<Item> getEquippedItemsWithoutStigma() {
		List<Item> equippedItems = new ArrayList<>();
		Set<Item> twoHanded = new HashSet<>();
		synchronized (equipment) {
			for (Item item : equipment.values()) {
				if (!ItemSlot.isStigma(item.getEquipmentSlot())) {
					if (item.getItemTemplate().isTwoHandWeapon() && !twoHanded.add(item))
						continue;
					equippedItems.add(item);
				}
			}
		}
		return equippedItems;
	}

	public List<Item> getEquippedForAppearance() {
		List<Item> equippedItems = new ArrayList<>();
		synchronized (equipment) {
			for (Item item : equipment.values()) {
				if (ItemSlot.isVisible(item.getEquipmentSlot()) && !(item.getItemTemplate().isTwoHandWeapon() && equippedItems.contains(item)))
					equippedItems.add(item);
			}
		}
		return equippedItems;
	}

	public List<Item> getEquippedItemsAllStigma() {
		List<Item> equippedItems = new ArrayList<>();
		synchronized (equipment) {
			for (Item item : equipment.values()) {
				if (ItemSlot.isStigma(item.getEquipmentSlot())) {
					equippedItems.add(item);
				}
			}
		}
		return equippedItems;
	}

	public List<Item> getEquippedItemsRegularStigma() {
		List<Item> equippedItems = new ArrayList<>();
		synchronized (equipment) {
			for (Item item : equipment.values()) {
				if (ItemSlot.isRegularStigma(item.getEquipmentSlot()))
					equippedItems.add(item);
			}
		}
		return equippedItems;
	}

	public List<Item> getEquippedItemsAdvancedStigma() {
		List<Item> equippedItems = new ArrayList<>();
		synchronized (equipment) {
			for (Item item : equipment.values()) {
				if (ItemSlot.isAdvancedStigma(item.getEquipmentSlot())) {
					equippedItems.add(item);
				}
			}
		}
		return equippedItems;
	}

	/**
	 * @return Number of parts equipped belonging to requested itemset
	 */
	public int itemSetPartsEquipped(int itemSetTemplateId) {
		int number = 0;
		List<Integer> counted = new ArrayList<>(); // no double counting for accessory and weapons

		synchronized (equipment) {
			for (Item item : equipment.values()) {
				if ((item.getEquipmentSlot() & ItemSlot.MAIN_OFF_HAND.getSlotIdMask()) != 0
						|| (item.getEquipmentSlot() & ItemSlot.SUB_OFF_HAND.getSlotIdMask()) != 0) {
					continue;
				}
				ItemSetTemplate setTemplate = item.getItemTemplate().getItemSet();
				if (setTemplate != null && setTemplate.getId() == itemSetTemplateId && !counted.contains(item.getItemId())) {
					counted.add(item.getItemId());
					++number;
				}
			}
		}
		return number;
	}

	/**
	 * Should be called only when loading from DB for items isEquipped=1
	 */
	public void onLoadHandler(Item item) {
		if (!checkAvailableEquipSkills(item)) {
			putItemBackToInventory(item);
			return;
		}
		if (!checkDualWieldRestriction(item, item.getEquipmentSlot())) {
			putItemBackToInventory(item);
			return;
		}
		if (item.getEquipmentSlot() == 0 || ItemSlot.getSlotsFor(item.getEquipmentSlot()).length == 0) { // e.g. stigmas saved in the 4.8 slot bits
			log.warn("Unknown equipment slot " + item.getEquipmentSlot() + " for " + item + " of " + owner);
			putItemBackToInventory(item);
			return;
		}
		for (ItemSlot slot : ItemSlot.getSlotsFor(item.getEquipmentSlot())) { // two slots (main+sub) for two-handed weapons
			if (equipment.putIfAbsent(slot.getSlotIdMask(), item) != null) {
				log.warn("Duplicate equipped item in slot " + slot + " for " + owner);
				putItemBackToInventory(item);
			}
		}
	}

	private void putItemBackToInventory(Item item) {
		item.setEquipped(false);
		item.setEquipmentSlot(0);
		setPersistentState(PersistentState.UPDATE_REQUIRED);
		owner.getInventory().put(item);
	}

	/**
	 * Should be called only when equipment object totally constructed on player loading. Applies every equipped item stats modificators
	 */
	public void onLoadApplyEquipmentStats() {
		Item twoHanded = null;
		synchronized (equipment) {
			for (Item item : equipment.values()) {
				if ((item.getEquipmentSlot() & ItemSlot.MAIN_OFF_HAND.getSlotIdMask()) == 0
						&& (item.getEquipmentSlot() & ItemSlot.SUB_OFF_HAND.getSlotIdMask()) == 0) {
					if (item.getItemTemplate().isTwoHandWeapon()) {
						if (twoHanded != null)
							continue;
						twoHanded = item;
					}
					ItemEquipmentListener.onItemEquipment(item, owner);
				}
			}
		}
		owner.getLifeStats().synchronizeWithMaxStats();
	}

	/**
	 * @return true or false
	 */
	public boolean isShieldEquipped() {
		Item subHandItem = equipment.get(ItemSlot.SUB_HAND.getSlotIdMask());
		if (subHandItem == null)
			return false;
		ItemSubType shieldType = subHandItem.getItemTemplate().getItemSubType();
		return shieldType == ItemSubType.SHIELD;
	}

	public Item getEquippedShield() {
		Item subHandItem = equipment.get(ItemSlot.SUB_HAND.getSlotIdMask());
		if (subHandItem == null)
			return null;
		ItemSubType shieldType = subHandItem.getItemTemplate().getItemSubType();
		return (shieldType == ItemSubType.SHIELD) ? subHandItem : null;
	}

	/**
	 * @return <tt>WeaponType</tt> of current weapon in main hand or null
	 */
	public ItemGroup getMainHandWeaponType() {
		Item mainHandItem = equipment.get(ItemSlot.MAIN_HAND.getSlotIdMask());
		if (mainHandItem == null)
			return null;

		return mainHandItem.getItemTemplate().getItemGroup();
	}

	/**
	 * @return <tt>WeaponType</tt> of current weapon in off hand or null
	 */
	public ItemGroup getOffHandWeaponType() {
		Item offHandItem = equipment.get(ItemSlot.SUB_HAND.getSlotIdMask());
		Item mainHandItem = equipment.get(ItemSlot.MAIN_HAND.getSlotIdMask());
		if (mainHandItem == offHandItem)
			offHandItem = null;
		if (offHandItem != null && offHandItem.getItemTemplate().isWeapon())
			return offHandItem.getItemTemplate().getItemGroup();

		return null;
	}

	public boolean isPowerShardEquipped() {
		return getMainHandPowerShard() != null || getOffHandPowerShard() != null;
	}

	public Item getMainHandPowerShard() {
		return equipment.get(ItemSlot.POWER_SHARD_RIGHT.getSlotIdMask());
	}

	public Item getOffHandPowerShard() {
		return equipment.get(ItemSlot.POWER_SHARD_LEFT.getSlotIdMask());
	}

	public void usePowerShard(Item powerShardItem, int count) {
		decreaseEquippedItemCount(powerShardItem.getObjectId(), count);

		if (powerShardItem.getItemCount() <= 0) {// Search for next same power shards stack
			List<Item> powerShardStacks = owner.getInventory().getItemsByItemId(powerShardItem.getItemTemplate().getTemplateId());
			if (powerShardStacks.size() != 0) {
				equipItem(powerShardStacks.get(0).getObjectId(), powerShardItem.getEquipmentSlot());
			} else {
				PacketSendUtility.sendPacket(owner, STR_MSG_WEAPON_BOOST_MODE_BURN_OUT());
				owner.unsetState(CreatureState.POWERSHARD);
			}
		}
	}

	/**
	 * increase item count and return left count
	 */
	public long increaseEquippedItemCount(Item item, long count) {
		// Only Shards can be increased
		if (item.getItemTemplate().getItemGroup() != ItemGroup.POWER_SHARDS)
			return count;

		long leftCount = item.increaseItemCount(count);
		ItemPacketService.updateItemAfterInfoChange(owner, item, ItemUpdateType.STATS_CHANGE);
		setPersistentState(PersistentState.UPDATE_REQUIRED);
		return leftCount;
	}

	public void decreaseEquippedItemCount(int itemObjId, int count) {
		Item equippedItem = getEquippedItemByObjId(itemObjId);

		if (equippedItem.getItemCount() >= count)
			equippedItem.decreaseItemCount(count);
		else
			equippedItem.decreaseItemCount(equippedItem.getItemCount());

		if (equippedItem.getItemCount() == 0) {
			InventoryDAO.store(equippedItem, owner); // must store (delete) before unequip
			unequip(equippedItem);
			PacketSendUtility.sendPacket(owner, new SM_DELETE_ITEM(equippedItem.getObjectId()));
		} else {
			ItemPacketService.updateItemAfterInfoChange(owner, equippedItem, ItemUpdateType.STATS_CHANGE);
		}
		PacketSendUtility.broadcastPacket(owner, new SM_UPDATE_PLAYER_APPEARANCE(owner.getObjectId(), owner.getEquipment().getEquippedForAppearance()),
			true);
		setPersistentState(PersistentState.UPDATE_REQUIRED);
	}

	/**
	 * Switch OFF and MAIN hands
	 */
	public void switchHands() {
		Item mainHandItem = equipment.get(ItemSlot.MAIN_HAND.getSlotIdMask());
		Item subHandItem = equipment.get(ItemSlot.SUB_HAND.getSlotIdMask());
		Item mainOffHandItem = equipment.get(ItemSlot.MAIN_OFF_HAND.getSlotIdMask());
		Item subOffHandItem = equipment.get(ItemSlot.SUB_OFF_HAND.getSlotIdMask());

		List<Item> equippedWeapon = new ArrayList<>();

		if (mainHandItem != null)
			equippedWeapon.add(mainHandItem);
		if (subHandItem != null && subHandItem != mainHandItem)
			equippedWeapon.add(subHandItem);
		if (mainOffHandItem != null)
			equippedWeapon.add(mainOffHandItem);
		if (subOffHandItem != null && subOffHandItem != mainOffHandItem)
			equippedWeapon.add(subOffHandItem);

		for (Item item : equippedWeapon) {
			unequip(item);
			PacketSendUtility.sendPacket(owner, new SM_INVENTORY_UPDATE_ITEM(owner, item, ItemUpdateType.EQUIP_UNEQUIP));
			if (owner.getGameStats() != null) {
				if ((item.getEquipmentSlot() & ItemSlot.MAIN_HAND.getSlotIdMask()) != 0
					|| (item.getEquipmentSlot() & ItemSlot.SUB_HAND.getSlotIdMask()) != 0) {
					notifyItemUnequip(item);
				}
			}
		}

		for (Item item : equippedWeapon) {
			long oldSlots = item.getEquipmentSlot();
			if ((oldSlots & ItemSlot.RIGHT_HAND.getSlotIdMask()) != 0)
				oldSlots ^= ItemSlot.RIGHT_HAND.getSlotIdMask();
			if ((oldSlots & ItemSlot.LEFT_HAND.getSlotIdMask()) != 0)
				oldSlots ^= ItemSlot.LEFT_HAND.getSlotIdMask();
			item.setEquipmentSlot(oldSlots);
		}

		for (Item item : equippedWeapon) {
			if (item.getItemTemplate().isTwoHandWeapon()) {
				ItemSlot[] slots = ItemSlot.getSlotsFor(item.getEquipmentSlot());
				for (ItemSlot slot : slots)
					equipment.put(slot.getSlotIdMask(), item);
			} else {
				equipment.put(item.getEquipmentSlot(), item);
			}
			item.setEquipped(true);
			ItemPacketService.updateItemAfterEquip(owner, item);
		}

		if (owner.getGameStats() != null) {
			for (Item item : equippedWeapon) {
				if ((item.getEquipmentSlot() & ItemSlot.MAIN_HAND.getSlotIdMask()) != 0
					|| (item.getEquipmentSlot() & ItemSlot.SUB_HAND.getSlotIdMask()) != 0) {
					notifyItemEquipped(item);
				}
			}
		}

		owner.getLifeStats().updateCurrentStats();
		owner.getGameStats().updateStatsAndSpeedVisually();
		setPersistentState(PersistentState.UPDATE_REQUIRED);
	}

	public boolean isWeaponEquipped(ItemSubType subType) {
		Item weapon = getMainHandWeapon();
		if (weapon != null && weapon.getItemTemplate().getItemSubType() == subType)
			return true;
		weapon = getOffHandWeapon();
		if (weapon != null && weapon.getItemTemplate().getItemSubType() == subType)
			return true;
		return false;
	}

	public boolean isDualWeaponEquipped() {
		for (ItemSlot offhandSlot : List.of(ItemSlot.SUB_HAND, ItemSlot.MAIN_HAND)) {
			Item weapon = equipment.get(offhandSlot.getSlotIdMask());
			if (weapon == null || !weapon.getItemTemplate().isOneHandWeapon())
				return false;
		}
		return true;
	}

	/**
	 * Only used for new Player creation. Although invalid, but fits its purpose
	 */
	public boolean isSlotEquipped(long slot) {
		return equipment.get(slot) != null;
	}

	public Item getMainHandWeapon() {
		return equipment.get(ItemSlot.MAIN_HAND.getSlotIdMask());
	}

	public Item getOffHandWeapon() {
		Item result = equipment.get(ItemSlot.SUB_HAND.getSlotIdMask());
		if (getMainHandWeapon() == result)
			return null;
		return result;
	}

	@Override
	public PersistentState getPersistentState() {
		return persistentState;
	}

	@Override
	public void setPersistentState(PersistentState persistentState) {
		this.persistentState = persistentState;
	}

	private boolean soulBindItem(final Player player, final Item item, final long slot) {
		if (player.getInventory().getItemByObjId(item.getObjectId()) == null)
			return false;
		if (player.isDead()) {
			PacketSendUtility.sendPacket(player, STR_SOUL_BOUND_INVALID_STANCE(ActionState.DEAD.getL10n()));
			return false;
		} else if (player.isInState(CreatureState.CHAIR)) {
			PacketSendUtility.sendPacket(player, STR_SOUL_BOUND_INVALID_STANCE(ActionState.SITTING.getL10n()));
			return false;
		} else if (player.isInState(CreatureState.RESTING)) {
			PacketSendUtility.sendPacket(player, STR_SOUL_BOUND_INVALID_STANCE(ActionState.RESTING.getL10n()));
			return false;
		} else if (player.isInState(CreatureState.GLIDING)) {
			PacketSendUtility.sendPacket(player, STR_SOUL_BOUND_INVALID_STANCE(ActionState.GLIDING.getL10n()));
			return false;
		} else if (player.isInState(CreatureState.FLYING)) {
			PacketSendUtility.sendPacket(player, STR_SOUL_BOUND_INVALID_STANCE(ActionState.FREE_FLYING.getL10n()));
			return false;
		} else if (player.isInState(CreatureState.WEAPON_EQUIPPED)) {
			PacketSendUtility.sendPacket(player, STR_SOUL_BOUND_INVALID_STANCE(ActionState.COMBAT.getL10n()));
			return false;
		}

		RequestResponseHandler<Player> responseHandler = new RequestResponseHandler<Player>(player) {

			@Override
			public void acceptRequest(Player requester, Player responder) {
				responder.getController().cancelUseItem();

				PacketSendUtility.broadcastPacket(responder,
					new SM_ITEM_USAGE_ANIMATION(responder.getObjectId(), item.getObjectId(), item.getItemId(), 5000, 4), true);

				final ItemUseObserver observer = new ItemUseObserver() {

					@Override
					public void abort() {
						responder.getController().cancelTask(TaskId.ITEM_USE);
						PacketSendUtility.sendPacket(responder, STR_SOUL_BOUND_ITEM_CANCELED(item.getL10n()));
						PacketSendUtility.broadcastPacket(responder,
							new SM_ITEM_USAGE_ANIMATION(responder.getObjectId(), item.getObjectId(), item.getItemId(), 0, 8), true);
					}
				};

				responder.getObserveController().attach(observer);

				// item usage animation
				responder.getController().addTask(TaskId.ITEM_USE, ThreadPoolManager.getInstance().schedule(new Runnable() {

					@Override
					public void run() {
						responder.getObserveController().removeObserver(observer);

						PacketSendUtility.broadcastPacket(responder,
							new SM_ITEM_USAGE_ANIMATION(responder.getObjectId(), item.getObjectId(), item.getItemId(), 0, 6), true);
						PacketSendUtility.sendPacket(responder, STR_SOUL_BOUND_ITEM_SUCCEED(item.getL10n()));

						item.setSoulBound(true);
						ItemPacketService.updateItemAfterInfoChange(owner, item);

						equip(slot, item);
						PacketSendUtility.broadcastPacket(responder, new SM_UPDATE_PLAYER_APPEARANCE(responder.getObjectId(), getEquippedForAppearance()), true);
					}
				}, 5000));
			}

			@Override
			public void denyRequest(Player requester, Player responder) {
				PacketSendUtility.sendPacket(responder, STR_SOUL_BOUND_ITEM_CANCELED(item.getL10n()));
			}
		};

		boolean requested = player.getResponseRequester().putRequest(SM_QUESTION_WINDOW.STR_SOUL_BOUND_ITEM_DO_YOU_WANT_SOUL_BOUND, responseHandler);
		if (requested) {
			PacketSendUtility.sendPacket(player,
				new SM_QUESTION_WINDOW(SM_QUESTION_WINDOW.STR_SOUL_BOUND_ITEM_DO_YOU_WANT_SOUL_BOUND, 0, 0, item.getL10n()));
		} else {
			PacketSendUtility.sendPacket(player, STR_SOUL_BOUND_CLOSE_OTHER_MSG_BOX_AND_RETRY());
		}
		return false;
	}

	private boolean verifyRankLimits(Item item) {
		int rank = owner.getAbyssRank().getRank().getId();
		if (!item.getItemTemplate().getUseLimits().verifyRank(rank))
			return false;
		if (item.getFusionedItemTemplate() != null)
			return item.getFusionedItemTemplate().getUseLimits().verifyRank(rank);
		return true;
	}

	public void checkRankLimitItems() {
		for (Item item : getEquippedItems()) {
			if (!verifyRankLimits(item)) {
				unEquipItem(item.getObjectId(), false);
				PacketSendUtility.sendPacket(owner, STR_MSG_UNEQUIP_RANKITEM(item.getL10n()));
				// TODO: Check retail what happens with full inv and the task msgs.
			}
		}
	}
}

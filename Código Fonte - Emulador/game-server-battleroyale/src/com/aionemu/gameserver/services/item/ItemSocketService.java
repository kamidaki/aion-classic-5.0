package com.aionemu.gameserver.services.item;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import com.aionemu.gameserver.controllers.observer.ItemUseObserver;
import com.aionemu.gameserver.dao.ItemStoneListDAO;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.TaskId;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.Persistable.PersistentState;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.items.ManaStone;
import com.aionemu.gameserver.model.items.storage.Storage;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.model.templates.item.OptionClearTemplate;
import com.aionemu.gameserver.model.templates.item.OptionClearType;
import com.aionemu.gameserver.model.templates.item.enums.ItemGroup;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ITEM_USAGE_ANIMATION;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemAddType;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemUpdateType;
import com.aionemu.gameserver.services.item.ItemService.ItemUpdatePredicate;
import com.aionemu.gameserver.services.trade.PricesService;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.ThreadPoolManager;
import com.aionemu.gameserver.utils.audit.AuditLogger;

/**
 * @author Lost Academy Team & Durak
 */
public class ItemSocketService {

	private static final ItemUpdatePredicate MANASTONE_RETURN = new ItemUpdatePredicate(ItemAddType.ITEM_COLLECT,
		ItemUpdateType.INC_MANASTONE_CLEAR);

	public static ManaStone addManaStone(Item item, int manaStoneItemId, boolean useFusionSlots) {
		if (item == null)
			return null;
		if (useFusionSlots && !item.hasFusionedItem())
			return null;
		int maxSlots = item.getSockets(useFusionSlots);
		Set<ManaStone> manaStones = useFusionSlots ? item.getFusionStones() : item.getItemStones();
		if (manaStones.size() >= maxSlots)
			return null;
		ItemGroup manaStoneCategory = DataManager.ITEM_DATA.getItemTemplate(manaStoneItemId).getItemGroup();
		int specialSlotCount = useFusionSlots ? item.getFusionedItemTemplate().getSpecialSlots() : item.getItemTemplate().getSpecialSlots();
		return insertManaStoneIntoNextPossibleSlot(item, manaStoneItemId, maxSlots, manaStones, manaStoneCategory, specialSlotCount);
	}

	public static ManaStone addManaStone(Item item, int manaStoneItemId, int slotId, boolean useFusionSlots) {
		if (item == null)
			return null;
		Set<ManaStone> manaStones = useFusionSlots ? item.getFusionStones() : item.getItemStones();
		if (manaStones.size() >= Item.MAX_BASIC_STONES)
			return null;
		return insertManastoneIntoSlot(item, manaStones, manaStoneItemId, slotId);
	}

	private static ManaStone insertManaStoneIntoNextPossibleSlot(Item item, int manaStoneItemId, int maxSlots, Set<ManaStone> manaStones,
		ItemGroup manastoneCategory, int specialSlotCount) {
		if (manastoneCategory == ItemGroup.SPECIAL_MANASTONE && specialSlotCount == 0)
			return null;

		int specialSlotsOccupied = 0;
		int normalSlotsOccupied = 0;
		Set<Integer> allSlots = new HashSet<>();
		for (ManaStone ms : manaStones) {
			ItemGroup category = DataManager.ITEM_DATA.getItemTemplate(ms.getItemId()).getItemGroup();
			if (category == ItemGroup.SPECIAL_MANASTONE)
				specialSlotsOccupied++;
			else
				normalSlotsOccupied++;
			allSlots.add(ms.getSlot());
		}

		if ((manastoneCategory == ItemGroup.SPECIAL_MANASTONE && specialSlotsOccupied >= specialSlotCount)
			|| (manastoneCategory == ItemGroup.MANASTONE && normalSlotsOccupied >= (maxSlots - specialSlotCount)))
			return null;

		int start = manastoneCategory == ItemGroup.SPECIAL_MANASTONE ? 0 : specialSlotCount;
		int end = manastoneCategory == ItemGroup.SPECIAL_MANASTONE ? specialSlotCount : maxSlots;
		int nextSlot = start;
		boolean slotFound = false;
		for (; nextSlot < end; nextSlot++) {
			if (!allSlots.contains(nextSlot)) {
				slotFound = true;
				break;
			}
		}
		if (!slotFound)
			return null;
		return insertManastoneIntoSlot(item, manaStones, manaStoneItemId, nextSlot);
	}

	private static ManaStone insertManastoneIntoSlot(Item item, Set<ManaStone> manaStones, int manastoneId, int slotId) {
		item.removeRemainingTuningCountIfPossible();
		ManaStone stone = new ManaStone(item.getObjectId(), manastoneId, slotId, PersistentState.NEW);
		manaStones.add(stone);
		return stone;
	}

	public static void copyFusionStones(Item source, Item target) {
		if (source.hasManaStones()) {
			for (ManaStone manaStone : source.getItemStones())
				target.getFusionStones().add(new ManaStone(target.getObjectId(), manaStone.getItemId(), manaStone.getSlot(), PersistentState.NEW));
			target.removeRemainingTuningCountIfPossible();
		}
	}

	public static void removeManastone(Player player, int itemObjId, int slotNum, boolean isFusionSocket) {
		Storage inventory = player.getInventory();
		Item item = inventory.getItemByObjId(itemObjId);
		if (item == null) {
			item = player.getEquipment().getEquippedItemByObjId(itemObjId);
		}
		if (item == null) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_REMOVE_ITEM_OPTION_NO_TARGET_ITEM());
			return;
		}

		boolean hasManaStones = isFusionSocket ? item.hasFusionStones() : item.hasManaStones();
		if (!hasManaStones) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_REMOVE_ITEM_OPTION_NO_OPTION_TO_REMOVE(item.getL10n()));
			return;
		}

		Set<ManaStone> itemStones = isFusionSocket ? item.getFusionStones() : item.getItemStones();
		ManaStone manaStoneToRemove = itemStones.stream().filter(ms -> ms.getSlot() == slotNum).findFirst().orElse(null);
		if (manaStoneToRemove == null) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_REMOVE_ITEM_OPTION_INVALID_OPTION_SLOT_NUMBER(item.getL10n()));
			return;
		}

		long price = PricesService.getPriceForService(650, player.getRace());
		if (player.getInventory().tryDecreaseKinah(price)) {
			manaStoneToRemove.setPersistentState(PersistentState.DELETED);
			if (isFusionSocket) {
				ItemStoneListDAO.storeFusionStone(Collections.singleton(manaStoneToRemove));
			} else {
				ItemStoneListDAO.storeManaStones(Collections.singleton(manaStoneToRemove));
			}
			// stone stats are keyed by the stone object itself, so they must be ended before the stone is dropped
			if (item.isEquipped())
				player.getGameStats().endEffect(manaStoneToRemove);
			itemStones.remove(manaStoneToRemove);

			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_REMOVE_ITEM_OPTION_SUCCEED(item.getL10n()));
			ItemPacketService.updateItemAfterInfoChange(player, item);
		} else {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_REMOVE_ITEM_OPTION_NOT_ENOUGH_GOLD(item.getL10n()));
		}
	}

	/**
	 * Removal through the Classic 5.0 option clear window, which is opened from the game menu and takes several slots at
	 * once. Cost and destination of each stone (given back as a non-tradeable stone or destroyed) come from option_clear.xml.
	 */
	public static void clearManastones(Player player, Item item, boolean isFusionSocket, List<Integer> slots) {
		if (item.getTemporaryExchangeTimeRemaining() > 0) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_ITEM_OPTION_CLEAR_TEMPORARY_EXCHANGE_TIME());
			return;
		}

		Set<ManaStone> itemStones = isFusionSocket ? item.getFusionStones() : item.getItemStones();
		if (itemStones.isEmpty()) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_ITEM_OPTION_CLEAR_MSG_NO_OPTION(item.getL10n()));
			return;
		}

		Map<ManaStone, OptionClearTemplate> stonesToRemove = new LinkedHashMap<>();
		long price = 0;
		for (ManaStone stone : itemStones) {
			if (slots == null || !slots.contains(stone.getSlot()))
				continue;
			OptionClearTemplate rule = DataManager.OPTION_CLEAR_DATA.getByStoneId(stone.getItemId());
			if (rule == null) { // the window only lists stones the client has a removal rule for
				PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_ITEM_OPTION_CLEAR_NOT_ITEM(item.getL10n()));
				AuditLogger.log(player, "tried to remove stone " + stone.getItemId() + " without option clear rule from item " + item.getItemId());
				return;
			}
			stonesToRemove.put(stone, rule);
			price += rule.getKinah();
		}
		if (stonesToRemove.isEmpty()) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_ITEM_OPTION_CLEAR_EQUIP_NOT_PROC());
			return;
		}
		if (!player.getInventory().tryDecreaseKinah(price, ItemUpdateType.DEC_KINAH_MANASTONE_CLEAR)) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_ITEM_OPTION_CLEAR_HAVE_NOT_KINA(item.getL10n()));
			return;
		}

		for (Map.Entry<ManaStone, OptionClearTemplate> entry : stonesToRemove.entrySet()) {
			ManaStone stone = entry.getKey();
			stone.setPersistentState(PersistentState.DELETED);
			// stone stats are keyed by the stone object itself, so they must be ended before the stone is dropped
			if (item.isEquipped())
				player.getGameStats().endEffect(stone);
			itemStones.remove(stone);
			OptionClearTemplate rule = entry.getValue();
			if (rule.getType() == OptionClearType.RETURN && rule.getReturnItemId() != 0)
				ItemService.addItem(player, rule.getReturnItemId(), 1, false, MANASTONE_RETURN);
		}
		storeStones(stonesToRemove.keySet(), isFusionSocket);
		repackSlots(item, itemStones, isFusionSocket);

		PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_ITEM_OPTION_CLEAR_MSG_SUCCEED(item.getL10n()));
		ItemPacketService.updateItemAfterInfoChange(player, item);
	}

	private static void storeStones(Set<ManaStone> stones, boolean isFusionSocket) {
		if (isFusionSocket)
			ItemStoneListDAO.storeFusionStone(stones);
		else
			ItemStoneListDAO.storeManaStones(stones);
	}

	/**
	 * Closes the gaps a removal leaves behind, so the remaining stones sit in the first slots of their category. The
	 * official 5.0 server does this (measured), and it has to: the client numbers the rows of the removal window from
	 * the sockets it gets in the item info, so a hole would shift every row after it and remove the wrong stone next
	 * time.
	 */
	private static void repackSlots(Item item, Set<ManaStone> stones, boolean isFusionSocket) {
		int specialSlots = isFusionSocket ? item.getFusionedItemTemplate().getSpecialSlots() : item.getItemTemplate().getSpecialSlots();
		List<ManaStone> ordered = new ArrayList<>(stones);
		ordered.sort(Comparator.comparingInt(ManaStone::getSlot));

		Map<ManaStone, Integer> moved = new LinkedHashMap<>();
		int nextSpecial = 0, nextNormal = specialSlots;
		for (ManaStone stone : ordered) {
			boolean isSpecial = DataManager.ITEM_DATA.getItemTemplate(stone.getItemId()).getItemGroup() == ItemGroup.SPECIAL_MANASTONE;
			int slot = isSpecial ? nextSpecial++ : nextNormal++;
			if (slot != stone.getSlot())
				moved.put(stone, slot);
		}
		if (moved.isEmpty())
			return;

		// the row is keyed by slot and ItemStoneListDAO's update ignores it, so a moved stone is deleted and re-inserted
		for (ManaStone stone : moved.keySet())
			stone.setPersistentState(PersistentState.DELETED);
		storeStones(moved.keySet(), isFusionSocket);
		for (Map.Entry<ManaStone, Integer> entry : moved.entrySet()) {
			entry.getKey().setSlot(entry.getValue());
			entry.getKey().setPersistentState(PersistentState.NEW);
		}
		storeStones(moved.keySet(), isFusionSocket);
	}

	/**
	 * Godstone removal through the Classic 5.0 option clear window: one godstone per item, so the client sends only the
	 * item. Cost and destination come from option_clear.xml, where every godstone of the 5.0 client is DELETE.
	 */
	public static void clearGodstone(Player player, Item item) {
		if (item.getTemporaryExchangeTimeRemaining() > 0) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_GIVE_ITEM_PROC_CLEAR_TEMPORARY_EXCHANGE_TIME());
			return;
		}
		if (!item.hasGodStone()) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_GIVE_ITEM_PROC_CLEAR_EQUIP_NOT_PROC());
			return;
		}

		int godstoneId = item.getGodStoneId();
		OptionClearTemplate rule = DataManager.OPTION_CLEAR_DATA.getByStoneId(godstoneId);
		if (rule == null) { // the window only lists items whose godstone the client has a removal rule for
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_GIVE_ITEM_PROC_CLEAR_NOT_ITEM(item.getL10n()));
			AuditLogger.log(player, "tried to remove godstone " + godstoneId + " without option clear rule from item " + item.getItemId());
			return;
		}
		if (!player.getInventory().tryDecreaseKinah(rule.getKinah(), ItemUpdateType.DEC_KINAH_GODSTONE_CLEAR)) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_GIVE_ITEM_PROC_CLEAR_HAVE_NOT_KINA(item.getL10n()));
			return;
		}

		item.setGodStone(null); // marks it deleted and persists it before dropping the reference
		if (rule.getType() == OptionClearType.RETURN && rule.getReturnItemId() != 0)
			ItemService.addItem(player, rule.getReturnItemId(), 1);

		PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_GIVE_ITEM_PROC_CLEAR_COMPLETE(item.getL10n()));
		ItemPacketService.updateItemAfterInfoChange(player, item);
	}

	public static void removeAllManastone(Player player, Item item) {
		if (item == null || !item.hasManaStones())
			return;

		Set<ManaStone> itemStones = item.getItemStones();
		for (ManaStone ms : itemStones)
			ms.setPersistentState(PersistentState.DELETED);
		ItemStoneListDAO.storeManaStones(itemStones);
		itemStones.clear();

		ItemPacketService.updateItemAfterInfoChange(player, item);
	}

	public static void removeAllFusionStone(Player player, Item item) {
		if (item == null || !item.hasFusionStones())
			return;

		Set<ManaStone> itemStones = item.getFusionStones();
		for (ManaStone ms : itemStones)
			ms.setPersistentState(PersistentState.DELETED);
		ItemStoneListDAO.storeFusionStone(itemStones);
		itemStones.clear();

		ItemPacketService.updateItemAfterInfoChange(player, item);
	}

	public static void socketGodstone(Player player, Item weapon, int stoneId) {
		if (weapon == null) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_GIVE_ITEM_PROC_NO_TARGET_ITEM());
			return;
		}

		if (!weapon.canSocketGodstone()) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_GIVE_ITEM_PROC_NOT_PROC_GIVABLE_ITEM(weapon.getL10n()));
			AuditLogger.log(player, "tried to insert godstone in not compatible item " + weapon.getItemId());
			return;
		}

		Item godstone = player.getInventory().getItemByObjId(stoneId);
		if (godstone == null) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_GIVE_ITEM_PROC_NO_PROC_GIVE_ITEM());
			return;
		}

		ItemTemplate itemTemplate = godstone.getItemTemplate();
		if (itemTemplate.getGodstoneInfo() == null) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_GIVE_ITEM_PROC_NO_PROC_GIVE_ITEM());
			return;
		}

		final ItemUseObserver observer = new ItemUseObserver() {
			@Override
			public void abort() {
				player.getObserveController().removeObserver(this);
				player.getController().cancelTask(TaskId.ITEM_USE);
				PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_MSG_GIVE_PROC_CANCEL(weapon.getL10n()));
				PacketSendUtility.broadcastPacketAndReceive(player,
					new SM_ITEM_USAGE_ANIMATION(player.getObjectId(), stoneId, itemTemplate.getTemplateId(), 0, 3, 0));
			}
		};

		player.getObserveController().attach(observer);

		PacketSendUtility.broadcastPacketAndReceive(player,
			new SM_ITEM_USAGE_ANIMATION(player.getObjectId(), stoneId, itemTemplate.getTemplateId(), 2000, 0, 0));

		player.getController().addTask(TaskId.ITEM_USE, ThreadPoolManager.getInstance().schedule(() -> {
			player.getObserveController().removeObserver(observer);

			PacketSendUtility.broadcastPacketAndReceive(player,
				new SM_ITEM_USAGE_ANIMATION(player.getObjectId(), stoneId, itemTemplate.getTemplateId(), 0, 1, 0));

			if (!player.getInventory().decreaseByObjectId(stoneId, 1))
				return;

			weapon.addGodStone(itemTemplate.getTemplateId());
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_GIVE_ITEM_PROC_ENCHANTED_TARGET_ITEM(weapon.getL10n()));

			ItemPacketService.updateItemAfterInfoChange(player, weapon);
		}, 2000));
	}
}

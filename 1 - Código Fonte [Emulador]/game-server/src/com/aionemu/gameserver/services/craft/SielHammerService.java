package com.aionemu.gameserver.services.craft;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;
import com.aionemu.gameserver.GameServer;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.dataholders.SielHammerData;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.items.storage.Storage;
import com.aionemu.gameserver.model.items.storage.StorageType;
import com.aionemu.gameserver.model.templates.item.SielHammerTable;
import com.aionemu.gameserver.model.templates.item.SielHammerTable.Band;
import com.aionemu.gameserver.model.templates.item.SielHammerTable.Reward;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SIEL_HAMMER_EVENT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SIEL_HAMMER_RESULT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SIEL_HAMMER_RESULT.Result;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_CUBE_UPDATE;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemAddType;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemUpdateType;
import com.aionemu.gameserver.services.item.ItemService;
import com.aionemu.gameserver.services.item.ItemService.ItemUpdatePredicate;
import com.aionemu.gameserver.skillengine.task.AbstractInteractionTask;
import com.aionemu.gameserver.utils.PacketSendUtility;

/** Menu-based Siel's Hammer, driven by the official can_crush/crush_name tables. */
public final class SielHammerService {
	private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(SielHammerService.class);
	private static final int DURATION = 2000;
	private static final ItemUpdatePredicate REWARD_UPDATE = new ItemUpdatePredicate(ItemAddType.CRUSH_RESULT, ItemUpdateType.INC_ITEM_MERGE);
	private SielHammerService() { }
	private record Selection(Item item, long quantity, SielHammerTable table, Band band, int enchantment) { }
	private record Plan(List<Selection> selections, long kinah) { }
	private record RewardKey(int itemId, boolean bonus) { }

	public static void start(Player player, Map<Integer, Long> selected) {
		synchronized (player) {
			if (player.getInteractionTask() != null) return; // do not close another accepted interaction
			Plan plan = resolve(player.getInventory(), DataManager.SIEL_HAMMER_DATA, selected);
			String reason = !canCrush(player) ? "player state" : plan == null ? "invalid item selection"
				: player.getInventory().getKinah() < plan.kinah ? "insufficient Kinah"
				: !hasRoom(player.getInventory(), plan) ? "insufficient inventory space" : null;
			if (reason != null) { reject(player, reason, selected); return; }
			new CrushTask(player, java.util.Collections.unmodifiableMap(new LinkedHashMap<>(selected)), plan).start();
		}
	}

	public static void cancel(Player player) {
		synchronized (player) {
			if (player.getInteractionTask() instanceof CrushTask task) task.abort();
		}
	}

	private static boolean canCrush(Player player) {
		return player.isOnline() && player.isSpawned() && !player.isDead() && !player.isTrading() && !player.hasStore()
			&& !GameServer.isShuttingDownSoon();
	}

	/** Use object ids, never client-supplied item ids/costs. Bound each quantity by its official stack size. */
	private static Plan resolve(Storage inventory, SielHammerData data, Map<Integer, Long> selected) {
		if (data == null || selected.isEmpty() || selected.size() > 20) return null;
		List<Selection> selections = new ArrayList<>();
		long kinah = 0;
		try {
			for (var entry : selected.entrySet()) {
				Item item = inventory.getItemByObjId(entry.getKey());
				long quantity = entry.getValue();
				if (entry.getKey() == 0 || item == null || item.isEquipped() || quantity <= 0 || quantity > item.getItemCount()
					|| quantity > Math.max(1, item.getItemTemplate().getMaxStackCount())
					|| item.getExpireTime() > 0 && item.getExpireTimeRemaining() <= 0) return null;
				SielHammerTable table = data.getTable(item.getItemId());
				Band band = table == null ? null : table.getBand(item.getEnchantLevel());
				if (band == null) return null;
				kinah = Math.addExact(kinah, Math.multiplyExact(quantity, table.getKinah()));
				selections.add(new Selection(item, quantity, table, band, item.getEnchantLevel()));
			}
		} catch (ArithmeticException e) { return null; }
		return new Plan(List.copyOf(selections), kinah);
	}

	private static Map<Integer, Long> maximumRewards(Plan plan) {
		Map<Integer, Long> maximum = new HashMap<>();
		for (var selection : plan.selections) {
			Map<Integer, Long> perUnit = new HashMap<>();
			for (var reward : selection.band.getResults())
				if (reward.getProbability() > 0) perUnit.merge(reward.getItemId(), reward.getCount(), Math::max);
			var bonus = selection.band.getBonus();
			if (bonus != null && bonus.getProbability() > 0) perUnit.merge(bonus.getItemId(), bonus.getCount(), Math::addExact);
			perUnit.forEach((id, count) -> maximum.merge(id, Math.multiplyExact(count, selection.quantity), Math::addExact));
		}
		return maximum;
	}

	/** Reserve every possible result before rolling, including bonus and capacity freed by the selected inputs. */
	private static boolean hasRoom(Storage inventory, Plan plan) {
		Map<Integer, Long> debit = new HashMap<>();
		Map<Integer, Long> available = new HashMap<>();
		for (var selection : plan.selections) {
			debit.put(selection.item.getObjectId(), selection.quantity);
			if (selection.quantity == selection.item.getItemCount())
				available.merge(selection.item.getItemTemplate().getExtraInventoryId(), 1L, Long::sum);
		}
		Map<Integer, Long> needed = new HashMap<>();
		for (var entry : maximumRewards(plan).entrySet()) {
			var template = DataManager.ITEM_DATA.getItemTemplate(entry.getKey());
			if (template == null) return false;
			if (template.isKinah()) continue;
			long stack = template.isStackable() ? template.getMaxStackCount() : 1;
			long capacity = 0;
			if (template.isStackable())
				for (Item item : inventory.getItemsByItemId(entry.getKey())) {
					long remaining = item.getItemCount() - debit.getOrDefault(item.getObjectId(), 0L);
					if (remaining > 0) capacity += Math.max(0, stack - remaining);
				}
			long remaining = Math.max(0, entry.getValue() - capacity);
			if (remaining > 0) needed.merge(template.getExtraInventoryId(), 1 + (remaining - 1) / stack, Long::sum);
		}
		return needed.entrySet().stream().allMatch(e -> e.getValue() <= inventory.getFreeSlots(e.getKey()) + available.getOrDefault(e.getKey(), 0L));
	}

	private static void reject(Player player, String reason, Map<Integer, Long> selected) {
		log.warn("Siel Hammer rejected: player={}, reason={}, selected={}", player.getObjectId(), reason, selected);
		PacketSendUtility.sendPacket(player, new SM_SIEL_HAMMER_EVENT(2, 0));
		PacketSendUtility.sendPacket(player, new SM_SIEL_HAMMER_RESULT(1, List.of()));
		int message = reason.equals("insufficient Kinah") ? 1403923 : reason.equals("insufficient inventory space") ? 1403924 : 1404452;
		PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(message));
	}

	private static void rollback(Player player, List<Selection> applied) {
		for (var selection : applied)
			ItemService.addItem(player, selection.item, selection.quantity, true, ItemService.DEFAULT_UPDATE_PREDICATE);
		PacketSendUtility.sendPacket(player, SM_CUBE_UPDATE.cubeSize(StorageType.CUBE, player));
	}
	private static boolean consume(Player player, Plan plan) {
		List<Selection> applied = new ArrayList<>();
		for (var selection : plan.selections) {
			if (player.getInventory().getItemByObjId(selection.item.getObjectId()) != selection.item || selection.item.isEquipped()
				|| selection.item.getEnchantLevel() != selection.enchantment
				|| !player.getInventory().decreaseByObjectId(selection.item.getObjectId(), selection.quantity, ItemUpdateType.DEC_ITEM_CRUSH)) {
				rollback(player, applied);
				return false;
			}
			applied.add(selection);
		}
		if (!player.getInventory().tryDecreaseKinah(plan.kinah)) {
			rollback(player, applied);
			return false;
		}
		return true;
	}

	private static void addReward(Map<RewardKey, Long> results, Reward reward, boolean bonus) {
		results.merge(new RewardKey(reward.getItemId(), bonus), reward.getCount(), Math::addExact);
	}
	private static List<Result> roll(Plan plan) {
		Map<RewardKey, Long> results = new LinkedHashMap<>();
		var random = ThreadLocalRandom.current();
		for (var selection : plan.selections)
			for (long i = 0; i < selection.quantity; i++) {
				addReward(results, selection.band.selectResult(random.nextInt(1000)), false);
				if (selection.band.hasBonus(random.nextInt(1000))) addReward(results, selection.band.getBonus(), true);
			}
		return results.entrySet().stream().map(e -> new Result(e.getKey().itemId, e.getValue(), e.getKey().bonus)).toList();
	}

	private static final class CrushTask extends AbstractInteractionTask {
		private final Map<Integer, Long> selected;
		private final Plan plan;
		private boolean finished;
		CrushTask(Player player, Map<Integer, Long> selected, Plan plan) {
			super(player, null);
			this.selected = selected;
			this.plan = plan;
			delay = DURATION;
		}
		@Override
		protected void onInteractionStart() { PacketSendUtility.sendPacket(requester, new SM_SIEL_HAMMER_EVENT(1, DURATION)); }
		@Override
		protected boolean onInteraction() {
			synchronized (requester) {
				if (finished || requester.getInteractionTask() != this) return true;
				finished = true;
				Plan current = resolve(requester.getInventory(), DataManager.SIEL_HAMMER_DATA, selected);
				if (!canCrush(requester) || current == null || !current.equals(plan) || requester.getInventory().getKinah() < plan.kinah
					|| !hasRoom(requester.getInventory(), plan) || !consume(requester, plan)) {
					reject(requester, "selection, state or resources changed during crushing", selected);
					return true;
				}
				List<Result> results = roll(plan);
				PacketSendUtility.sendPacket(requester, new SM_SIEL_HAMMER_RESULT(0, results));
				for (var result : results) ItemService.addItem(requester, result.itemId(), result.count(), true, REWARD_UPDATE);
				PacketSendUtility.sendPacket(requester, SM_CUBE_UPDATE.cubeSize(StorageType.CUBE, requester));
				return true;
			}
		}
		@Override
		protected void onInteractionFinish() { }
		@Override
		protected void onInteractionAbort() {
			synchronized (requester) {
				if (!finished) {
					finished = true;
					PacketSendUtility.sendPacket(requester, new SM_SIEL_HAMMER_EVENT(2, 0));
				}
			}
		}
	}
}

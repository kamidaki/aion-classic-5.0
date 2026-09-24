package com.aionemu.gameserver.services.craft;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;
import java.sql.SQLException;
import com.aionemu.gameserver.dao.SielAnvilDAO;
import com.aionemu.gameserver.network.aion.serverpackets.SM_UNK_01AB;
import com.aionemu.gameserver.GameServer;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.items.ItemId;
import com.aionemu.gameserver.model.items.storage.Storage;
import com.aionemu.gameserver.model.templates.item.SielAnvilRecipe;
import com.aionemu.gameserver.model.templates.item.SielAnvilRecipe.Ingredient;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SIEL_ANVIL_START;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SIEL_ANVIL_RESULT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemUpdateType;
import com.aionemu.gameserver.services.item.ItemService;
import com.aionemu.gameserver.skillengine.task.AbstractInteractionTask;
import com.aionemu.gameserver.utils.PacketSendUtility;

/** Siel's Anvil is menu crafting: no NPC, profession level or learned recipe is required. */
public final class SielAnvilService {
	private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(SielAnvilService.class);
	private static final int DURATION = 3000;
	private static final int CRAFT_ERROR = 1403926;
	private SielAnvilService() { }
	public static void sendProgress(Player player) {
		try { PacketSendUtility.sendPacket(player, new SM_UNK_01AB(SielAnvilDAO.load(player.getObjectId()))); }
		catch (SQLException e) { org.slf4j.LoggerFactory.getLogger(SielAnvilService.class).error("Cannot load Siel Anvil progress for {}", player.getObjectId(), e); }
	}

	public static void cancel(Player player, int recipeId) {
		synchronized (player) {
			if (player.getInteractionTask() instanceof CraftTask task && task.recipe.getId() == recipeId)
				task.abort();
		}
	}

	public static void start(Player player, int recipeId, int groupIndex, int quantity, Map<Integer, Long> supplied, List<Integer> selected) {
		synchronized (player) {
			if (player.getInteractionTask() != null) {
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(CRAFT_ERROR));
				return; // a duplicate request must not cancel the progress display of an accepted craft
			}
			SielAnvilRecipe recipe = DataManager.SIEL_ANVIL_DATA.getRecipe(recipeId);
			Map<Integer, Long> costs = resolveCosts(player.getInventory(), recipe, groupIndex, quantity, supplied, selected);
			String rejection = !canCraft(player) ? "player state"
				: recipe == null ? "unknown recipe" : !recipe.isEnabled() ? "disabled recipe"
				: costs == null ? "material group or selected equipment mismatch"
				: !hasMaterials(player.getInventory(), costs) ? "insufficient materials"
				: !hasRoomForEveryOutcome(player, recipe, quantity) ? "insufficient inventory space" : null;
			if (rejection != null) {
				log.warn("Siel Anvil rejected: player={}, recipe={}, group={}, quantity={}, reason={}, materials={}, selectedObjects={}",
					player.getObjectId(), recipeId, groupIndex, quantity, rejection, supplied, selected);
				reject(player, recipeId, CRAFT_ERROR);
				return;
			}
			new CraftTask(player, recipe, Map.copyOf(costs), List.copyOf(selected), quantity).start();
		}
	}

	/** Pair quantities describe ONE attempt; equipment is carried separately as inventory object ids. */
	private static Map<Integer, Long> resolveCosts(Storage inventory, SielAnvilRecipe recipe, int groupIndex, int quantity,
		Map<Integer, Long> supplied, List<Integer> selected) {
		if (recipe == null || groupIndex < 0 || groupIndex >= recipe.getMaterials().size() || quantity < 1 || quantity > 255)
			return null;
		Map<Integer, Long> ordinary = new HashMap<>(), equipment = new HashMap<>(), chosen = new HashMap<>();
		for (Ingredient item : recipe.getMaterials().get(groupIndex).getItems())
			(item.isSelected() ? equipment : ordinary).merge(item.getItemId(), item.getCount(), Math::addExact);
		if (!ordinary.equals(supplied) || selected.stream().distinct().count() != selected.size() || (!equipment.isEmpty() && quantity != 1))
			return null; // the official equipment selection UI allows a single attempt
		for (int objectId : selected) {
			Item item = inventory.getItemByObjId(objectId);
			if (item == null || item.isEquipped() || item.getItemCount() != 1 || !equipment.containsKey(item.getItemId()))
				return null;
			chosen.merge(item.getItemId(), 1L, Long::sum);
		}
		if (!equipment.equals(chosen)) return null;
		Map<Integer, Long> total = new HashMap<>(equipment);
		ordinary.forEach((id, count) -> total.merge(id, Math.multiplyExact(count, quantity), Math::addExact));
		return total;
	}

	private static boolean canCraft(Player player) {
		return player.isOnline() && player.isSpawned() && !player.isDead() && !player.isTrading() && !player.hasStore()
			&& !GameServer.isShuttingDownSoon();
	}

	private static boolean hasMaterials(Storage inventory, Map<Integer, Long> costs) {
		return costs.entrySet().stream().allMatch(e -> e.getValue() > 0
			&& (e.getKey() == ItemId.KINAH ? inventory.getKinah() : inventory.getItemCountByItemId(e.getKey())) >= e.getValue());
	}

	private static boolean hasRoomForEveryOutcome(Player player, SielAnvilRecipe recipe, int quantity) {
		// Check all outcomes BEFORE rolling: insufficient space must not become a free reroll.
		List<Map<Integer, Long>> outcomes = new ArrayList<>();
		for (var product : recipe.getProducts())
			if (product.getProbability() > 0) outcomes.add(Map.of(product.getItemId(), product.getCount()));
		if (recipe.getProducts().stream().mapToInt(p -> p.getProbability()).sum() < 10000) {
			Map<Integer, Long> refunds = new HashMap<>();
			for (Ingredient refund : recipe.getRefunds()) refunds.merge(refund.getItemId(), refund.getCount(), Long::sum);
			outcomes.add(refunds);
		}
		List<Integer> ids = outcomes.stream().flatMap(o -> o.keySet().stream()).distinct().toList();
		long[][] rewards = new long[outcomes.size()][ids.size()];
		long[] stackSizes = new long[ids.size()], freeStack = new long[ids.size()];
		int[] bags = new int[ids.size()];
		for (int i = 0; i < ids.size(); i++) {
			var template = DataManager.ITEM_DATA.getItemTemplate(ids.get(i));
			if (template == null) return false;
			bags[i] = template.getExtraInventoryId();
			stackSizes[i] = template.isKinah() ? Long.MAX_VALUE : template.isStackable() ? template.getMaxStackCount() : 1;
			if (template.isKinah()) freeStack[i] = Long.MAX_VALUE;
			else if (template.isStackable())
				for (Item item : player.getInventory().getItemsByItemId(ids.get(i)))
					freeStack[i] += Math.max(0, stackSizes[i] - item.getItemCount());
			for (int j = 0; j < outcomes.size(); j++) rewards[j][i] = outcomes.get(j).getOrDefault(ids.get(i), 0L);
		}
		for (int bag : java.util.Arrays.stream(bags).distinct().toArray())
			if (maximumSlots(quantity, rewards, stackSizes, freeStack, bags, bag) > player.getInventory().getFreeSlots(bag)) return false;
		return true;
	}

	/** At most three mutually exclusive outcomes; include all possible mixed batch results. */
	private static long maximumSlots(int quantity, long[][] rewards, long[] stackSizes, long[] freeStack, int[] bags, int bag) {
		long maximum = 0;
		for (int first = rewards.length == 1 ? quantity : 0; first <= quantity; first++) {
			for (int second = rewards.length == 2 ? quantity - first : 0;
				second <= (rewards.length > 1 ? quantity - first : 0); second++) {
				long slots = 0;
				for (int i = 0; i < stackSizes.length; i++) {
					if (bags[i] != bag) continue;
					long count = rewards[0][i] * first;
					if (rewards.length > 1) count += rewards[1][i] * second;
					if (rewards.length > 2) count += rewards[2][i] * (quantity - first - second);
					long remaining = Math.max(0, count - freeStack[i]);
					if (remaining > 0) slots += 1 + (remaining - 1) / stackSizes[i];
				}
				maximum = Math.max(maximum, slots);
			}
		}
		return maximum;
	}

	private static void reject(Player player, int recipeId, int message) {
		PacketSendUtility.sendPacket(player, new SM_SIEL_ANVIL_START(recipeId, 0));
		PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(message));
	}

	private record Debit(Item item, long count) { }

	private static List<Debit> consume(Player player, Map<Integer, Long> costs, List<Item> selected) {
		List<Debit> plan = new ArrayList<>();
		Map<Integer, Long> remainingCosts = new HashMap<>(costs);
		for (Item item : selected) {
			if (player.getInventory().getItemByObjId(item.getObjectId()) != item || item.isEquipped() || item.getItemCount() != 1)
				return null;
			plan.add(new Debit(item, 1));
			remainingCosts.compute(item.getItemId(), (id, count) -> count - 1);
		}
		for (var cost : remainingCosts.entrySet()) {
			if (cost.getKey() == ItemId.KINAH)
				continue; // Kinah is stored separately from ordinary inventory items.
			long remaining = cost.getValue();
			for (Item item : player.getInventory().getItemsByItemId(cost.getKey())) {
				if (selected.contains(item) || item.isEquipped()) continue;
				long count = Math.min(remaining, item.getItemCount());
				if (count > 0)
					plan.add(new Debit(item, count));
				remaining -= count;
			}
			if (remaining != 0)
				return null;
		}
		List<Debit> applied = new ArrayList<>();
		for (Debit debit : plan) {
			if (!player.getInventory().decreaseByObjectId(debit.item.getObjectId(), debit.count, ItemUpdateType.DEC_SIEL_ANVIL_MATERIAL)) {
				// A concurrent inventory change must not leave a partially paid recipe.
				for (Debit previous : applied)
					ItemService.addItem(player, previous.item, previous.count, true, ItemService.DEFAULT_UPDATE_PREDICATE);
				return null;
			}
			applied.add(debit);
		}
		if (!player.getInventory().tryDecreaseKinah(costs.getOrDefault(ItemId.KINAH, 0L), ItemUpdateType.DEC_KINAH_ENCHANT)) {
			for (Debit previous : applied)
				ItemService.addItem(player, previous.item, previous.count, true, ItemService.DEFAULT_UPDATE_PREDICATE);
			return null;
		}
		return plan;
	}

	private static final class CraftTask extends AbstractInteractionTask {
		private final SielAnvilRecipe recipe;
		private final Map<Integer, Long> costs;
		private final List<Item> selected;
		private final int quantity;
		private boolean finished;

		CraftTask(Player player, SielAnvilRecipe recipe, Map<Integer, Long> costs, List<Integer> selected, int quantity) {
			super(player, null);
			this.recipe = recipe;
			this.costs = costs;
			this.selected = selected.stream().map(player.getInventory()::getItemByObjId).toList();
			this.quantity = quantity;
			delay = DURATION;
		}

		@Override
		protected void onInteractionStart() {
			PacketSendUtility.sendPacket(requester, new SM_SIEL_ANVIL_START(recipe.getId(), DURATION));
		}

		@Override
		protected boolean onInteraction() {
			synchronized (requester) {
				if (finished || requester.getInteractionTask() != this)
					return true;
				finished = true;
				int ceiling = 0;
				if (recipe.getCeilingMax() > 0) {
					try { ceiling = SielAnvilDAO.load(requester.getObjectId()).getOrDefault(recipe.getId(), 0); }
					catch (SQLException e) { reject(requester, recipe.getId(), CRAFT_ERROR); return true; }
				}
				if (!canCraft(requester) || !hasMaterials(requester.getInventory(), costs) || !hasRoomForEveryOutcome(requester, recipe, quantity)) {
					reject(requester, recipe.getId(), CRAFT_ERROR);
					return true;
				}
				List<Debit> debits = consume(requester, costs, selected);
				if (debits == null) { reject(requester, recipe.getId(), CRAFT_ERROR); return true; }
				List<Integer> results = new ArrayList<>();
				List<Ingredient> rewards = new ArrayList<>();
				for (int i = 0; i < quantity; i++) {
					var product = ceiling > 0 && ceiling >= recipe.getCeilingMax() ? recipe.getProducts().getFirst()
						: recipe.selectProduct(ThreadLocalRandom.current().nextInt(10000));
					results.add(product == null ? 3 : product.getIndex());
					rewards.addAll(product == null ? recipe.getRefunds() : List.of(product));
					if (recipe.getCeilingMax() > 0)
						ceiling = recipe.nextCeiling(ceiling, product != null,
							ThreadLocalRandom.current().nextInt(recipe.getCeilingMinGain(), recipe.getCeilingMaxGain() + 1));
				}
				if (recipe.getCeilingMax() > 0) {
					try { SielAnvilDAO.save(requester.getObjectId(), recipe.getId(), ceiling); }
					catch (SQLException e) {
						for (Debit debit : debits) ItemService.addItem(requester, debit.item, debit.count, true, ItemService.DEFAULT_UPDATE_PREDICATE);
						requester.getInventory().increaseKinah(costs.getOrDefault(ItemId.KINAH, 0L));
						reject(requester, recipe.getId(), CRAFT_ERROR); return true;
					}
				}
				PacketSendUtility.sendPacket(requester, new SM_SIEL_ANVIL_RESULT(recipe.getId(), results, ceiling));
				List<Item> originals = new ArrayList<>(selected);
				for (Ingredient reward : rewards) {
					long count = reward.getCount();
					// Return the selected equipment's properties rather than creating a clean substitute.
					for (var it = originals.iterator(); it.hasNext() && count > 0;) {
						Item source = it.next();
						if (source.getItemId() == reward.getItemId()) {
							ItemService.addItem(requester, source, 1, true, ItemService.DEFAULT_UPDATE_PREDICATE);
							it.remove(); count--;
						}
					}
					ItemService.addItem(requester, reward.getItemId(), count, true);
				}
				return true;
			}
		}

		@Override
		public void abort() {
			synchronized (requester) { super.abort(); }
		}

		@Override
		protected void onInteractionAbort() {
			if (!finished) {
				finished = true;
				PacketSendUtility.sendPacket(requester, new SM_SIEL_ANVIL_START(recipe.getId(), 2, 0));
			}
		}

		@Override
		protected void onInteractionFinish() { finished = true; }
	}
}

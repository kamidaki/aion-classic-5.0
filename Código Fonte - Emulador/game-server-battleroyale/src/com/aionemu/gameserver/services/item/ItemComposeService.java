package com.aionemu.gameserver.services.item;

import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.GameServer;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.items.storage.Storage;
import com.aionemu.gameserver.model.templates.item.ItemComposeRecipe;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ITEM_COMPOSE_EVENT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ITEM_COMPOSE_RESULT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemAddType;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemUpdateType;
import com.aionemu.gameserver.services.item.ItemService.ItemUpdatePredicate;
import com.aionemu.gameserver.skillengine.task.AbstractInteractionTask;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * Altar of Transcendence (fusão) do Classic 5.0: aberto pelo quick menu, sem NPC. Cada fusão gasta {@code material_count} itens da receita
 * (qualquer mistura de itemIds do grupo) e a taxa em kinah, e sorteia uma faixa SAME/UP/TOP (items/item_compose.xml).
 * <p>
 * Sequência da captura: S 0x1A6 [receita][1][1000 ms]; 1 s depois kinah (0x1D motivo 0x120), materiais (0x1C/0x1D motivo 0x11D),
 * S 0x1A7 com o resultado e o S_ADD_INVENTORY (cabeçalho 0x11E). O C_CANCEL_ITEM_COMPOSE existe no cliente mas não foi capturado; a fusão só
 * é interrompida pelo logout.
 */
public final class ItemComposeService {

	private static final Logger log = LoggerFactory.getLogger(ItemComposeService.class);
	private static final int DURATION = 1000;
	private static final int MAX_QUANTITY = 255;
	// client_strings_msg 5.0
	private static final int MSG_CANNOT_USE = 1403954; // STR_MSG_CANNOT_USE_DIALOG_ITEM_COMPOSE
	private static final int MSG_NOT_ENOUGH_FEE = 1403955; // STR_MSG_CANNOT_ITEM_COMPOSE_ENOUGH_FEE
	private static final int MSG_FULL_INVENTORY = 1403956; // STR_MSG_CANNOT_ITEM_COMPOSE_FULL_INVENTORY
	private static final int MSG_STOP = 1404007; // STR_MSG_ITEM_COMPOSE_STOP
	private static final int MSG_NOT_ENOUGH_MATERIAL = 1404040; // STR_MSG_CANNOT_ITEM_COMPOSE_NOT_ENOUGH_MATERIAL
	private static final ItemUpdatePredicate RESULT_PREDICATE = new ItemUpdatePredicate(ItemAddType.ITEM_COMPOSE, ItemUpdateType.INC_ITEM_COMPOSE);

	private ItemComposeService() {
	}

	/**
	 * @param materials
	 *          itemId -> quantidade consumida por fusão (o cliente envia a quantidade de fusões separadamente)
	 */
	public static void start(Player player, int recipeId, Map<Integer, Long> materials, int quantity) {
		synchronized (player) {
			if (player.getInteractionTask() != null) {
				reject(player, recipeId, MSG_CANNOT_USE); // pedido repetido não pode interromper a fusão já aceita
				return;
			}
			ItemComposeRecipe recipe = DataManager.ITEM_COMPOSE_DATA.getRecipe(recipeId);
			int message = !canCompose(player) ? MSG_CANNOT_USE : check(player, recipe, materials, quantity);
			if (message != 0) {
				log.info("Altar recusado: player={}, receita={}, quantidade={}, materiais={}, mensagem={}", player.getName(), recipeId, quantity, materials,
					message);
				reject(player, recipeId, message);
				return;
			}
			new ComposeTask(player, recipe, Map.copyOf(materials), quantity).start();
		}
	}

	public static void reject(Player player, int recipeId, int message) {
		PacketSendUtility.sendPacket(player, new SM_ITEM_COMPOSE_EVENT(recipeId, SM_ITEM_COMPOSE_EVENT.REJECTED, 0));
		if (message != 0)
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(message));
	}

	/**
	 * @return 0 se a fusão pode começar, ou a mensagem de recusa
	 */
	private static int check(Player player, ItemComposeRecipe recipe, Map<Integer, Long> materials, int quantity) {
		if (recipe == null || quantity < 1 || quantity > MAX_QUANTITY)
			return MSG_CANNOT_USE;
		long total = 0;
		Storage inventory = player.getInventory();
		for (Map.Entry<Integer, Long> material : materials.entrySet()) {
			long required;
			try {
				required = Math.multiplyExact(material.getValue(), quantity);
				total = Math.addExact(total, material.getValue());
			} catch (ArithmeticException e) {
				return MSG_NOT_ENOUGH_MATERIAL;
			}
			if (!recipe.isMaterial(material.getKey()) || inventory.getItemCountByItemId(material.getKey()) < required)
				return MSG_NOT_ENOUGH_MATERIAL;
		}
		if (total != recipe.getMaterialCount())
			return MSG_NOT_ENOUGH_MATERIAL;
		long fee;
		try {
			fee = Math.multiplyExact(recipe.getFee(), quantity);
		} catch (ArithmeticException e) {
			return MSG_NOT_ENOUGH_FEE;
		}
		if (inventory.getKinah() < fee)
			return MSG_NOT_ENOUGH_FEE;
		if (!hasRoom(player, recipe, quantity))
			return MSG_FULL_INVENTORY;
		return 0;
	}

	private static boolean canCompose(Player player) {
		return player.isOnline() && player.isSpawned() && !player.isDead() && !player.isTrading() && !player.hasStore()
			&& !GameServer.isShuttingDownSoon();
	}

	/**
	 * Espaço para o pior caso de todas as combinações de faixa, antes do sorteio: faltar espaço não pode virar um novo sorteio de graça.
	 */
	private static boolean hasRoom(Player player, ItemComposeRecipe recipe, int quantity) {
		List<ItemComposeRecipe.Result> results = recipe.getResults();
		for (int first = 0; first <= quantity; first++) {
			for (int second = 0; second <= quantity - first; second++) {
				int[] times = { first, second, quantity - first - second };
				Map<Integer, Long> rewards = new HashMap<>();
				boolean possible = true;
				for (int i = 0; i < times.length; i++) {
					if (times[i] == 0)
						continue;
					if (i >= results.size()) {
						possible = false;
						break;
					}
					rewards.merge(results.get(i).getItemId(), results.get(i).getCount() * times[i], Long::sum);
				}
				if (possible && !fits(player.getInventory(), rewards))
					return false;
			}
		}
		return true;
	}

	private static boolean fits(Storage inventory, Map<Integer, Long> rewards) {
		Map<Integer, Long> slotsPerBag = new HashMap<>();
		for (Map.Entry<Integer, Long> reward : rewards.entrySet()) {
			ItemTemplate template = DataManager.ITEM_DATA.getItemTemplate(reward.getKey());
			if (template == null)
				return false;
			long slots = reward.getValue();
			if (template.isStackable()) {
				long room = 0;
				for (Item item : inventory.getItemsByItemId(reward.getKey()))
					room += Math.max(0, template.getMaxStackCount() - item.getItemCount());
				long remaining = Math.max(0, reward.getValue() - room);
				slots = (remaining + template.getMaxStackCount() - 1) / template.getMaxStackCount();
			}
			slotsPerBag.merge(template.getExtraInventoryId(), slots, Long::sum);
		}
		for (Map.Entry<Integer, Long> bag : slotsPerBag.entrySet())
			if (bag.getValue() > inventory.getFreeSlots(bag.getKey()))
				return false;
		return true;
	}

	private static final class ComposeTask extends AbstractInteractionTask {

		private final ItemComposeRecipe recipe;
		private final Map<Integer, Long> materials;
		private final int quantity;
		private boolean finished;

		ComposeTask(Player player, ItemComposeRecipe recipe, Map<Integer, Long> materials, int quantity) {
			super(player, null);
			this.recipe = recipe;
			this.materials = materials;
			this.quantity = quantity;
			delay = DURATION;
		}

		@Override
		protected void onInteractionStart() {
			PacketSendUtility.sendPacket(requester, new SM_ITEM_COMPOSE_EVENT(recipe.getId(), SM_ITEM_COMPOSE_EVENT.STARTED, DURATION));
		}

		@Override
		protected boolean onInteraction() {
			synchronized (requester) {
				if (finished || requester.getInteractionTask() != this)
					return true;
				finished = true;
				int message = !canCompose(requester) ? MSG_CANNOT_USE : check(requester, recipe, materials, quantity);
				if (message != 0) {
					reject(requester, recipe.getId(), message);
					return true;
				}
				Storage inventory = requester.getInventory();
				inventory.decreaseKinah(recipe.getFee() * quantity, ItemUpdateType.DEC_KINAH_ITEM_COMPOSE);
				for (Map.Entry<Integer, Long> material : materials.entrySet())
					if (!inventory.decreaseByItemId(material.getKey(), material.getValue() * quantity, ItemUpdateType.DEC_ITEM_COMPOSE_MATERIAL))
						log.error("Altar: material {} x{} de {} sumiu depois da conferência", material.getKey(), material.getValue() * quantity,
							requester.getName());

				List<SM_ITEM_COMPOSE_RESULT.Reward> wireResults = new java.util.ArrayList<>(quantity);
				Map<Integer, Long> rewards = new LinkedHashMap<>();
				for (int i = 0; i < quantity; i++) {
					ItemComposeRecipe.Result result = recipe.roll(ThreadLocalRandom.current().nextInt(10000));
					wireResults.add(new SM_ITEM_COMPOSE_RESULT.Reward(result.getGrade().ordinal(), result.getItemId(), result.getCount()));
					rewards.merge(result.getItemId(), result.getCount(), Long::sum);
				}
				PacketSendUtility.sendPacket(requester, new SM_ITEM_COMPOSE_RESULT(recipe.getId(), quantity, wireResults));
				rewards.forEach((itemId, count) -> ItemService.addItem(requester, itemId, count, true, RESULT_PREDICATE));
				log.info("Altar: {} fez {}x receita {} ({}) -> {}", requester.getName(), quantity, recipe.getId(), recipe.getName(), rewards);
				return true;
			}
		}

		@Override
		public void abort() {
			synchronized (requester) {
				super.abort();
			}
		}

		@Override
		protected void onInteractionAbort() {
			if (!finished) {
				finished = true;
				PacketSendUtility.sendPacket(requester, new SM_ITEM_COMPOSE_EVENT(recipe.getId(), SM_ITEM_COMPOSE_EVENT.ABORTED, 0));
				PacketSendUtility.sendPacket(requester, new SM_SYSTEM_MESSAGE(MSG_STOP));
			}
		}

		@Override
		protected void onInteractionFinish() {
			finished = true;
		}
	}
}

package com.aionemu.gameserver.services.item;

import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.GameServer;
import com.aionemu.gameserver.dao.InventoryDAO;
import com.aionemu.gameserver.dao.ItemStoneListDAO;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.DescriptionId;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.items.ManaStone;
import com.aionemu.gameserver.model.items.storage.Storage;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.model.templates.item.ItemUpgradeTemplate;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ITEM_UPGRADE_EVENT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ITEM_UPGRADE_RESULT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.abyss.AbyssPointsService;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemAddType;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemDeleteType;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemUpdateType;
import com.aionemu.gameserver.skillengine.task.AbstractInteractionTask;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * Ascend (Item Upgrade) do Classic 5.0: aberto pelo quick menu, sem NPC. O cliente manda a receita, o item e a opção (C 0x106); o item de origem
 * some e nasce o resultado sorteado da opção (FAIL/UP/TOP, items/item_upgrade.xml), com o encantamento da faixa e o que a receita manda passar.
 * <p>
 * Sequência da captura (Outros/outros_2026-09-21_06-10-28, receita 1070): S 0x1AD [receita][1][1000 ms]; 1 s depois o 0xED com os AP, a mensagem
 * STR_MSG_USE_ABYSSPOINT, o 0x1C do item (motivo 0x10A), STR_ITEM_UPGRADE_MSG_UPGRADE_SUCCESS (origem, resultado), S 0x1AE com o objeto novo e o
 * S_ADD_INVENTORY (cabeçalho 0x108). Só a faixa UP foi capturada.
 * <p>
 * Cancelamento (Outros/outros_2026-09-21_14-43-57, 2 de 2): C 0x142 [D itemId de origem] durante o 1 s do Ascend, e o oficial responde
 * S 0x1AD [D 0][C 2][D 0], sem mensagem e sem gastar nada. Sem Ascend em andamento o mesmo pedido fica sem resposta.
 */
public final class ItemUpgradeService {

	private static final Logger log = LoggerFactory.getLogger(ItemUpgradeService.class);
	private static final int DURATION = 1000;
	// client_strings_msg 5.0
	private static final int MSG_ERROR = 1403710; // STR_REGISTER_ITEM__MSG_UPGRADE_ERROR
	private static final int MSG_SUCCESS = 1403711; // STR_ITEM_UPGRADE_MSG_UPGRADE_SUCCESS: %0 origem, %1 resultado
	private static final int MSG_ENCHANT = 1403712; // STR_REGISTER_ITEM_MSG_UPGRADE_CANNOT: %0 encantamento mínimo
	private static final int MSG_NEED_AP = 1403713; // STR_REGISTER_ITEM_MSG_UPGRADE_CANNOT_NEED_AP
	private static final int MSG_NEED_KINAH = 1403714; // STR_REGISTER_ITEM_MSG_UPGRADE_CANNOT_NEED_QINA
	private static final int MSG_EQUIPPED = 1403922; // STR_MSG_UPGRADE_CANNOT_REGISTER_EQUIPPED_ITEM
	private static final int MSG_STOP = 1404166; // STR_MSG_ITEM_UPGRADE_STOP
	private static final int MSG_CANT_USE = 1404167; // STR_MSG_ITEM_UPGRADE_CANT_USE
	private static final int MSG_NOT_AVAILABLE = 1404168; // STR_MSG_ITEM_UPGRADE_ERROR_NOT_AVAILABLE
	private static final int MSG_RESULT_ERROR = 1404200; // STR_MSG_ERROR_ITEM_UPGRADE

	private ItemUpgradeService() {
	}

	public static void start(Player player, int recipeId, int itemObjectId, int optionIndex) {
		synchronized (player) {
			if (player.getInteractionTask() != null) {
				reject(player, recipeId, MSG_CANT_USE); // pedido repetido não pode interromper o Ascend já aceito
				return;
			}
			ItemUpgradeTemplate recipe = DataManager.ITEM_UPGRADE_DATA.getTemplate(recipeId);
			ItemUpgradeTemplate.Option option = recipe == null ? null : recipe.getOption(optionIndex);
			int message = !canUpgrade(player) ? MSG_CANT_USE : check(player, recipe, option, itemObjectId);
			if (message != 0) {
				log.info("Ascend recusado: player={}, receita={}, objeto={}, opção={}, mensagem={}", player.getName(), recipeId, itemObjectId, optionIndex,
					message);
				reject(player, recipeId, message, recipe);
				return;
			}
			new UpgradeTask(player, recipe, option, itemObjectId).start();
		}
	}

	/**
	 * C 0x142: interrompe o Ascend em andamento do item {@code itemId}. Sem Ascend, ou de outro item, não há resposta, como no oficial.
	 */
	public static void cancel(Player player, int itemId) {
		synchronized (player) {
			if (player.getInteractionTask() instanceof UpgradeTask task && task.recipe.getItemId() == itemId) {
				task.cancelledByClient = true;
				task.abort();
			}
		}
	}

	private static void reject(Player player, int recipeId, int message) {
		reject(player, recipeId, message, null);
	}

	private static void reject(Player player, int recipeId, int message, ItemUpgradeTemplate recipe) {
		PacketSendUtility.sendPacket(player, new SM_ITEM_UPGRADE_EVENT(recipeId, SM_ITEM_UPGRADE_EVENT.REJECTED, 0));
		if (message == MSG_ENCHANT && recipe != null)
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(message, recipe.getEnchantMin()));
		else if (message != 0)
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(message));
	}

	private static boolean canUpgrade(Player player) {
		return player.isOnline() && player.isSpawned() && !player.isDead() && !player.isTrading() && !player.hasStore()
			&& !GameServer.isShuttingDownSoon();
	}

	/**
	 * @return 0 se o Ascend pode começar, ou a mensagem de recusa
	 */
	private static int check(Player player, ItemUpgradeTemplate recipe, ItemUpgradeTemplate.Option option, int itemObjectId) {
		if (recipe == null || option == null)
			return MSG_ERROR;
		Storage inventory = player.getInventory();
		Item item = inventory.getItemByObjId(itemObjectId);
		if (item == null)
			return player.getEquipment().getEquippedItemByObjId(itemObjectId) != null ? MSG_EQUIPPED : MSG_ERROR;
		if (item.getItemId() != recipe.getItemId() || item.getItemCount() != 1)
			return MSG_ERROR;
		if (item.getEnchantLevel() < recipe.getEnchantMin() || item.getEnchantLevel() > recipe.getEnchantMax())
			return MSG_ENCHANT;
		if (inventory.getKinah() < option.getKinah())
			return MSG_NEED_KINAH;
		if (player.getAbyssRank().getAp() < option.getAp())
			return MSG_NEED_AP;
		for (ItemUpgradeTemplate.Material material : option.getMaterials())
			if (inventory.getItemCountByItemId(material.getItemId()) < material.getCount())
				return MSG_NOT_AVAILABLE;
		if (!hasRoom(inventory, item, option))
			return MSG_RESULT_ERROR;
		return 0;
	}

	/**
	 * Espaço para qualquer faixa, antes do sorteio: faltar espaço não pode virar um novo sorteio de graça. O item de origem libera o seu espaço.
	 */
	private static boolean hasRoom(Storage inventory, Item item, ItemUpgradeTemplate.Option option) {
		for (ItemUpgradeTemplate.Result result : option.getResults()) {
			ItemTemplate template = DataManager.ITEM_DATA.getItemTemplate(result.getItemId());
			if (template == null)
				return false;
			boolean takesSourceSlot = !template.isStackable() && result.getCount() == 1
				&& template.getExtraInventoryId() == item.getItemTemplate().getExtraInventoryId();
			if (!takesSourceSlot && !ItemService.hasInventorySpace(inventory, template, result.getCount()))
				return false;
		}
		return true;
	}

	/**
	 * Item novo da faixa sorteada: encantamento da faixa (até o máximo do template) e o que a receita manda passar do item de origem.
	 */
	static Item createResult(Item source, ItemUpgradeTemplate recipe, ItemUpgradeTemplate.Result result) {
		Item created = ItemFactory.newItem(result.getItemId(), result.getCount());
		if (created == null)
			return null;
		ItemTemplate template = created.getItemTemplate();
		created.setEnchantLevel(Math.min(result.getEnchant(), template.getMaxEnchantLevel()));
		created.setSoulBound(source.isSoulBound());
		created.setItemCreator(source.getItemCreator());
		if (recipe.isOptionTransfer()) {
			created.setOptionalSockets(source.getOptionalSockets());
			for (ManaStone stone : source.getItemStones())
				ItemSocketService.addManaStone(created, stone.getItemId(), stone.getSlot(), false);
		}
		if (recipe.isProcTransfer() && source.getGodStone() != null)
			created.addGodStone(source.getGodStone().getItemId(), source.getGodStone().getActivatedCount());
		if (recipe.isSkillTransfer())
			created.setBuffSkill(source.getBuffSkill());
		return created;
	}

	private static DescriptionId nameOf(ItemTemplate template) {
		return new DescriptionId(template.getNameId() << 1 | 1);
	}

	private static final class UpgradeTask extends AbstractInteractionTask {

		private final ItemUpgradeTemplate recipe;
		private final ItemUpgradeTemplate.Option option;
		private final int itemObjectId;
		private boolean finished;
		private boolean cancelledByClient;

		UpgradeTask(Player player, ItemUpgradeTemplate recipe, ItemUpgradeTemplate.Option option, int itemObjectId) {
			super(player, null);
			this.recipe = recipe;
			this.option = option;
			this.itemObjectId = itemObjectId;
			delay = DURATION;
		}

		@Override
		protected void onInteractionStart() {
			PacketSendUtility.sendPacket(requester, new SM_ITEM_UPGRADE_EVENT(recipe.getId(), SM_ITEM_UPGRADE_EVENT.STARTED, DURATION));
		}

		@Override
		protected boolean onInteraction() {
			synchronized (requester) {
				if (finished || requester.getInteractionTask() != this)
					return true;
				finished = true;
				int message = !canUpgrade(requester) ? MSG_CANT_USE : check(requester, recipe, option, itemObjectId);
				if (message != 0) {
					reject(requester, recipe.getId(), message, recipe);
					return true;
				}
				Storage inventory = requester.getInventory();
				Item source = inventory.getItemByObjId(itemObjectId);
				ItemUpgradeTemplate.Result result = option.roll(ThreadLocalRandom.current().nextInt(10000));
				Item created = createResult(source, recipe, result);
				if (created == null) {
					reject(requester, recipe.getId(), MSG_RESULT_ERROR, recipe);
					return true;
				}
				if (option.getAp() > 0)
					AbyssPointsService.addAp(requester, -option.getAp());
				if (option.getKinah() > 0)
					inventory.decreaseKinah(option.getKinah(), ItemUpdateType.DEC_KINAH);
				for (ItemUpgradeTemplate.Material material : option.getMaterials())
					if (!inventory.decreaseByItemId(material.getItemId(), material.getCount(), ItemUpdateType.DEC_ITEM_UPGRADE))
						log.error("Ascend: material {} x{} de {} sumiu depois da conferência", material.getItemId(), material.getCount(), requester.getName());
				inventory.delete(source, ItemDeleteType.ITEM_UPGRADE);
				PacketSendUtility.sendPacket(requester,
					new SM_SYSTEM_MESSAGE(MSG_SUCCESS, nameOf(source.getItemTemplate()), nameOf(created.getItemTemplate())));
				PacketSendUtility.sendPacket(requester, new SM_ITEM_UPGRADE_RESULT(recipe.getId(),
					List.of(new SM_ITEM_UPGRADE_RESULT.Result(created.getItemId(), created.getItemCount(), created.getObjectId()))));
				inventory.add(created, ItemAddType.ITEM_UPGRADE);
				InventoryDAO.store(requester);
				if (created.hasManaStones() || created.getGodStone() != null)
					ItemStoneListDAO.save(List.of(created));
				log.info("Ascend: {} usou a receita {} ({}) opção {} em {}+{} -> {} {}+{}", requester.getName(), recipe.getId(), recipe.getName(),
					recipe.getOptions().indexOf(option), source.getItemId(), source.getEnchantLevel(), result.getGrade(), created.getItemId(),
					created.getEnchantLevel());
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
				// captura: o evento de interrupção vai com receita 0
				PacketSendUtility.sendPacket(requester, new SM_ITEM_UPGRADE_EVENT(0, SM_ITEM_UPGRADE_EVENT.ABORTED, 0));
				if (!cancelledByClient) // o cliente não pediu (outra interação, logout): avisa por quê
					PacketSendUtility.sendPacket(requester, new SM_SYSTEM_MESSAGE(MSG_STOP));
			}
		}

		@Override
		protected void onInteractionFinish() {
			finished = true;
		}
	}
}

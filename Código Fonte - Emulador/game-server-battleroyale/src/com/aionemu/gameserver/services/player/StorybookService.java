package com.aionemu.gameserver.services.player;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ThreadLocalRandom;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.GameServer;
import com.aionemu.gameserver.dao.InventoryDAO;
import com.aionemu.gameserver.dao.PlayerStorybookDAO;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.PlayerStorybook;
import com.aionemu.gameserver.model.items.storage.Storage;
import com.aionemu.gameserver.model.stats.calc.functions.StatFunction;
import com.aionemu.gameserver.model.templates.item.DecomposableItemInfo;
import com.aionemu.gameserver.model.templates.item.DecomposableSetItem;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.model.templates.storybook.StorybookAppraiseTemplate;
import com.aionemu.gameserver.model.templates.storybook.StorybookTemplate;
import com.aionemu.gameserver.network.aion.serverpackets.SM_STORYBOOK_APPRAISE_RESULT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_STORYBOOK_DISASSEMBLE_RESULT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_STORYBOOK_FINISHED_LIST;
import com.aionemu.gameserver.network.aion.serverpackets.SM_STORYBOOK_ITEM_RESULT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_STORYBOOK_REGISTERED_LIST;
import com.aionemu.gameserver.network.aion.serverpackets.SM_STORYBOOK_UPDATE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemAddType;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemUpdateType;
import com.aionemu.gameserver.services.item.ItemService;
import com.aionemu.gameserver.services.item.ItemService.ItemUpdatePredicate;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * Book of Legends (USER_STORY_BOOK) do Classic 5.0, pela janela do livro, sem NPC:
 * <ul>
 * <li>identificação (C 0xDC): cada unidade de fragmento desconhecido vira um fragmento sorteado (storybook/storybook.xml, appraise); S 0x171;</li>
 * <li>desmontagem (C 0xDD): cada unidade de fragmento vira o que o decomposable_items dá para ele (o pó de montagem); S 0x172;</li>
 * <li>registro (C 0xE4 [D livro]): dos itens do inventário, o que falta ao livro é gasto e registrado; S 0x14E. O livro completo dá a
 * recompensa: atributos para sempre, skill ou itens.</li>
 * </ul>
 * Capturas (06_Sistemas_Novos_Book_of_Legends, 11/09): 0x1C dos gastos antes do resultado (motivos 0xFC, 0xFE e 0xEC/0xED no 0x1D), e os
 * S_ADD_INVENTORY depois (cabeçalhos 0xFD e 0x50). Nenhum livro completo foi capturado: o S 0x14C sai vazio (ver SM_STORYBOOK_FINISHED_LIST).
 */
public final class StorybookService {

	private static final Logger log = LoggerFactory.getLogger(StorybookService.class);
	/** Pilhas por pedido de identificação ou desmontagem; o cliente tem o limite dele (STR_STORYBOOK_ITEM_COUNT_ERROR), que não foi medido. */
	public static final int MAX_ITEMS_PER_REQUEST = 100;
	// client_strings_msg 5.0
	private static final int MSG_INVENTORY_FULL = 1390182; // STR_MSG_DICE_INVEN_ERROR
	private static final int MSG_REGISTER_RESTRICT = 1401910; // STR_MSG_STORYBOOK_REGISTER_RESTRICT
	private static final int MSG_ALREADY_FINISH = 1401911; // STR_MSG_STORYBOOK_ALREADY_FINISH
	private static final int MSG_ITEM_NOT_FOUND = 1401912; // STR_MSG_STORYBOOK_REGISTER_ITEM_NOT_FOUND
	private static final int MSG_FINISH = 1401913; // STR_MSG_STORYBOOK_FINISH
	private static final int MSG_UNKNOWN_ERROR = 1403344; // STR_STORYBOOK_UNKNOWN_ERROR
	private static final int MSG_APPRAISE_ERROR = 1403345; // STR_STORYBOOK_ITEM_ERROR
	private static final int MSG_UNKNOWN_DISASSEMBLE_ERROR = 1403355; // STR_STORYBOOK_UNKNOWN_DISASSEMBLE_ERROR
	private static final int MSG_DISASSEMBLE_ERROR = 1403356; // STR_STORYBOOK_ITEM_DISASSEMBLE_ERROR
	private static final ItemUpdatePredicate APPRAISE_PREDICATE = new ItemUpdatePredicate(ItemAddType.STORYBOOK_APPRAISE,
		ItemUpdateType.INC_STORYBOOK_APPRAISE);
	private static final ItemUpdatePredicate DISASSEMBLE_PREDICATE = new ItemUpdatePredicate(ItemAddType.STORYBOOK_DISASSEMBLE,
		ItemUpdateType.INC_STORYBOOK_DISASSEMBLE);

	private static volatile Set<Integer> storybookPieces;

	private StorybookService() {
	}

	/**
	 * Carrega o livro e aplica os atributos dos livros completos. Chamado ao montar o personagem, antes de entrar no mundo.
	 */
	public static void onLoad(Player player) {
		PlayerStorybook storybook;
		try {
			storybook = PlayerStorybookDAO.load(player.getObjectId());
		} catch (Exception e) {
			log.error("Book of Legends: não foi possível carregar {}; o sistema fica fora nesta sessão", player.getName(), e);
			return;
		}
		player.setStorybook(storybook);
		List<StatFunction> modifiers = storybook.getModifiers();
		if (!modifiers.isEmpty())
			player.getGameStats().addEffectOnly(storybook, modifiers);
	}

	/**
	 * S 0x14C e S 0x14D do login.
	 */
	public static void onEnterWorld(Player player) {
		PacketSendUtility.sendPacket(player, new SM_STORYBOOK_FINISHED_LIST(player.getObjectId()));
		List<SM_STORYBOOK_REGISTERED_LIST.Entry> entries = new ArrayList<>();
		PlayerStorybook storybook = player.getStorybook();
		if (storybook != null)
			storybook.getRegistered().forEach((storybookId, items) -> items
				.forEach((itemId, count) -> entries.add(new SM_STORYBOOK_REGISTERED_LIST.Entry(storybookId, itemId, count))));
		PacketSendUtility.sendPacket(player, new SM_STORYBOOK_REGISTERED_LIST(player.getObjectId(), entries));
	}

	private static boolean canUse(Player player) {
		return player.getStorybook() != null && player.isOnline() && player.isSpawned() && !player.isDead() && !player.isTrading()
			&& !player.hasStore() && !GameServer.isShuttingDownSoon();
	}

	/**
	 * C 0xDC: identifica os fragmentos desconhecidos, um sorteio por unidade.
	 */
	public static void appraise(Player player, Map<Integer, Long> items) {
		synchronized (player) {
			if (!canUse(player)) {
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_UNKNOWN_ERROR));
				return;
			}
			Storage inventory = player.getInventory();
			Map<Integer, Long> results = new LinkedHashMap<>();
			for (Map.Entry<Integer, Long> entry : items.entrySet()) {
				Item item = inventory.getItemByObjId(entry.getKey());
				StorybookAppraiseTemplate appraise = item == null ? null : DataManager.STORYBOOK_DATA.getAppraise(item.getItemId());
				if (appraise == null || item.getItemCount() < entry.getValue()) {
					log.info("Book of Legends: identificação recusada de {}: objeto {} x{} ({})", player.getName(), entry.getKey(), entry.getValue(),
						item == null ? "fora do inventário" : item.getItemId());
					PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_APPRAISE_ERROR));
					return;
				}
				for (long i = 0; i < entry.getValue(); i++) {
					StorybookAppraiseTemplate.Result result = appraise.roll(ThreadLocalRandom.current().nextInt(10000));
					results.merge(result.getItemId(), result.getCount(), Long::sum);
				}
			}
			finishExchange(player, items, results, ItemUpdateType.DEC_STORYBOOK_APPRAISE, new SM_STORYBOOK_APPRAISE_RESULT(toResults(results)),
				APPRAISE_PREDICATE, "identificou");
		}
	}

	/**
	 * C 0xDD: desmonta os fragmentos, um sorteio do decomposable_items por unidade.
	 */
	public static void disassemble(Player player, Map<Integer, Long> items) {
		synchronized (player) {
			if (!canUse(player)) {
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_UNKNOWN_DISASSEMBLE_ERROR));
				return;
			}
			Storage inventory = player.getInventory();
			Map<Integer, Long> results = new LinkedHashMap<>();
			for (Map.Entry<Integer, Long> entry : items.entrySet()) {
				Item item = inventory.getItemByObjId(entry.getKey());
				DecomposableItemInfo info = item == null || !isStorybookPiece(item.getItemId()) ? null
					: DataManager.DECOMPOSABLE_ITEMS_DATA.getSetDecomposable(item.getItemId());
				if (info == null || item.getItemCount() < entry.getValue()) {
					log.info("Book of Legends: desmontagem recusada de {}: objeto {} x{} ({})", player.getName(), entry.getKey(), entry.getValue(),
						item == null ? "fora do inventário" : item.getItemId());
					PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_DISASSEMBLE_ERROR));
					return;
				}
				for (long i = 0; i < entry.getValue(); i++)
					for (DecomposableSetItem result : info.rollItemsFor(player))
						results.merge(result.getItemId(), (long) result.getCount(), Long::sum);
			}
			finishExchange(player, items, results, ItemUpdateType.DEC_STORYBOOK_DISASSEMBLE,
				new SM_STORYBOOK_DISASSEMBLE_RESULT(toResults(results)), DISASSEMBLE_PREDICATE, "desmontou");
		}
	}

	/**
	 * Gasta as entradas, manda o resultado e entrega os itens, na ordem da captura. Se o resultado não couber, nada é gasto.
	 */
	private static void finishExchange(Player player, Map<Integer, Long> items, Map<Integer, Long> results, ItemUpdateType decreaseType,
		SM_STORYBOOK_ITEM_RESULT packet, ItemUpdatePredicate predicate, String action) {
		Storage inventory = player.getInventory();
		if (!fits(inventory, items, results)) {
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_INVENTORY_FULL));
			return;
		}
		for (Map.Entry<Integer, Long> entry : items.entrySet())
			if (!inventory.decreaseByObjectId(entry.getKey(), entry.getValue(), decreaseType))
				log.error("Book of Legends: objeto {} x{} de {} sumiu depois da conferência", entry.getKey(), entry.getValue(), player.getName());
		PacketSendUtility.sendPacket(player, packet);
		results.forEach((itemId, count) -> ItemService.addItem(player, itemId, count, true, predicate));
		InventoryDAO.store(player);
		log.info("Book of Legends: {} {} {} -> {}", player.getName(), action, items, results);
	}

	private static List<SM_STORYBOOK_ITEM_RESULT.Result> toResults(Map<Integer, Long> results) {
		return results.entrySet().stream().map(e -> new SM_STORYBOOK_ITEM_RESULT.Result(e.getKey(), e.getValue())).toList();
	}

	/**
	 * Espaço para os resultados, contando as pilhas de entrada que somem inteiras.
	 */
	private static boolean fits(Storage inventory, Map<Integer, Long> inputs, Map<Integer, Long> results) {
		Map<Integer, Long> freedSlots = new HashMap<>();
		for (Map.Entry<Integer, Long> input : inputs.entrySet()) {
			Item item = inventory.getItemByObjId(input.getKey());
			if (item != null && item.getItemCount() == input.getValue())
				freedSlots.merge(item.getItemTemplate().getExtraInventoryId(), 1L, Long::sum);
		}
		Map<Integer, Long> neededSlots = new HashMap<>();
		for (Map.Entry<Integer, Long> result : results.entrySet()) {
			ItemTemplate template = DataManager.ITEM_DATA.getItemTemplate(result.getKey());
			if (template == null)
				return false;
			long slots = result.getValue();
			if (template.isStackable()) {
				long room = 0;
				for (Item item : inventory.getItemsByItemId(result.getKey()))
					room += Math.max(0, template.getMaxStackCount() - item.getItemCount());
				long remaining = Math.max(0, result.getValue() - room);
				slots = (remaining + template.getMaxStackCount() - 1) / template.getMaxStackCount();
			}
			neededSlots.merge(template.getExtraInventoryId(), slots, Long::sum);
		}
		for (Map.Entry<Integer, Long> bag : neededSlots.entrySet())
			if (bag.getValue() > inventory.getFreeSlots(bag.getKey()) + freedSlots.getOrDefault(bag.getKey(), 0L))
				return false;
		return true;
	}

	private static boolean isStorybookPiece(int itemId) {
		Set<Integer> pieces = storybookPieces;
		if (pieces == null) {
			pieces = new HashSet<>();
			for (StorybookTemplate storybook : DataManager.STORYBOOK_DATA.getStorybooks())
				pieces.addAll(storybook.getPieces().keySet());
			storybookPieces = pieces = Set.copyOf(pieces);
		}
		return pieces.contains(itemId);
	}

	/**
	 * C 0xE4: registra no livro, de cada item que ele pede, o que falta e o jogador tem no inventário.
	 */
	public static void register(Player player, int storybookId) {
		synchronized (player) {
			PlayerStorybook storybook = player.getStorybook();
			StorybookTemplate template = DataManager.STORYBOOK_DATA.getStorybook(storybookId);
			if (template == null || !canUse(player)) {
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_REGISTER_RESTRICT));
				return;
			}
			if (storybook.isFinished(storybookId)) {
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_ALREADY_FINISH));
				return;
			}
			Storage inventory = player.getInventory();
			Map<Integer, Long> taken = new LinkedHashMap<>();
			for (Map.Entry<Integer, Long> piece : template.getPieces().entrySet()) {
				long missing = piece.getValue() - storybook.getRegistered(storybookId, piece.getKey());
				long take = Math.min(missing, inventory.getItemCountByItemId(piece.getKey()));
				if (take > 0)
					taken.put(piece.getKey(), take);
			}
			if (taken.isEmpty()) {
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_ITEM_NOT_FOUND));
				return;
			}
			boolean completes = template.getPieces().entrySet().stream()
				.allMatch(piece -> storybook.getRegistered(storybookId, piece.getKey()) + taken.getOrDefault(piece.getKey(), 0L) >= piece.getValue());
			if (completes && !rewardItemsFit(inventory, template)) {
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_INVENTORY_FULL));
				return;
			}
			Map<Integer, Long> totals = new LinkedHashMap<>();
			List<SM_STORYBOOK_UPDATE.Entry> entries = new ArrayList<>();
			for (Map.Entry<Integer, Long> take : taken.entrySet()) {
				if (!inventory.decreaseByItemId(take.getKey(), take.getValue(), ItemUpdateType.DEC_STORYBOOK_REGISTER)) {
					log.error("Book of Legends: item {} x{} de {} sumiu depois da conferência", take.getKey(), take.getValue(), player.getName());
					continue;
				}
				long total = storybook.getRegistered(storybookId, take.getKey()) + take.getValue();
				storybook.setRegistered(storybookId, take.getKey(), total);
				totals.put(take.getKey(), total);
				entries.add(new SM_STORYBOOK_UPDATE.Entry(take.getKey(), total));
			}
			boolean finished = storybook.isComplete(template);
			if (finished)
				storybook.setFinished(storybookId);
			InventoryDAO.store(player);
			PlayerStorybookDAO.store(player.getObjectId(), storybookId, totals, finished);
			PacketSendUtility.sendPacket(player, new SM_STORYBOOK_UPDATE(player.getObjectId(), storybookId, entries));
			log.info("Book of Legends: {} registrou no livro {} ({}) {}{}", player.getName(), storybookId, template.getName(), totals,
				finished ? ", livro completo" : "");
			if (finished)
				reward(player, storybook, template);
		}
	}

	private static boolean rewardItemsFit(Storage inventory, StorybookTemplate template) {
		for (StorybookTemplate.Item reward : template.getRewardItems()) {
			ItemTemplate itemTemplate = DataManager.ITEM_DATA.getItemTemplate(reward.getItemId());
			if (itemTemplate == null || !ItemService.hasInventorySpace(inventory, itemTemplate, reward.getCount()))
				return false;
		}
		return true;
	}

	private static void reward(Player player, PlayerStorybook storybook, StorybookTemplate template) {
		PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(MSG_FINISH));
		if (template.getModifiers() != null) {
			player.getGameStats().endEffect(storybook);
			player.getGameStats().addEffect(storybook, storybook.getModifiers());
		}
		for (StorybookTemplate.Skill skill : template.getRewardSkills())
			player.getSkillList().addSkill(player, skill.getSkillId(), skill.getLevel());
		for (StorybookTemplate.Item item : template.getRewardItems())
			ItemService.addItem(player, item.getItemId(), item.getCount(), true);
	}
}

package com.aionemu.gameserver.services;

import java.sql.SQLException;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.dao.LegionDonationDAO;
import com.aionemu.gameserver.dao.LegionMissionDAO;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.dataholders.LegionCraftData;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.items.ItemId;
import com.aionemu.gameserver.model.team.legion.Legion;
import com.aionemu.gameserver.model.team.legion.LegionCraftBoard;
import com.aionemu.gameserver.network.aion.serverpackets.SM_LEGION_CRAFT_LIST;
import com.aionemu.gameserver.network.aion.serverpackets.SM_LEGION_ESSENCE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.ThreadPoolManager;
import com.aionemu.gameserver.services.item.ItemFactory;
import com.aionemu.gameserver.model.team.legion.LegionHistoryAction;
import com.aionemu.gameserver.model.items.storage.LegionStorageProxy;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.dao.InventoryDAO;

/**
 * Doação de materiais para a produção da Legion (C_GUILD 0x14 [D receita][H n] n x ([D item][D quantidade])), reconstruída da criação da Lost
 * Academy (outros2 2026-09-22 10:23: 1 kinah e 1 classic_iddramata_01_essence para a receita 501).
 * <p>
 * Resposta oficial: kinah e item consumidos, STR_MSG_GUILD_MAKING_DONATION_MONEY [nome][kinah], STR_MSG_GUILD_MAKING_DONATION [nome][item][qtd],
 * S 0x15A só com a receita e S 0x156 com os pontos (compo_contribu) de quem doou.
 * <p>
 * PENDENTE_DE_COMPROVACAO: o que acontece com a receita completa (início, tempo, produto, permissão 0x2000/0x4000), se os pontos são por unidade
 * doada (na captura foi 1 unidade de 1 ponto) e quem além do doador recebe as mensagens e o S 0x15A (a captura tem um membro só).
 */
public class LegionCraftService {

	private static final Logger log = LoggerFactory.getLogger(LegionCraftService.class);

	private final Map<Integer, LegionCraftBoard> boards = new ConcurrentHashMap<>();

	public static LegionCraftService getInstance() {
		return SingletonHolder.instance;
	}

	private LegionCraftService() {
	}

	/**
	 * Login, criação e entrada na Legion: a lista inteira das receitas da raça da Legion.
	 */
	public void sendState(Player player) {
		Legion legion = player.getLegion();
		LegionCraftBoard board = legion == null ? null : getBoard(legion);
		if (board == null)
			return;
		List<SM_LEGION_CRAFT_LIST.Recipe> recipes = new ArrayList<>();
		for (LegionCraftData.Recipe recipe : DataManager.LEGION_CRAFT_DATA.getRecipes(player.getRace()))
			recipes.add(toPacket(recipe, board));
		PacketSendUtility.sendPacket(player, new SM_LEGION_CRAFT_LIST(recipes));
	}

	public void donate(Player player, int recipeId, Map<Integer, Long> requested) {
		Legion legion = player.getLegion();
		LegionCraftBoard board = legion == null ? null : getBoard(legion);
		LegionCraftData.Recipe recipe = DataManager.LEGION_CRAFT_DATA.getRecipe(recipeId);
		if (board == null || recipe == null || !DataManager.LEGION_CRAFT_DATA.getRecipes(player.getRace()).contains(recipe) || requested.isEmpty()) {
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1401951)); // STR_MSG_GUILD_MAKING_DONATION_FAIL
			return;
		}
		int points = 0;
		synchronized (board) {
			for (Map.Entry<Integer, Long> e : requested.entrySet()) {
				LegionCraftData.Component component = recipe.getDonatableComponent(e.getKey());
				if (component == null || e.getValue() <= 0) {
					PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1401951)); // STR_MSG_GUILD_MAKING_DONATION_FAIL
					return;
				}
				if (board.getDonated(recipeId, e.getKey()) + e.getValue() > component.getCount()) {
					PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1401953)); // STR_MSG_GUILD_MAKING_DONATION_FAIL_3
					return;
				}
				long owned = e.getKey() == ItemId.KINAH ? player.getInventory().getKinah() : player.getInventory().getItemCountByItemId(e.getKey());
				if (owned < e.getValue()) {
					PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1401952)); // STR_MSG_GUILD_MAKING_DONATION_FAIL_2
					return;
				}
			}
			for (Map.Entry<Integer, Long> e : requested.entrySet()) {
				if (e.getKey() == ItemId.KINAH)
					player.getInventory().decreaseKinah(e.getValue());
				else if (!player.getInventory().decreaseByItemId(e.getKey(), e.getValue()))
					continue;
				board.addDonated(recipeId, e.getKey(), e.getValue());
				points += recipe.getDonatableComponent(e.getKey()).getPoints() * e.getValue().intValue();
			}
			LegionDonationDAO.storeCraft(legion.getLegionId(), recipeId, board);
		}
		for (Map.Entry<Integer, Long> e : requested.entrySet()) {
			if (e.getKey() == ItemId.KINAH) // STR_MSG_GUILD_MAKING_DONATION_MONEY
				PacketSendUtility.broadcastToLegion(legion, new SM_SYSTEM_MESSAGE(1401986, player.getName(), String.valueOf(e.getValue())));
			else // STR_MSG_GUILD_MAKING_DONATION
				PacketSendUtility.broadcastToLegion(legion,
					new SM_SYSTEM_MESSAGE(1401950, player.getName(), "[item:" + e.getKey() + "]", String.valueOf(e.getValue())));
		}
		PacketSendUtility.broadcastToLegion(legion, new SM_LEGION_CRAFT_LIST(List.of(toPacket(recipe, board))));
		if (points > 0) // doação só de kinah (compo_contribu 0) não manda S 0x156 (Nova Pasta 2026-09-29 16:02)
			LegionDonationService.getInstance().addCraftPoints(player, points);
	}

	/**
	 * C_GUILD 0x15 [D receita]: produção, conferida nas capturas da Lost Academy.
	 * <ul>
	 * <li>Essência (receitas 1 a 3, fragmentos, sem tempo; outros2 2026-09-22 19:22): S 0x163 com os fragmentos descontados,
	 * STR_MSG_GUILD_MAKING_START_ESSENCE, S 0x15A com a hora de início, S 0x163 com a essência, STR_GUILD_GET_ESSENCE,
	 * STR_MSG_GUILD_MAKING_COMPLETION_ESSENCE e S 0x15A; histórico de produção 24 (quem) e 25.</li>
	 * <li>Item (Nova Pasta 2026-09-29 16:02: receita 300, 10000 kinah, 1 minuto): S 0x15A com a hora de início e as doações em 0,
	 * STR_MSG_GUILD_MAKING_START [item] e histórico 20; craft_time minutos depois, STR_MSG_GUILD_MAKING_COMPLETION [item],
	 * STR_MSG_GUILD_MAKING_COMPLETION_2, histórico 21 e S 0x15A, e o produto vai para o armazém da Legion (retirado dele na mesma captura).</li>
	 * </ul>
	 * PENDENTE_DE_COMPROVACAO: a permissão de produção (0x2000 ou 0x4000; quem produziu era o Brigade General) e o que acontece com o armazém
	 * cheio.
	 */
	public void produce(Player player, int recipeId) {
		Legion legion = player.getLegion();
		LegionCraftData.Recipe recipe = DataManager.LEGION_CRAFT_DATA.getRecipe(recipeId);
		LegionCraftBoard board = legion == null ? null : getBoard(legion);
		if (board == null || recipe == null || !DataManager.LEGION_CRAFT_DATA.getRecipes(player.getRace()).contains(recipe)) {
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1401981)); // STR_MSG_GUILD_MAKING_FAIL
			return;
		}
		if (recipe.isEssenceRecipe())
			produceEssence(player, legion, board, recipe);
		else if (recipe.getProductId() != 0)
			produceItem(player, legion, board, recipe);
		else
			PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1401981)); // STR_MSG_GUILD_MAKING_FAIL
	}

	private void produceEssence(Player player, Legion legion, LegionCraftBoard board, LegionCraftData.Recipe recipe) {
		int cost = (int) recipe.getEssencePieceCost();
		synchronized (legion) {
			if (legion.getEssencePiece() < cost) {
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1401984)); // STR_MSG_GUILD_MAKING_MATERIAL_SCARCE
				return;
			}
			legion.addEssence(0, -cost);
			PacketSendUtility.broadcastToLegion(legion, new SM_LEGION_ESSENCE(legion.getEssence(), legion.getEssencePiece()));
			PacketSendUtility.broadcastToLegion(legion, new SM_SYSTEM_MESSAGE(1401970)); // STR_MSG_GUILD_MAKING_START_ESSENCE
			board.setCraft(recipe.getId(), (int) (System.currentTimeMillis() / 1000), false);
			LegionDonationDAO.storeCraft(legion.getLegionId(), recipe.getId(), board);
			SM_LEGION_CRAFT_LIST recipeUpdate = new SM_LEGION_CRAFT_LIST(List.of(toPacket(recipe, board)));
			PacketSendUtility.broadcastToLegion(legion, recipeUpdate);
			LegionService.getInstance().addHistory(legion, player.getName(), LegionHistoryAction.ESSENCE_START, "");
			legion.addEssence(recipe.getEssenceCount(), 0);
			LegionMissionDAO.storeGrowth(legion);
			PacketSendUtility.broadcastToLegion(legion, new SM_LEGION_ESSENCE(legion.getEssence(), legion.getEssencePiece()));
			PacketSendUtility.broadcastToLegion(legion, new SM_SYSTEM_MESSAGE(1401979, String.valueOf(recipe.getEssenceCount()))); // STR_GUILD_GET_ESSENCE
			PacketSendUtility.broadcastToLegion(legion, new SM_SYSTEM_MESSAGE(1401971)); // STR_MSG_GUILD_MAKING_COMPLETION_ESSENCE
			LegionService.getInstance().addHistory(legion, "", LegionHistoryAction.ESSENCE_COMPLETE, "");
			PacketSendUtility.broadcastToLegion(legion, recipeUpdate);
		}
	}

	private void produceItem(Player player, Legion legion, LegionCraftBoard board, LegionCraftData.Recipe recipe) {
		int now = (int) (System.currentTimeMillis() / 1000);
		synchronized (board) {
			if (board.isCrafting(recipe.getId())) {
				PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1401949)); // STR_MSG_GUILD_MAKING_START_FAIL
				return;
			}
			for (LegionCraftData.Component component : recipe.getDonatableComponents()) {
				if (board.getDonated(recipe.getId(), component.getItemId()) < component.getCount()) {
					PacketSendUtility.sendPacket(player, new SM_SYSTEM_MESSAGE(1401984)); // STR_MSG_GUILD_MAKING_MATERIAL_SCARCE
					return;
				}
			}
			board.startCraft(recipe.getId(), now);
			LegionDonationDAO.storeCraft(legion.getLegionId(), recipe.getId(), board);
		}
		PacketSendUtility.broadcastToLegion(legion, new SM_LEGION_CRAFT_LIST(List.of(toPacket(recipe, board))));
		PacketSendUtility.broadcastToLegion(legion, new SM_SYSTEM_MESSAGE(1401946, "[item:" + recipe.getProductId() + "]")); // STR_MSG_GUILD_MAKING_START
		LegionService.getInstance().addHistory(legion, player.getName(), LegionHistoryAction.CRAFT_START, "[item_text:" + recipe.getProductId() + "]");
		scheduleCompletion(legion, recipe, now);
	}

	private void scheduleCompletion(Legion legion, LegionCraftData.Recipe recipe, int craftStart) {
		long delay = Math.max(0, (craftStart + recipe.getCraftTime() * 60L) * 1000 - System.currentTimeMillis());
		ThreadPoolManager.getInstance().schedule(() -> completeCraft(legion, recipe), delay);
	}

	private void completeCraft(Legion legion, LegionCraftData.Recipe recipe) {
		LegionCraftBoard board = getBoard(legion);
		if (board == null)
			return;
		synchronized (board) {
			if (!board.isCrafting(recipe.getId()))
				return;
			board.finishCraft(recipe.getId());
			LegionDonationDAO.storeCraft(legion.getLegionId(), recipe.getId(), board);
		}
		Item product = ItemFactory.newItem(recipe.getProductId(), recipe.getProductCount());
		if (new LegionStorageProxy(legion.getLegionWarehouse(), null).add(product) == null)
			log.warn("Legion warehouse of " + legion + " is full, product " + recipe.getProductId() + " of recipe " + recipe.getId() + " was not stored");
		else
			InventoryDAO.store(List.of(product), null, null, legion.getLegionId());
		PacketSendUtility.broadcastToLegion(legion, new SM_SYSTEM_MESSAGE(1401947, "[item:" + recipe.getProductId() + "]")); // STR_MSG_GUILD_MAKING_COMPLETION
		PacketSendUtility.broadcastToLegion(legion, new SM_SYSTEM_MESSAGE(1401948)); // STR_MSG_GUILD_MAKING_COMPLETION_2
		LegionService.getInstance().addHistory(legion, "[item_text:" + recipe.getProductId() + "]", LegionHistoryAction.CRAFT_COMPLETE, "");
		PacketSendUtility.broadcastToLegion(legion, new SM_LEGION_CRAFT_LIST(List.of(toPacket(recipe, board))));
	}

	private static SM_LEGION_CRAFT_LIST.Recipe toPacket(LegionCraftData.Recipe recipe, LegionCraftBoard board) {
		List<SM_LEGION_CRAFT_LIST.Component> components = new ArrayList<>();
		for (LegionCraftData.Component component : recipe.getDonatableComponents())
			components.add(new SM_LEGION_CRAFT_LIST.Component(component.getItemId(), board.getDonated(recipe.getId(), component.getItemId())));
		return new SM_LEGION_CRAFT_LIST.Recipe(recipe.getId(), board.getCraftStart(recipe.getId()), components);
	}

	private LegionCraftBoard getBoard(Legion legion) {
		return boards.computeIfAbsent(legion.getLegionId(), id -> {
			try {
				LegionCraftBoard board = LegionDonationDAO.loadCraft(id);
				// produções em andamento no desligamento terminam no horário previsto (ou já, se passou)
				board.getCrafting().forEach((recipeId, craftStart) -> {
					LegionCraftData.Recipe recipe = DataManager.LEGION_CRAFT_DATA.getRecipe(recipeId);
					if (recipe != null)
						scheduleCompletion(legion, recipe, craftStart);
				});
				return board;
			} catch (SQLException e) {
				log.error("Could not load legion craft of " + legion, e);
				return null;
			}
		});
	}

	/**
	 * @return quantidade por item na ordem pedida; a mesma entrada repetida é somada
	 */
	public static Map<Integer, Long> requested(int[] itemIds, long[] counts) {
		Map<Integer, Long> requested = new LinkedHashMap<>();
		for (int i = 0; i < itemIds.length; i++)
			requested.merge(itemIds[i], counts[i], Long::sum);
		return requested;
	}

	private static class SingletonHolder {

		protected static final LegionCraftService instance = new LegionCraftService();
	}
}

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
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.dataholders.LegionCraftData;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.items.ItemId;
import com.aionemu.gameserver.model.team.legion.Legion;
import com.aionemu.gameserver.model.team.legion.LegionCraftBoard;
import com.aionemu.gameserver.network.aion.serverpackets.SM_LEGION_CRAFT_LIST;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.utils.PacketSendUtility;

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
		LegionDonationService.getInstance().addCraftPoints(player, points);
	}

	private static SM_LEGION_CRAFT_LIST.Recipe toPacket(LegionCraftData.Recipe recipe, LegionCraftBoard board) {
		List<SM_LEGION_CRAFT_LIST.Component> components = new ArrayList<>();
		for (LegionCraftData.Component component : recipe.getDonatableComponents())
			components.add(new SM_LEGION_CRAFT_LIST.Component(component.getItemId(), board.getDonated(recipe.getId(), component.getItemId())));
		return new SM_LEGION_CRAFT_LIST.Recipe(recipe.getId(), components);
	}

	private LegionCraftBoard getBoard(Legion legion) {
		return boards.computeIfAbsent(legion.getLegionId(), id -> {
			try {
				return LegionDonationDAO.loadCraft(id);
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

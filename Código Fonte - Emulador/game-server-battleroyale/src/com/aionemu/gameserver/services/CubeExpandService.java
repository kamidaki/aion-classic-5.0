package com.aionemu.gameserver.services;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.configs.main.CustomConfig;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.RequestResponseHandler;
import com.aionemu.gameserver.model.items.storage.StorageType;
import com.aionemu.gameserver.model.templates.StorageExpansionTemplate;
import com.aionemu.gameserver.network.aion.serverpackets.SM_CUBE_UPDATE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_QUESTION_WINDOW;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemUpdateType;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.PositionUtil;

/**
 * @author Lost Academy Team & Durak
 */
public class CubeExpandService {

	private static final Logger log = LoggerFactory.getLogger(CubeExpandService.class);

	/**
	 * Paid expansion requested by the Classic 5.0 inventory UI. The client shows
	 * its own confirmation before sending the request, so there is no NPC or
	 * second server-side question in this flow.
	 */
	public static void expandCube(Player player) {
		if (player == null || !player.isSpawned() || player.isDead() || player.isTrading())
			return;
		synchronized (player.getInventory()) {
			if (!canExpand(player))
				return;
			int newNpcExpansions = player.getNpcExpands() + 1;
			int maxExpansionLevel = CustomConfig.NPC_CUBE_EXPANDS_SIZE_LIMIT;
			Integer price = DataManager.CUBEEXPANDER_DATA.getPrice(newNpcExpansions);
			if (price == null || newNpcExpansions > maxExpansionLevel) {
				PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_EXTEND_INVENTORY_CANT_EXTEND_MORE());
				return;
			}
			if (player.getInventory().tryDecreaseKinah(price, ItemUpdateType.DEC_KINAH_CUBE))
				npcExpand(player);
			else
				PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_WAREHOUSE_EXPAND_NOT_ENOUGH_MONEY());
		}
	}

	/**
	 * Shows Question window and expands on positive response
	 */
	public static void expandCube(Player player, Npc npc) {
		if (!canInteract(player, npc)) return;
		StorageExpansionTemplate template = DataManager.CUBEEXPANDER_DATA.getCubeExpansionTemplate(npc.getNpcId());
		if (template == null) {
			log.warn("Cube expansion template could not be found for " + npc);
			return;
		}

		if (!canExpand(player))
			return;
		int newNpcExpansions = player.getNpcExpands() + 1;
		int minExpansionLevel = template.getMinExpansionLevel();
		if (newNpcExpansions < minExpansionLevel) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_EXTEND_INVENTORY_CANT_EXTEND_DUE_TO_MINIMUM_EXTEND_LEVEL_BY_THIS_NPC(npc.getObjectTemplate().getL10n(), minExpansionLevel - 1));
			return;
		}
		Integer price = template.getPrice(newNpcExpansions);
		int maxExpansionLevel = Math.min(template.getMaxExpansionLevel(), CustomConfig.NPC_CUBE_EXPANDS_SIZE_LIMIT);
		if (price == null || newNpcExpansions > maxExpansionLevel) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_EXTEND_INVENTORY_CANT_EXTEND_MORE_DUE_TO_MAXIMUM_EXTEND_LEVEL_BY_THIS_NPC(npc.getObjectTemplate().getL10n(), maxExpansionLevel));
			return;
		}
		RequestResponseHandler<Npc> responseHandler = new RequestResponseHandler<>(npc) {

			@Override
			public void acceptRequest(Npc requester, Player responder) {
				synchronized (responder.getInventory()) {
					if (!canInteract(responder, requester) || !canExpand(responder)
						|| responder.getNpcExpands() + 1 != newNpcExpansions) return;
					if (responder.getInventory().tryDecreaseKinah(price, ItemUpdateType.DEC_KINAH_CUBE))
						npcExpand(responder);
					else
						PacketSendUtility.sendPacket(responder, SM_SYSTEM_MESSAGE.STR_WAREHOUSE_EXPAND_NOT_ENOUGH_MONEY());
				}
			}
		};
		boolean result = player.getResponseRequester().putRequest(SM_QUESTION_WINDOW.STR_WAREHOUSE_EXPAND_WARNING, responseHandler);
		if (result) {
			PacketSendUtility.sendPacket(player, new SM_QUESTION_WINDOW(SM_QUESTION_WINDOW.STR_WAREHOUSE_EXPAND_WARNING, 0, 0, String.valueOf(price)));
		}
	}

	/**
	 * Expands the cubes
	 *
	 * @param player
	 * @param type
	 *          1 - npc // 2 - item // 3 - quest
	 */
	private static void expand(Player player, int type) {
		if (!canExpand(player))
			return;
		PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_EXTEND_INVENTORY_SIZE_EXTENDED(9));
		switch (type) {
			case 1: // npc
				player.getCommonData().setNpcExpands(player.getNpcExpands() + 1);
				break;
			case 2: // item
				player.getCommonData().setItemExpands(player.getItemExpands() + 1);
				break;
			case 3: // quest
				player.getCommonData().setQuestExpands(player.getQuestExpands() + 1);
				break;
		}
		player.setCubeLimit();
		PacketSendUtility.sendPacket(player, SM_CUBE_UPDATE.cubeSize(StorageType.CUBE, player));
		player.getGameStats().updateStatsVisually();
	}

	private static boolean canInteract(Player player, Npc npc) {
		return player != null && npc != null && player.isSpawned() && npc.isSpawned()
			&& !player.isDead() && !npc.isDead() && !player.isTrading()
			&& player.getKnownList().getObject(npc.getObjectId()) == npc
			&& PositionUtil.isInRange(player, npc, 10);
	}

	public static void questExpand(Player player) {
		expand(player, 3);
	}

	public static void itemExpand(Player player) {
		expand(player, 2);
	}

	public static void npcExpand(Player player) {
		expand(player, 1);
	}

	public static boolean canExpandByTicket(Player player, int ticketLevel) {
		if (!canExpand(player))
			return false;
		if (player.getItemExpands() >= ticketLevel) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_EXTEND_INVENTORY_CANT_EXTEND_MORE());
			return false;
		}
		return true;
	}

	public static boolean canExpand(Player player) {
		int newExpansions = player.getNpcExpands() + player.getQuestExpands() + player.getItemExpands() + 1;
		if (newExpansions < 0)
			return false;
		if (newExpansions > CustomConfig.CUBE_EXPANSION_LIMIT) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_EXTEND_INVENTORY_CANT_EXTEND_MORE());
			return false;
		}
		return true;
	}
}

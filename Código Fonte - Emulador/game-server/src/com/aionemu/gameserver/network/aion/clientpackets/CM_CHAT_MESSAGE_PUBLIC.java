package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.ChatType;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_MESSAGE;
import com.aionemu.gameserver.restrictions.PlayerRestrictions;
import com.aionemu.gameserver.services.NameRestrictionService;
import com.aionemu.gameserver.services.player.PlayerChatService;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.chathandlers.ChatProcessor;
import com.aionemu.gameserver.utils.stats.AbyssRankEnum;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_CHAT_MESSAGE_PUBLIC extends AionClientPacket {

	private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(CM_CHAT_MESSAGE_PUBLIC.class);

	/**
	 * Chat type
	 */
	private ChatType type;

	/**
	 * Chat message
	 */
	private String message;

	private boolean isLookSurgeryRequest = false;
	private boolean isLookGenderSwitch = false;

	public CM_CHAT_MESSAGE_PUBLIC(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		// Se o payload tiver 4 bytes, trata-se de requisicao do AION Look (SHIFT+R) com o NPC de aparencia/genero
		if (getRemainingBytes() == 4) {
			int npcId = readD();
			// 798390: Palentine (Elyos Beauty/Plastic Surgery), 798392: Marra (Asmo Beauty/Plastic Surgery)
			// 798391: Andu (Elyos Gender Change), 798393: Daskin (Asmo Gender Change)
			if (npcId == 798390 || npcId == 798392) {
				isLookSurgeryRequest = true;
				isLookGenderSwitch = false;
				log.info("[AION_LOOK] Recebida requisicao de aparencia (Modify Appearance) para npcId={}", npcId);
				return;
			} else if (npcId == 798391 || npcId == 798393) {
				isLookSurgeryRequest = true;
				isLookGenderSwitch = true;
				log.info("[AION_LOOK] Recebida requisicao de genero (Change Gender) para npcId={}", npcId);
				return;
			}
		}

		try {
			byte rawType = (byte) readC();
			type = ChatType.getChatType(rawType);
			message = readS();
		} catch (Exception e) {
			type = null;
			message = null;
			if (getRemainingBytes() > 0) {
				readB(getRemainingBytes());
			}
		}
	}

	@Override
	protected void runImpl() {
		final Player player = getConnection().getActivePlayer();
		if (player == null)
			return;

		if (isLookSurgeryRequest) {
			player.getCommonData().setInEditMode(true);
			PacketSendUtility.sendPacket(player, new com.aionemu.gameserver.network.aion.serverpackets.SM_PLASTIC_SURGERY(player, isLookGenderSwitch));
			return;
		}

		if (type == null || message == null)
			return;

		if (ChatProcessor.getInstance().handleChatCommand(player, message))
			return;

		if (!PlayerRestrictions.canChat(player))
			return;

		PlayerChatService.logMessage(player, type, message);
		message = NameRestrictionService.filterMessage(message);

		switch (type) {
			case GROUP:
				if (!player.isInTeam())
					return;
				broadcastToGroupMembers(player);
				break;
			case ALLIANCE:
				if (!player.isInAlliance())
					return;
				broadcastToAllianceMembers(player);
				break;
			case GROUP_LEADER:
				if (!player.isInTeam())
					return;
				// Alert must go to entire group or alliance.
				if (player.isInGroup())
					broadcastToGroupMembers(player);
				else
					broadcastToAllianceMembers(player);
				break;
			case LEGION:
				if (!player.isLegionMember())
					return;
				broadcastToLegionMembers(player);
				break;
			case LEAGUE:
			case LEAGUE_ALERT:
				if (!player.isInLeague())
					return;
				broadcastToLeagueMembers(player);
				break;
			case NORMAL:
			case SHOUT:
				broadcastToPlayers(player);
				break;
			case COMMAND:
				if (player.getAbyssRank().getRank() == AbyssRankEnum.COMMANDER || player.getAbyssRank().getRank() == AbyssRankEnum.SUPREME_COMMANDER)
					broadcastFromCommander(player);
				break;
			default:
				if (!player.isStaff())
					return;
				broadcastToPlayers(player);
				break;
		}
	}

	private void broadcastFromCommander(final Player player) {
		final int senderRace = player.getRace().getRaceId();
		PacketSendUtility.broadcastPacket(player, new SM_MESSAGE(player, message, type), true,
			p -> senderRace == p.getRace().getRaceId() || player.isStaff() || p.isStaff());
	}

	/**
	 * Sends message to all players that are not in blocklist (except GMs)
	 *
	 * @param player
	 */
	private void broadcastToPlayers(final Player player) {
		PacketSendUtility.broadcastPacket(player, new SM_MESSAGE(player, message, type), true,
			p -> !p.getBlockList().contains(player.getObjectId()) || player.isStaff() || p.isStaff());
	}

	/**
	 * Sends message to all group members.
	 *
	 * @param player
	 */
	private void broadcastToGroupMembers(final Player player) {
		player.getCurrentGroup().sendPackets(new SM_MESSAGE(player, message, type));
	}

	/**
	 * Sends message to all alliance members
	 *
	 * @param player
	 */
	private void broadcastToAllianceMembers(final Player player) {
		player.getPlayerAlliance().sendPackets(new SM_MESSAGE(player, message, type));
	}

	/**
	 * Sends message to all league members
	 *
	 * @param player
	 */
	private void broadcastToLeagueMembers(final Player player) {
		player.getPlayerAlliance().getLeague().sendPackets(new SM_MESSAGE(player, message, type));
	}

	/**
	 * Sends message to all legion members
	 *
	 * @param player
	 */
	private void broadcastToLegionMembers(final Player player) {
		PacketSendUtility.broadcastToLegion(player.getLegion(), new SM_MESSAGE(player, message, type));
	}
}

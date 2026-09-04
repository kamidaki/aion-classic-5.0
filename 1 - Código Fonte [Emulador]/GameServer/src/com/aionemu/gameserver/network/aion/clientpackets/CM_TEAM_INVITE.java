package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.model.gameobjects.player.DeniedStatus;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.team.alliance.PlayerAllianceService;
import com.aionemu.gameserver.model.team.group.PlayerGroupService;
import com.aionemu.gameserver.model.team.league.LeagueService;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.S_MESSAGE_CODE;
import com.aionemu.gameserver.utils.ChatUtil;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.Util;
import com.aionemu.gameserver.world.World;

public class CM_TEAM_INVITE extends AionClientPacket {

	private String name;
	private int inviteType;
	
	public CM_TEAM_INVITE(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void readImpl() {
		inviteType = readC();
		name = readS();
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void runImpl() {
		name = ChatUtil.stripAdminTags(name);
		final String playerName = Util.convertName(name);
		final Player inviter = getConnection().getActivePlayer();
		if (inviter.getLifeStats().isAlreadyDead()) {
			// You cannot issue an invitation while you are dead.
			PacketSendUtility.sendPacket(inviter, new S_MESSAGE_CODE(1300163));
			return;
		}
		final Player invited = World.getInstance().findPlayer(playerName);
		if (invited != null) {
			if (invited.getPlayerSettings().isInDeniedStatus(DeniedStatus.GROUP)) {
				sendPacket(S_MESSAGE_CODE.STR_MSG_REJECTED_INVITE_PARTY(invited.getName()));
				return;
			} switch (inviteType) {
				case 0:
					PlayerGroupService.inviteToGroup(inviter, invited);
				break;
				case 12: // 2.5
					PlayerAllianceService.inviteToAlliance(inviter, invited);
				break;
				case 28:
					LeagueService.inviteToLeague(inviter, invited);
				break;
				default:
					PacketSendUtility.sendMessage(inviter, "You used an unknown invite type: " + inviteType);
				break;
			}
		} else {
			inviter.getClientConnection().sendPacket(S_MESSAGE_CODE.STR_NO_SUCH_USER(name));
		}
	}
}
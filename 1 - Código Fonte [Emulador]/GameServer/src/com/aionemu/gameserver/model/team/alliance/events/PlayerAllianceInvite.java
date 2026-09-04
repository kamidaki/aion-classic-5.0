package com.aionemu.gameserver.model.team.alliance.events;


import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.RequestResponseHandler;
import com.aionemu.gameserver.model.team.TeamType;
import com.aionemu.gameserver.model.team.alliance.PlayerAlliance;
import com.aionemu.gameserver.model.team.alliance.PlayerAllianceService;
import com.aionemu.gameserver.model.team.group.PlayerFilters.ExcludePlayerFilter;
import com.aionemu.gameserver.model.team.group.PlayerGroup;
import com.aionemu.gameserver.model.team.group.PlayerGroupService;
import com.aionemu.gameserver.network.aion.serverpackets.S_MESSAGE_CODE;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.google.common.base.Preconditions;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

public class PlayerAllianceInvite extends RequestResponseHandler
{
    private final Player inviter;
    private final Player invited;
	
    public PlayerAllianceInvite(Player inviter, Player invited) {
        super(inviter);
        this.inviter = inviter;
        this.invited = invited;
    }
	
    @Override
    public void acceptRequest(Creature requester, Player responder) {
        if (PlayerAllianceService.canInvite(inviter, invited)) {
            //%0 has joined the alliance.
			PacketSendUtility.sendPacket(inviter, S_MESSAGE_CODE.STR_FORCE_ENTER_HIM(invited.getName()));
			PlayerAlliance alliance = inviter.getPlayerAlliance();
            if (alliance != null) {
                if (alliance.size() == 24) {
                    PacketSendUtility.sendMessage(invited, "That alliance is already full.");
                    PacketSendUtility.sendMessage(inviter, "Your alliance is already full.");
                    return;
                } else if (invited.isInGroup() && invited.getPlayerGroup().size() + alliance.size() > 24) {
                    PacketSendUtility.sendMessage(invited, "That alliance is now too full for your group to join.");
                    PacketSendUtility.sendMessage(inviter, "Your alliance is now too full for that group to join.");
                    return;
                }
            }
            List<Player> playersToAdd = new ArrayList<Player>();
            collectPlayersToAdd(playersToAdd, alliance);
            if (alliance == null) {
                alliance = PlayerAllianceService.createAlliance(inviter, invited, TeamType.ALLIANCE);
            } for (Player member: playersToAdd) {
                PlayerAllianceService.addPlayer(alliance, member);
            }
        }
    }
	
    private final void collectPlayersToAdd(List<Player> playersToAdd, PlayerAlliance alliance) {
        if (inviter.isInGroup()) {
            Preconditions.checkState(alliance == null, "If inviter is in group - alliance should be null");
            PlayerGroup group = inviter.getPlayerGroup();
            playersToAdd.addAll(group.filterMembers(new ExcludePlayerFilter(inviter)));
            Iterator<Player> pIter = group.getMembers().iterator();
            while (pIter.hasNext()) {
                PlayerGroupService.removePlayer(pIter.next());
            }
        } if (invited.isInGroup()) {
            PlayerGroup group = invited.getPlayerGroup();
            playersToAdd.addAll(group.getMembers());
            Iterator<Player> pIter = group.getMembers().iterator();
            while (pIter.hasNext()) {
                PlayerGroupService.removePlayer(pIter.next());
            }
        } else {
            playersToAdd.add(invited);
        }
    }
	
    @Override
    public void denyRequest(Creature requester, Player responder) {
        //%0 has declined your invitation to join the alliance.
		PacketSendUtility.sendPacket(inviter, S_MESSAGE_CODE.STR_PARTY_ALLIANCE_HE_REJECT_INVITATION(responder.getName()));
    }
}
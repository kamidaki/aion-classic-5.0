package com.aionemu.gameserver.model.team.alliance.events;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.team.alliance.PlayerAlliance;
import com.aionemu.gameserver.model.team.common.events.AbstractTeamPlayerEvent;
import com.aionemu.gameserver.network.aion.serverpackets.S_ALLIANCE_INFO;
import com.aionemu.gameserver.network.aion.serverpackets.S_MESSAGE_CODE;
import com.aionemu.gameserver.utils.PacketSendUtility;

public class AssignViceCaptainEvent extends AbstractTeamPlayerEvent<PlayerAlliance>
{
    public static enum AssignType {
        PROMOTE,
        DEMOTE_CAPTAIN_TO_VICECAPTAIN,
        DEMOTE
    }
	
    private final AssignType assignType;
	
    public AssignViceCaptainEvent(PlayerAlliance team, Player eventPlayer, AssignType assignType) {
        super(team, eventPlayer);
        this.assignType = assignType;
    }
	
    @Override
    public boolean checkCondition() {
        return eventPlayer != null && eventPlayer.isOnline();
    }
	
    @Override
    public void handleEvent() {
        switch (assignType) {
            case DEMOTE:
                team.getViceCaptainIds().remove(eventPlayer.getObjectId());
            break;
            case PROMOTE:
                if (team.getViceCaptainIds().size() == 4) {
                    PacketSendUtility.sendPacket(team.getLeaderObject(), S_MESSAGE_CODE.STR_FORCE_CANNOT_PROMOTE_MANAGER);
                    return;
                }
                team.getViceCaptainIds().add(eventPlayer.getObjectId());
            break;
            case DEMOTE_CAPTAIN_TO_VICECAPTAIN:
                team.getViceCaptainIds().add(eventPlayer.getObjectId());
            break;
        }
        team.applyOnMembers(this);
    }
	
    @Override
    public boolean apply(Player player) {
        int messageId = 0;
        switch (assignType) {
            case PROMOTE:
                messageId = S_ALLIANCE_INFO.VICECAPTAIN_PROMOTE;
            break;
            case DEMOTE:
                messageId = S_ALLIANCE_INFO.VICECAPTAIN_PROMOTE;
            break;
        }
        PacketSendUtility.sendPacket(player, new S_ALLIANCE_INFO(team, messageId, eventPlayer.getName()));
        return true;
    }
}
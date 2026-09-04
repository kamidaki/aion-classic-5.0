package com.aionemu.gameserver.model.team.alliance.events;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.team.alliance.PlayerAlliance;
import com.aionemu.gameserver.model.team.alliance.PlayerAllianceMember;
import com.aionemu.gameserver.model.team.alliance.PlayerAllianceService;
import com.aionemu.gameserver.model.team.common.events.PlayerLeavedEvent;
import com.aionemu.gameserver.model.team.common.legacy.PlayerAllianceEvent;
import com.aionemu.gameserver.network.aion.serverpackets.S_ALLIANCE_INFO;
import com.aionemu.gameserver.network.aion.serverpackets.S_ALLIANCE_MEMBER_INFO;
import com.aionemu.gameserver.network.aion.serverpackets.S_GROUP_INFO;
import com.aionemu.gameserver.network.aion.serverpackets.S_MESSAGE_CODE;
import com.aionemu.gameserver.services.instance.InstanceService;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.ThreadPoolManager;
import com.aionemu.gameserver.world.WorldMapInstance;


public class PlayerAllianceLeavedEvent extends PlayerLeavedEvent<PlayerAllianceMember, PlayerAlliance> {

    public PlayerAllianceLeavedEvent(PlayerAlliance alliance, Player player) {
        super(alliance, player);
    }

    public PlayerAllianceLeavedEvent(PlayerAlliance team, Player player, PlayerLeavedEvent.LeaveReson reason,
                                     String banPersonName) {
        super(team, player, reason, banPersonName);
    }

    public PlayerAllianceLeavedEvent(PlayerAlliance alliance, Player player, PlayerLeavedEvent.LeaveReson reason) {
        super(alliance, player, reason);
    }

    @Override
    public void handleEvent() {
        team.removeMember(leavedPlayer.getObjectId());
        team.getViceCaptainIds().remove(leavedPlayer.getObjectId());

        if (leavedPlayer.isOnline()) {
            PacketSendUtility.sendPacket(leavedPlayer, new S_GROUP_INFO());
        }

        team.apply(this);

        switch (reason) {
            case BAN:
            case LEAVE:
            case LEAVE_TIMEOUT:
                if (team.onlineMembers() <= 1) {
                    PlayerAllianceService.disband(team);
                } else {
                    if (leavedPlayer.equals(team.getLeader().getObject())) {
                        team.onEvent(new ChangeAllianceLeaderEvent(team));
                    }
                }
                if (reason == LeaveReson.BAN) {
                    PacketSendUtility.sendPacket(leavedPlayer, S_MESSAGE_CODE.STR_FORCE_BAN_ME(banPersonName));
                }

                break;
            case DISBAND:
                PacketSendUtility.sendPacket(leavedPlayer, S_MESSAGE_CODE.STR_PARTY_ALLIANCE_DISPERSED);
                break;
        }

        if (leavedPlayer.isInInstance()) {
            ThreadPoolManager.getInstance().schedule(new Runnable() {
                @Override
                public void run() {
                    if (!leavedPlayer.isInAlliance()) {
                        WorldMapInstance instance = leavedPlayer.getPosition().getWorldMapInstance();
                        if (instance.getRegistredAlliance() != null || instance.getRegistredLeague() != null) {
                            InstanceService.moveToExitPoint(leavedPlayer);
                        }
                    }
                }
            }, 10000);
        }
    }

    @Override
    public boolean apply(PlayerAllianceMember member) {
        Player player = member.getObject();

        PacketSendUtility.sendPacket(player, new S_ALLIANCE_MEMBER_INFO(leavedTeamMember, PlayerAllianceEvent.LEAVE));
        PacketSendUtility.sendPacket(player, new S_ALLIANCE_INFO(team));

        switch (reason) {
            case LEAVE_TIMEOUT:
                PacketSendUtility.sendPacket(player,
                        S_MESSAGE_CODE.STR_PARTY_ALLIANCE_HE_LEAVED_PARTY(leavedPlayer.getName()));
                break;
            case LEAVE:
                PacketSendUtility.sendPacket(player,
                        S_MESSAGE_CODE.STR_PARTY_ALLIANCE_HE_LEAVED_PARTY(leavedPlayer.getName()));
                break;
            case DISBAND:
                PacketSendUtility.sendPacket(player, S_MESSAGE_CODE.STR_PARTY_ALLIANCE_DISPERSED);
                break;
            case BAN:
                PacketSendUtility
                        .sendPacket(player, S_MESSAGE_CODE.STR_FORCE_BAN_HIM(banPersonName, leavedPlayer.getName()));
                break;
        }

        return true;
    }
}

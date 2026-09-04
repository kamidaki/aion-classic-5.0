package com.aionemu.gameserver.model.team.group.events;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.team.common.events.PlayerLeavedEvent;
import com.aionemu.gameserver.model.team.common.legacy.GroupEvent;
import com.aionemu.gameserver.model.team.group.PlayerGroup;
import com.aionemu.gameserver.model.team.group.PlayerGroupMember;
import com.aionemu.gameserver.model.team.group.PlayerGroupService;
import com.aionemu.gameserver.network.aion.serverpackets.S_PARTY_MEMBER_INFO;
import com.aionemu.gameserver.network.aion.serverpackets.S_GROUP_INFO;
import com.aionemu.gameserver.network.aion.serverpackets.S_MESSAGE_CODE;
import com.aionemu.gameserver.services.instance.InstanceService;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.ThreadPoolManager;


public class PlayerGroupLeavedEvent extends PlayerLeavedEvent<PlayerGroupMember, PlayerGroup> {

    public PlayerGroupLeavedEvent(PlayerGroup alliance, Player player) {
        super(alliance, player);
    }

    public PlayerGroupLeavedEvent(PlayerGroup team, Player player, PlayerLeavedEvent.LeaveReson reason,
                                  String banPersonName) {
        super(team, player, reason, banPersonName);
    }

    public PlayerGroupLeavedEvent(PlayerGroup alliance, Player player, PlayerLeavedEvent.LeaveReson reason) {
        super(alliance, player, reason);
    }

    @Override
    public void handleEvent() {
        team.removeMember(leavedPlayer.getObjectId());

        if (leavedPlayer.isMentor()) {
            team.onEvent(new PlayerGroupStopMentoringEvent(team, leavedPlayer));
        }

        team.apply(this);

        PacketSendUtility.sendPacket(leavedPlayer, new S_GROUP_INFO());
        switch (reason) {
            case BAN:
            case LEAVE:
                // PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_PARTY_SECEDE); // client side?
                if (team.onlineMembers() <= 1) {
                    PlayerGroupService.disband(team);
                } else {
                    if (leavedPlayer.equals(team.getLeader().getObject())) {
                        team.onEvent(new ChangeGroupLeaderEvent(team));
                    }
                }
                if (reason == LeaveReson.BAN) {
                    PacketSendUtility.sendPacket(leavedPlayer, S_MESSAGE_CODE.STR_PARTY_YOU_ARE_BANISHED);
                }
                break;
            case DISBAND:
                PacketSendUtility.sendPacket(leavedPlayer, S_MESSAGE_CODE.STR_PARTY_IS_DISPERSED);
                break;
        }

        if (leavedPlayer.isInInstance()) {
            ThreadPoolManager.getInstance().schedule(new Runnable() {
                @Override
                public void run() {
                    if (!leavedPlayer.isInGroup()) {
                        if (leavedPlayer.getPosition().getWorldMapInstance().getRegisteredGroup() != null) {
                            InstanceService.moveToExitPoint(leavedPlayer);
                        }
                    }
                }
            }, 10000);
        }
    }

    @Override
    public boolean apply(PlayerGroupMember member) {
        Player player = member.getObject();
        PacketSendUtility.sendPacket(player, new S_PARTY_MEMBER_INFO(team, leavedPlayer, GroupEvent.LEAVE));

        switch (reason) {
            case LEAVE:
            case DISBAND:
                PacketSendUtility.sendPacket(player, S_MESSAGE_CODE.STR_PARTY_HE_LEAVE_PARTY(leavedPlayer.getName()));
                break;
            case BAN:
                // TODO find out empty strings (Retail has +2 empty strings
                PacketSendUtility.sendPacket(player, S_MESSAGE_CODE.STR_PARTY_HE_IS_BANISHED(leavedPlayer.getName()));
                break;
        }

        return true;
    }
}

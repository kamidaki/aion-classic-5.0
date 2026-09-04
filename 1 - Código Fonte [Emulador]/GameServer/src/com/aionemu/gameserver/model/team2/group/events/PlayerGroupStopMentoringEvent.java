package com.aionemu.gameserver.model.team2.group.events;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.team2.common.events.PlayerStopMentoringEvent;
import com.aionemu.gameserver.model.team2.common.legacy.GroupEvent;
import com.aionemu.gameserver.model.team2.group.PlayerGroup;
import com.aionemu.gameserver.network.aion.serverpackets.S_PARTY_MEMBER_INFO;
import com.aionemu.gameserver.utils.PacketSendUtility;


public class PlayerGroupStopMentoringEvent extends PlayerStopMentoringEvent<PlayerGroup> {

    /**
     * @param group
     * @param player
     */
    public PlayerGroupStopMentoringEvent(PlayerGroup group, Player player) {
        super(group, player);
    }

    @Override
    protected void sendGroupPacketOnMentorEnd(Player member) {
        PacketSendUtility.sendPacket(member, new S_PARTY_MEMBER_INFO(team, player, GroupEvent.MOVEMENT));
    }
}

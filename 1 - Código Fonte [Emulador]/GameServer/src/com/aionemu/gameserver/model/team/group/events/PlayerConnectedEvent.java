package com.aionemu.gameserver.model.team.group.events;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.team.common.events.AlwaysTrueTeamEvent;
import com.aionemu.gameserver.model.team.common.legacy.GroupEvent;
import com.aionemu.gameserver.model.team.group.PlayerGroup;
import com.aionemu.gameserver.model.team.group.PlayerGroupMember;
import com.aionemu.gameserver.network.aion.serverpackets.S_PARTY_INFO;
import com.aionemu.gameserver.network.aion.serverpackets.S_PARTY_MEMBER_INFO;
import com.aionemu.gameserver.network.aion.serverpackets.S_INSTANCE_DUNGEON_COOLTIMES;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.google.common.base.Predicate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;


public class PlayerConnectedEvent extends AlwaysTrueTeamEvent implements Predicate<Player> {

    private static final Logger log = LoggerFactory.getLogger(PlayerConnectedEvent.class);
    private final PlayerGroup group;
    private final Player player;

    public PlayerConnectedEvent(PlayerGroup group, Player player) {
        this.group = group;
        this.player = player;
    }

    @Override
    public void handleEvent() {
        group.removeMember(player.getObjectId());
        group.addMember(new PlayerGroupMember(player));
        // TODO this probably should never happen
        if (player.sameObjectId(group.getLeader().getObjectId())) {
            log.warn("[TEAM2] leader connected {}", group.size());
            group.changeLeader(new PlayerGroupMember(player));
        }
        PacketSendUtility.sendPacket(player, new S_PARTY_INFO(group));
        PacketSendUtility.sendPacket(player, new S_PARTY_MEMBER_INFO(group, player, GroupEvent.JOIN));
        group.applyOnMembers(this);
    }

    @Override
    public boolean apply(Player member) {
        if (!player.equals(member)) {
            PacketSendUtility.sendPacket(member, new S_PARTY_MEMBER_INFO(group, player, GroupEvent.ENTER));
            PacketSendUtility.sendPacket(member, new S_INSTANCE_DUNGEON_COOLTIMES(player, false, group));
            PacketSendUtility.sendPacket(player, new S_PARTY_MEMBER_INFO(group, member, GroupEvent.ENTER));
        }
        return true;
    }
}

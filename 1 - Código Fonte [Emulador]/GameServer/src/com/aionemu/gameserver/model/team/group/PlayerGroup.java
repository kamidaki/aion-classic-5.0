package com.aionemu.gameserver.model.team.group;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.team.TeamType;
import com.aionemu.gameserver.model.team.TemporaryPlayerTeam;
import com.aionemu.gameserver.utils.idfactory.IDFactory;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import java.util.Collection;

public class PlayerGroup extends TemporaryPlayerTeam<PlayerGroupMember>
{
    private TeamType type;
	private int bgIndex = -1;
	private int killCount = 0;
	private int buffId = 0;
    private final PlayerGroupStats playerGroupStats;
    private Map<Integer, Player> groupMembers = new ConcurrentHashMap<Integer, Player>();
	
    public PlayerGroup(PlayerGroupMember leader, TeamType type) {
        super(IDFactory.getInstance().nextId());
        this.playerGroupStats = new PlayerGroupStats(this);
        this.type = type;
        initializeTeam(leader);
    }

    @Override
    public void addMember(PlayerGroupMember member) {
        super.addMember(member);
        playerGroupStats.onAddPlayer(member);
        member.getObject().setPlayerGroup(this);
    }

    @Override
    public void removeMember(PlayerGroupMember member) {
        super.removeMember(member);
        playerGroupStats.onRemovePlayer(member);
        member.getObject().setPlayerGroup(null);
    }

    @Override
    public boolean isFull() {
        return size() == 6;
    }

    @Override
    public int getMinExpPlayerLevel() {
        return playerGroupStats.getMinExpPlayerLevel();
    }

    @Override
    public int getMaxExpPlayerLevel() {
        return playerGroupStats.getMaxExpPlayerLevel();
    }

    public TeamType getTeamType() {
        return type;
    }

    public void setKillCount(int killCount) {
        this.killCount = killCount;
    }

    public int getKillCount() {
        return killCount;
    }

    public void setBgIndex(int bgIndex) {
        this.bgIndex = bgIndex;
    }

    public int getBgIndex() {
        return bgIndex;
    }

    public Collection<Integer> getMemberObjIds() {
        return groupMembers.keySet();
    }
	
    public int getGroupId() {
        return this.getObjectId();
    }

    public void setBuffId(int buffId) {
        this.buffId = buffId;
    }

    public int getBuffId() {
        return buffId;
    }
}
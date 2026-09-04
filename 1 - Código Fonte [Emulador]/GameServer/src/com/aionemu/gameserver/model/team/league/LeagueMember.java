package com.aionemu.gameserver.model.team.league;

import com.aionemu.gameserver.model.team.TeamMember;
import com.aionemu.gameserver.model.team.alliance.PlayerAlliance;


public class LeagueMember implements TeamMember<PlayerAlliance>
{
    private final PlayerAlliance alliance;
    private int leaguePosition;
	
    public LeagueMember(PlayerAlliance alliance, int position) {
        this.alliance = alliance;
        this.leaguePosition = position;
    }
	
    @Override
    public Integer getObjectId() {
        return alliance.getObjectId();
    }
	
    @Override
    public String getName() {
        return alliance.getName();
    }
	
    @Override
    public PlayerAlliance getObject() {
        return alliance;
    }
	
    public final int getLeaguePosition() {
        return leaguePosition;
    }
}
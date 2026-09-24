package com.aionemu.gameserver.model.team.common.events;

import com.aionemu.gameserver.model.team.TeamEvent;

/**
 * @author Lost Academy Team & Durak
 */
public abstract class AlwaysTrueTeamEvent implements TeamEvent {

	@Override
	public final boolean checkCondition() {
		return true;
	}

}

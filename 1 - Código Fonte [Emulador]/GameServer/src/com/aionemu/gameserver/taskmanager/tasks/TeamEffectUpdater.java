package com.aionemu.gameserver.taskmanager.tasks;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.team.alliance.PlayerAllianceService;
import com.aionemu.gameserver.model.team.common.legacy.GroupEvent;
import com.aionemu.gameserver.model.team.common.legacy.PlayerAllianceEvent;
import com.aionemu.gameserver.model.team.group.PlayerGroupService;
import com.aionemu.gameserver.taskmanager.AbstractIterativePeriodicTaskManager;

public final class TeamEffectUpdater extends AbstractIterativePeriodicTaskManager<Player>
{
	private static final class SingletonHolder {
		private static final TeamEffectUpdater INSTANCE = new TeamEffectUpdater();
	}
	
	public static TeamEffectUpdater getInstance() {
		return SingletonHolder.INSTANCE;
	}
	
	public TeamEffectUpdater() {
		super(500);
	}
	
	@Override
	protected void callTask(Player player) {
		if (player.isOnline()) {
			if (player.isInGroup()) {
				PlayerGroupService.updateGroup(player, GroupEvent.UPDATE);
			} if (player.isInAlliance()) {
				PlayerAllianceService.updateAlliance(player, PlayerAllianceEvent.UPDATE);
			}
		}
		this.stopTask(player);
	}
	
	@Override
	protected String getCalledMethodName() {
		return "teamEffectUpdate()";
	}
}
package ai.worlds.eltnen;

import ai.AggressiveNpcAI;

import com.aionemu.commons.network.util.ThreadPoolManager;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.ai.AIActions;
import com.aionemu.gameserver.skillengine.SkillEngine;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("Explosive_Device_Of_Yuditio")
public class Explosive_Device_Of_YuditioAI extends AggressiveNpcAI
{
	@Override
	public void think() {
	}
	
	@Override
	protected void handleSpawned() {
		super.handleSpawned();
		SkillEngine.getInstance().getSkill(getOwner(), 1857, 60, getTarget()).useNoAnimationSkill(); //Aether Explosion.
		ThreadPoolManager.getInstance().schedule(new Runnable() {
			@Override
			public void run() {
				AIActions.deleteOwner(Explosive_Device_Of_YuditioAI.this);
			}
		}, 6000);
	}
	
	@Override
	public boolean isMoveSupported() {
		return false;
	}
	
	@Override
	protected void handleDied() {
		super.handleDied();
		AIActions.deleteOwner(this);
	}
}
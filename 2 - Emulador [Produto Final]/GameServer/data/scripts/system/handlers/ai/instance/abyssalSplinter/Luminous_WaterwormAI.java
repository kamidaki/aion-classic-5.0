package ai.instance.abyssalSplinter;

import com.aionemu.gameserver.ai2.AIName;
import com.aionemu.gameserver.ai2.NpcAI;
import com.aionemu.gameserver.model.actions.NpcActions;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.skillengine.SkillEngine;
import com.aionemu.gameserver.utils.ThreadPoolManager;

import java.util.concurrent.Future;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("Luminous_Waterworm")
public class Luminous_WaterwormAI extends NpcAI
{
	private Npc pazuzu;
	private Future<?> replenishmentTask;
	
	@Override
	public void think() {
	}
	
	@Override
	protected void handleSpawned() {
		super.handleSpawned();
		pazuzu = getPosition().getWorldMapInstance().getNpc(216951);
		replenishment();
	}
	
	private void replenishment() {
		replenishmentTask = ThreadPoolManager.getInstance().scheduleAtFixedRate(new Runnable() {
			@Override
			public void run() {
				if (pazuzu != null && !NpcActions.isAlreadyDead(pazuzu)) {
					SkillEngine.getInstance().applyEffectDirectly(19291, getOwner(), pazuzu, 0); //Replenishment.
				}
			}
		}, 3000, 10000);
	}
	
	@Override
	protected void handleDespawned() {
		super.handleDespawned();
		replenishmentTask.cancel(true);
	}
	
    @Override
	public boolean isMoveSupported() {
		return false;
	}
}
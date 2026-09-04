package ai.instance.arena;

import com.aionemu.commons.network.util.ThreadPoolManager;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.ai.NpcAI;
import com.aionemu.gameserver.ai.AIActions;
import com.aionemu.gameserver.ai.poll.*;

import java.util.concurrent.Future;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("Crater")
public class CraterAI extends NpcAI
{
	private Future<?> craterExplosionTask;
	
	@Override
	public void think() {
	}
	
	@Override
	protected void handleSpawned() {
		super.handleSpawned();
		craterExplosion();
	}
	
	private void craterExplosion() {
		craterExplosionTask = ThreadPoolManager.getInstance().scheduleAtFixedRate(new Runnable() {
			@Override
			public void run() {
				AIActions.useSkill(CraterAI.this, 20069); //Crater Explosion.
			}
		}, 3000, 10000);
	}
	
	@Override
	protected void handleDespawned() {
		super.handleDespawned();
		craterExplosionTask.cancel(true);
	}
	
	@Override
    public AIAnswer ask(AIQuestion question) {
        switch (question) {
            case CAN_ATTACK_PLAYER:
                return AIAnswers.POSITIVE;
            default:
                return AIAnswers.NEGATIVE;
        }
    }
	
    @Override
	public boolean isMoveSupported() {
		return false;
	}
}
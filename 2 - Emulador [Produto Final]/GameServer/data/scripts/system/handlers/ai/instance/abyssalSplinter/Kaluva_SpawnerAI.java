package ai.instance.abyssalSplinter;

import com.aionemu.commons.utils.Rnd;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.ai.NpcAI;
import com.aionemu.gameserver.utils.ThreadPoolManager;

import java.util.concurrent.Future;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("Kaluva_Spawner")
public class Kaluva_SpawnerAI extends NpcAI
{
	private Future<?> kaluvaSpawnerTask;
	
	@Override
	public void think() {
	}
	
	private void kaluvaSpawner() {
		kaluvaSpawnerTask = ThreadPoolManager.getInstance().scheduleAtFixedRate(new Runnable() {
			@Override
			public void run() {
				switch (Rnd.get(1, 2)) {
					case 1:
					    getOwner().getController().onDelete();
						spawn(281911, getOwner().getX(), getOwner().getY(), getOwner().getZ(), (byte) getOwner().getHeading());
					break;
					case 2:
					    getOwner().getController().onDelete();
					    spawn(281912, getOwner().getX(), getOwner().getY(), getOwner().getZ(), (byte) getOwner().getHeading());
					break;
				}
			}
		}, 30000, 120000);
	}
	
	@Override
	protected void handleSpawned() {
		super.handleSpawned();
		kaluvaSpawner();
	}
	
	@Override
	protected void handleDespawned() {
		super.handleDespawned();
		kaluvaSpawnerTask.cancel(true);
		getOwner().getEffectController().removeAllEffects();
	}
	
	@Override
	protected void handleDied() {
		super.handleDied();
		kaluvaSpawnerTask.cancel(true);
		getOwner().getController().onDelete();
		getOwner().getEffectController().removeAllEffects();
	}
	
	@Override
	public boolean isMoveSupported() {
		return false;
	}
}
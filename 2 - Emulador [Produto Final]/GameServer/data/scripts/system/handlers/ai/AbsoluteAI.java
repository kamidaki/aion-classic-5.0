package ai;

import com.aionemu.commons.network.util.ThreadPoolManager;

import com.aionemu.gameserver.ai.AIName;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("Absolute")
public class AbsoluteAI extends GeneralNpcAI
{
	@Override
	protected void handleSpawned() {
		super.handleSpawned();
		despawn();
	}
	
	private void despawn() {
		ThreadPoolManager.getInstance().schedule(new Runnable() {
			@Override
			public void run() {
				getOwner().getController().onDelete();
			}
		}, 120000);
	}
	
	@Override
	public boolean isMoveSupported() {
		return false;
	}
}
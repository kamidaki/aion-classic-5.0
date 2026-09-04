package ai.worlds.heiron.exedil;

import com.aionemu.commons.network.util.ThreadPoolManager;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.ai.NpcAI;
import com.aionemu.gameserver.ai.AIActions;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("Power_Of_Exedil")
public class Power_Of_ExedilAI extends NpcAI
{
	@Override
	public void think() {
	}
	
	@Override
	protected void handleSpawned() {
		super.handleSpawned();
		despawn();
		AIActions.targetCreature(Power_Of_ExedilAI.this, getPosition().getWorldMapInstance().getNpc(212317)); //Exedil.
		AIActions.useSkill(Power_Of_ExedilAI.this, 17125);
	}
	
    private void despawn() {
  	    ThreadPoolManager.getInstance().schedule(new Runnable() {
  		    @Override
  		    public void run() {
  			    getOwner().getController().onDelete();
  		    }
  	    }, 15000);
    }
	
    @Override
	public boolean isMoveSupported() {
		return false;
	}
}
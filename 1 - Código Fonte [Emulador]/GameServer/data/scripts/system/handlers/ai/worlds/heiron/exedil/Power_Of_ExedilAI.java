package ai.worlds.heiron.exedil;

import com.aionemu.commons.network.util.ThreadPoolManager;

import com.aionemu.gameserver.ai2.AIName;
import com.aionemu.gameserver.ai2.NpcAI;
import com.aionemu.gameserver.ai2.AI2Actions;

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
		AI2Actions.targetCreature(Power_Of_ExedilAI.this, getPosition().getWorldMapInstance().getNpc(212317)); //Exedil.
		AI2Actions.useSkill(Power_Of_ExedilAI.this, 17125);
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
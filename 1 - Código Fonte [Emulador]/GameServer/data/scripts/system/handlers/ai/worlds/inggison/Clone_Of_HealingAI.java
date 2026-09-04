package ai.worlds.inggison;

import com.aionemu.gameserver.ai2.AIName;
import com.aionemu.gameserver.ai2.NpcAI;
import com.aionemu.gameserver.ai2.AI2Actions;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("Clone_Of_Healing")
public class Clone_Of_HealingAI extends NpcAI
{
	@Override
	public void think() {
	}
	
	@Override
	protected void handleSpawned() {
		super.handleSpawned();
		AI2Actions.targetCreature(Clone_Of_HealingAI.this, getPosition().getWorldMapInstance().getNpc(216516)); //Omega.
		AI2Actions.useSkill(Clone_Of_HealingAI.this, 18685);
	}
}
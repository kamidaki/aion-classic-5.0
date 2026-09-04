package ai.worlds.inggison;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.ai.NpcAI;
import com.aionemu.gameserver.ai.AIActions;

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
		AIActions.targetCreature(Clone_Of_HealingAI.this, getPosition().getWorldMapInstance().getNpc(216516)); //Omega.
		AIActions.useSkill(Clone_Of_HealingAI.this, 18685);
	}
}
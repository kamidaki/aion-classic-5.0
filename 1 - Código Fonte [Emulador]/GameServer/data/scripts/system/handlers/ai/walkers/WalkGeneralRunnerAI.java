package ai.walkers;

import com.aionemu.gameserver.model.gameobjects.Npc;

import ai.GeneralNpcAI;
import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.model.gameobjects.state.CreatureState;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("general_runner")
public class WalkGeneralRunnerAI extends GeneralNpcAI
{
	public WalkGeneralRunnerAI() {
		super();
	}

	public WalkGeneralRunnerAI(Npc owner) {
		super(owner);
	}

	@Override
	protected void handleMoveArrived() {
		super.handleMoveArrived();
		getOwner().setState(CreatureState.WEAPON_EQUIPPED);
	}
}
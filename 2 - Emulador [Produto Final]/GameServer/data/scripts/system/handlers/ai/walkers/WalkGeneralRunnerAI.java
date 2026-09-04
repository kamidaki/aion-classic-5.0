package ai.walkers;

import ai.GeneralNpcAI;
import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.model.gameobjects.state.CreatureState;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("general_runner")
public class WalkGeneralRunnerAI extends GeneralNpcAI
{
	@Override
	protected void handleMoveArrived() {
		super.handleMoveArrived();
		getOwner().setState(CreatureState.WEAPON_EQUIPPED);
	}
}
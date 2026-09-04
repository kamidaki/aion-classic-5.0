package ai.walkers;

import ai.AggressiveNpcAI;
import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.model.gameobjects.state.CreatureState;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("aggro_runner")
public class WalkAggroRunnerAI extends AggressiveNpcAI
{
	@Override
	protected void handleMoveArrived() {
		super.handleMoveArrived();
		getOwner().setState(CreatureState.WEAPON_EQUIPPED);
	}
}
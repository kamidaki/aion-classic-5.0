package ai.instance.steelRake;

import ai.AggressiveNpcAI;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.ai.AIActions;
import com.aionemu.gameserver.ai.poll.*;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.utils.ThreadPoolManager;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("Koakoa_Bomb")
public class Koakoa_BombAI extends AggressiveNpcAI
{
	@Override
	protected void handleCreatureAggro(Creature creature) {
		AIActions.useSkill(this, 18551); //Explosion.
		ThreadPoolManager.getInstance().schedule(new Runnable() {
			@Override
			public void run() {
				getOwner().getController().onDelete();
			}
		}, 15500);
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
}
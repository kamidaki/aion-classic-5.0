package ai.instance.admaStronghold;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.ai.NpcAI;
import com.aionemu.gameserver.ai.AIActions;
import com.aionemu.gameserver.ai.poll.*;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.utils.MathUtil;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("Acid_Cloud")
public class Acid_CloudAI extends NpcAI
{
	@Override
	public void think() {
	}
	
	@Override
	protected void handleCreatureSee(Creature creature) {
		checkDistance(creature);
	}
	
	@Override
	protected void handleCreatureMoved(Creature creature) {
		checkDistance(creature);
	}
	
	private void checkDistance(Creature creature) {
		int owner = getNpcId();
		int skill = 0;
		switch (owner) {
			case 281458:
				skill = 20400;
			break;
		} if (creature instanceof Player) {
			if (getNpcId() == 281458 && MathUtil.isIn3dRangeLimited(getOwner(), creature, 1, 15)) {
				if (!creature.getEffectController().hasAbnormalEffect(skill)) {
					AIActions.useSkill(this, skill);
				}
			}
		}
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
	
	@Override
	public boolean isMoveSupported() {
		return false;
	}
}
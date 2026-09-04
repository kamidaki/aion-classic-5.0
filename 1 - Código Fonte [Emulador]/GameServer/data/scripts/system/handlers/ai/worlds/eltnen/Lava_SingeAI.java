package ai.worlds.eltnen;

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

@AIName("Lava_Singe")
public class Lava_SingeAI extends NpcAI
{
	@Override
	public void think() {
	}
	
	@Override
	protected void handleCreatureSee(Creature creature) {
		checkDistance(this, creature);
	}
	
	@Override
	protected void handleCreatureMoved(Creature creature) {
		checkDistance(this, creature);
	}
	
	private void checkDistance(NpcAI ai, Creature creature) {
		int owner = getNpcId();
		int skill = 0;
		switch (owner) {
			case 206212:
				skill = 8269;
			break;
		} if (creature instanceof Player) {
			if (getNpcId() == 206212 && MathUtil.isIn3dRangeLimited(getOwner(), creature, 1, 8)) {
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
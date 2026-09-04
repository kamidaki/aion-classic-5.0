package ai.instance.empyreanCrucible;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.ai.NpcAI;
import com.aionemu.gameserver.ai.AIActions;
import com.aionemu.gameserver.ai.poll.*;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.utils.MathUtil;
import com.aionemu.gameserver.world.WorldMapInstance;

import java.util.*;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("Spark_Of_Darkness")
public class Spark_Of_DarknessAI extends NpcAI
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
			case 282373:
				skill = 19554;
			break;
		} if (creature instanceof Player) {
			if (getNpcId() == 282373 && MathUtil.isIn3dRangeLimited(getOwner(), creature, 1, 15)) {
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
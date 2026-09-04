package ai;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.ai.AttackIntention;
import com.aionemu.gameserver.ai.manager.AttackManager;
import com.aionemu.gameserver.ai.poll.AIAnswer;
import com.aionemu.gameserver.ai.poll.AIAnswers;
import com.aionemu.gameserver.ai.poll.AIQuestion;
import com.aionemu.gameserver.model.gameobjects.Homing;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("homing")
public class HomingNpcAI extends GeneralNpcAI
{
	@Override
	public void think() {
	}
	
	@Override
	public AttackIntention chooseAttackIntention() {
		return AttackIntention.SIMPLE_ATTACK;
	}
	
	@Override
	protected void handleAttackComplete() {
		super.handleAttackComplete();
		Homing owner = (Homing) getOwner();
		if (owner.getActiveSkillId() != 0) {
			AttackManager.scheduleNextAttack(this);
		}
	}
	
	@Override
	protected AIAnswer pollInstance(AIQuestion question) {
		switch (question) {
			case SHOULD_DECAY:
				return AIAnswers.NEGATIVE;
			case SHOULD_RESPAWN:
				return AIAnswers.NEGATIVE;
			case SHOULD_REWARD:
				return AIAnswers.NEGATIVE;
			default:
				return null;
		}
	}
}
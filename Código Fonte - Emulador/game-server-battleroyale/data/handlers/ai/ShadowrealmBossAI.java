package ai;

import java.util.concurrent.atomic.AtomicBoolean;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.ai.AIState;
import com.aionemu.gameserver.ai.manager.AttackManager;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.utils.ThreadPoolManager;

/** Boss estacionario do Land of Shadows: conserva o agro e a rotacao mesmo fora do alcance basico. */
@AIName("shadowrealm_boss")
public class ShadowrealmBossAI extends AggressiveNpcAI {

	private final AtomicBoolean retryScheduled = new AtomicBoolean();

	public ShadowrealmBossAI(Npc owner) {
		super(owner);
	}

	@Override
	protected void handleCreatureNotSee(Creature creature) {
		if (creature.equals(getTarget()) && keepTarget(creature)) {
			getOwner().getController().abortCast();
			scheduleRetry();
			return;
		}
		super.handleCreatureNotSee(creature);
	}

	@Override
	protected void handleTargetTooFar() {
		if (getTarget() instanceof Creature target && keepTarget(target)) {
			scheduleRetry();
			return;
		}
		super.handleTargetTooFar();
	}

	@Override
	protected void handleTargetGiveup() {
		if (getTarget() instanceof Creature target && keepTarget(target)) {
			scheduleRetry();
			return;
		}
		super.handleTargetGiveup();
	}

	private boolean keepTarget(Creature target) {
		return isInState(AIState.FIGHT) && !target.isDead() && !target.getLifeStats().isAboutToDie()
			&& getAggroList().isHating(target);
	}

	private void scheduleRetry() {
		getOwner().getMoveController().abortMove();
		if (!retryScheduled.compareAndSet(false, true))
			return;
		ThreadPoolManager.getInstance().schedule(() -> {
			retryScheduled.set(false);
			if (!getOwner().isDead() && isInState(AIState.FIGHT) && getTarget() instanceof Creature target && keepTarget(target))
				AttackManager.scheduleNextAttack(this);
		}, 750);
	}
}

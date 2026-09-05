package ai.siege;

import com.aionemu.gameserver.model.gameobjects.Npc;

import ai.AggressiveNpcAI;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.ai.AIState;
import com.aionemu.gameserver.ai.AIActions;
import com.aionemu.gameserver.ai.poll.*;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.utils.*;

/****/
/** Author Rinzler (Encom)
/****/

@AIName("siege_mine")
public class MineAI extends AggressiveNpcAI
{
	public MineAI() {
		super();
	}

	public MineAI(Npc owner) {
		super(owner);
	}

	@Override
	protected void handleCreatureAggro(Creature creature) {
		tryActivateMine(creature);
	}
	
	private void tryActivateMine(Creature creature) {
		if (!creature.getLifeStats().isAlreadyDead() && MathUtil.isIn3dRangeLimited(getOwner(), creature, 1, 20)) {
			explode(creature);
		}
	}
	
	private void explode(Creature creature) {
		if (setStateIfNot(AIState.FIGHT)) {
			AIActions.useSkill(this, 17790);
			AIActions.targetCreature(MineAI.this, creature);
		}
	}
	
	@Override
	protected AIAnswer pollInstance(AIQuestion question) {
		switch (question) {
			case CAN_ATTACK_PLAYER:
                return AIAnswers.POSITIVE;
			default:
				return null;
		}
	}
	
	@Override
	public boolean isMoveSupported() {
		return false;
	}
}
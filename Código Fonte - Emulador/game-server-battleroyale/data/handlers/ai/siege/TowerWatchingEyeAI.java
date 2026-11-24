package ai.siege;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.ai.AttackIntention;
import com.aionemu.gameserver.ai.event.AIEventType;
import com.aionemu.gameserver.controllers.attack.AggroTarget;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.Npc;

/**
 * Watching Eye das torres de Tiamaranta Mesa (ai_name LDF4b_Tower_Boss no cliente). No oficial ele não ataca nem anda: só fica com o
 * aggro. O cliente não tem attack_range nem animação de golpe para o modelo, e as velocidades são 0. A conquista da torre na morte, o
 * "sem respawn" e o HP vêm do {@link BaseProtectorAI}.
 */
@AIName("ldf4b_tower_boss")
public class TowerWatchingEyeAI extends BaseProtectorAI {

	public TowerWatchingEyeAI(Npc owner) {
		super(owner);
	}

	@Override
	public boolean isMoveSupported() {
		return false;
	}

	@Override
	public AttackIntention chooseAttackIntention() {
		Creature mostHated = getAggroList().getTarget(AggroTarget.MOST_HATED);
		if (mostHated == null)
			return AttackIntention.FINISH_ATTACK;
		if (!mostHated.equals(getTarget()))
			onCreatureEvent(AIEventType.TARGET_CHANGED, mostHated);
		return AttackIntention.HOLD_AGGRO;
	}

	@Override
	protected void handleTargetTooFar() {
		// sem golpe não há "longe demais": o alvo segue o aggro (chooseAttackIntention), sem a desistência de 8 s de quem não alcança
	}
}

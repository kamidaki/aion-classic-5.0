package ai;

import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.ai.AIActions;
import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.skill.NpcSkillEntry;
import com.aionemu.gameserver.skillengine.SkillEngine;

/**
 * Aethers de Tiamaranta Mesa (ai do cliente LDF4b_Mine): 220977 Mutated Fallen Aether e 220978 Mutated Poison Aether.
 * <p>
 * 5.0 oficial (Tiamaranta.pcapng e 08_Spawns_Mapas/Tiamaranta_Mesa): não persegue nem ataca. Quando o jogador encosta, tudo no mesmo instante:
 * S_NPC_CHANGED_TARGET para si mesma, S_USE_SKILL em si mesma (21420 nível 4 / 21421 nível 2, área de 6 m), S_SKILL_SUCCEDED e S_REMOVE_OBJECT
 * com animação 1. A skill vem da lista de skills do NPC (npc_skills); o respawn é o do spawn.
 */
@AIName("ldf4b_mine")
public class LDF4bMineAI extends TouchTriggerNpcAI {

	public LDF4bMineAI(Npc owner) {
		super(owner);
	}

	@Override
	protected boolean canTrigger(Player player) {
		return getOwner().isEnemy(player);
	}

	@Override
	protected void onTouch(Player player) {
		Npc owner = getOwner();
		if (owner.getSkillList().getNpcSkills().isEmpty()) {
			LoggerFactory.getLogger(getClass()).warn("{} sem skill de explosão em npc_skills", owner);
			return;
		}
		NpcSkillEntry skill = owner.getSkillList().getNpcSkills().get(0);
		owner.getMoveController().abortMove();
		AIActions.targetSelf(this);
		SkillEngine.getInstance().getSkill(owner, skill.getSkillId(), skill.getSkillLevel(), owner).useSkill();
		owner.getController().deleteAndScheduleRespawn();
	}
}

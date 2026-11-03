package ai;

import java.util.Map;

import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.skill.NpcSkillEntry;
import com.aionemu.gameserver.skillengine.SkillEngine;
import com.aionemu.gameserver.spawnengine.SpawnEngine;

/**
 * Anéis de Tiamaranta Mesa (ai do cliente LDF4b_GetItem_Buff_NPC / LDF4b_GetItem_Hide_NPC / LDF4b_GetItem_FP_NPC).
 * <p>
 * 5.0 oficial (Tiamaranta.pcapng e 08_Spawns_Mapas/Tiamaranta_Mesa): o anel não lança nada. Quando o jogador passa por ele, tudo no mesmo
 * instante: S_PUT_NPC do NPC invisível LDF4b_GetItem_*_Skill_NPC (mesh NoShownPC, ai LDF4b_Buff_NPC) na posição do anel, S_NPC_CHANGED_TARGET
 * para o jogador, S_USE_SKILL no jogador (nível 1), S_SKILL_SUCCEDED, e S_REMOVE_OBJECT com animação 1 do auxiliar e do anel. A skill vem da
 * lista do auxiliar (npc_skills): 802439 → 21382 velocidade e voo, 802438 → 21381 Hide, 802440 → 21383 FP. O respawn do anel é o do spawn.
 */
@AIName("ldf4b_getitem_npc")
public class LDF4bGetItemNpcAI extends TouchTriggerNpcAI {

	// anel → auxiliar que lança a skill (client_npcs: LDF4b_GetItem_X_NPC → LDF4b_GetItem_X_Skill_NPC)
	private static final Map<Integer, Integer> SKILL_NPC = Map.of(802217, 802438, 802218, 802439, 802219, 802440);

	public LDF4bGetItemNpcAI(Npc owner) {
		super(owner);
	}

	@Override
	protected void onTouch(Player player) {
		Npc owner = getOwner();
		Integer skillNpcId = SKILL_NPC.get(owner.getNpcId());
		if (skillNpcId == null) {
			LoggerFactory.getLogger(getClass()).warn("{} sem NPC de skill associado", owner);
			return;
		}
		Npc skillNpc = (Npc) SpawnEngine.spawnObject(SpawnEngine.newSingleTimeSpawn(owner.getWorldId(), skillNpcId, owner.getX(), owner.getY(),
			owner.getZ(), owner.getHeading(), owner, null), owner.getInstanceId());
		try {
			if (skillNpc.getSkillList().getNpcSkills().isEmpty()) {
				LoggerFactory.getLogger(getClass()).warn("{} sem skill em npc_skills", skillNpc);
				return;
			}
			NpcSkillEntry skill = skillNpc.getSkillList().getNpcSkills().get(0);
			skillNpc.updateKnownlist();
			skillNpc.setTarget(player);
			SkillEngine.getInstance().getSkill(skillNpc, skill.getSkillId(), skill.getSkillLevel(), player).useSkill();
		} finally {
			skillNpc.getController().delete();
			owner.getController().deleteAndScheduleRespawn();
		}
	}
}

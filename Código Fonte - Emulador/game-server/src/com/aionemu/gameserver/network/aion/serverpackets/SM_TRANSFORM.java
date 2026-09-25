package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.TransformModel;
import com.aionemu.gameserver.model.templates.npc.NpcTemplate;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * [S_POLYMORPH] 0x3A, 39 bytes na 5.0 (27 de 27 nas capturas oficiais). O layout de 33 bytes que vinha antes nao tinha o D apos o
 * painel, a ultima flag nem a skill, e o cliente nao aplicava a transformacao.
 *
 * <pre>
 *  0 D objectId        4 D modelo (0 = invisivel; no fim, o template do personagem)
 *  8 H estado         10 F raio  14 F altura (jogador 0.25/2.0; NPC o mesmo par do S_PUT_NPC dele)
 * 18 C flag          19 D tipo (reserved8: None 0, PC 1, form1 3)
 * 23 C x5 flags      28 D painel (reserved4: 36/33/37 em TH/EL/BM_D_start)
 * 32 D 0             36 C flag
 * 37 H skill que transformou (10498 panda marinho, 10813 invisivel, 4340 TH_D_start); 0 no fim
 * </pre>
 *
 * As capturas provam a posicao das 7 flags e que valem 0 nos candies. Qual restricao e cada uma nao foi medido: a ordem e a do layout
 * antigo, e nenhum template usa as restricoes. O byte 36 veio 1 so nas formas com painel (TH/EL/BM_D_start, reserved15=1 no cliente).
 *
 * @author Lost Academy Team & Durak
 */
public class SM_TRANSFORM extends AionServerPacket {

	private final int objectId, modelId, state, type, panelId, skillId;
	private final float radius, height;
	private final boolean cantUseSkills, cantFly, cantUseItems, cantAttack, cantJump, cantRecall, cantMove;

	public SM_TRANSFORM(Creature creature) {
		this(creature, creature.getTransformModel(), creature.getObjectTemplate() instanceof NpcTemplate t ? t : null);
	}

	private SM_TRANSFORM(Creature creature, TransformModel tm, NpcTemplate npc) { // NPC e summon usam o par do SM_NPC_INFO
		this(creature.getObjectId(), tm.getModelId(), creature.getState(), npc == null ? 0.25f : npc.getBoundRadius().getMaxOfFrontAndSide(),
			npc == null ? 2.0f : npc.getHeight(), tm.getType().getId(), tm.getPanelId(), tm.getSkillId(), tm.cantUseSkills(), tm.cantFly(),
			tm.cantUseItems(), tm.cantAttack(), tm.cantJump(), tm.cantRecall(), tm.cantMove());
	}

	SM_TRANSFORM(int objectId, int modelId, int state, float radius, float height, int type, int panelId, int skillId, boolean cantUseSkills,
		boolean cantFly, boolean cantUseItems, boolean cantAttack, boolean cantJump, boolean cantRecall, boolean cantMove) {
		this.objectId = objectId;
		this.modelId = modelId;
		this.state = state;
		this.radius = radius;
		this.height = height;
		this.type = type;
		this.panelId = panelId;
		this.skillId = skillId;
		this.cantUseSkills = cantUseSkills;
		this.cantFly = cantFly;
		this.cantUseItems = cantUseItems;
		this.cantAttack = cantAttack;
		this.cantJump = cantJump;
		this.cantRecall = cantRecall;
		this.cantMove = cantMove;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(objectId);
		writeD(modelId);
		writeH(state);
		writeF(radius);
		writeF(height);
		writeC(cantUseSkills ? 1 : 0);
		writeD(type);
		writeC(cantFly ? 1 : 0);
		writeC(cantUseItems ? 1 : 0);
		writeC(cantAttack ? 1 : 0);
		writeC(cantJump ? 1 : 0);
		writeC(cantRecall ? 1 : 0);
		writeD(panelId); // display panel
		writeD(0);
		writeC(cantMove ? 1 : 0);
		writeH(skillId);
	}
}

package com.aionemu.gameserver.model.gameobjects;

import com.aionemu.gameserver.model.TribeClass;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.SM_CUSTOM_SETTINGS;
import com.aionemu.gameserver.network.aion.serverpackets.SM_TRANSFORM;
import com.aionemu.gameserver.services.RecallService;
import com.aionemu.gameserver.services.RecallService.CancelReason;
import com.aionemu.gameserver.skillengine.model.TransformType;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * @author Lost Academy Team & Durak
 */
public class TransformModel {

	private Creature owner;

	/**
	 * Transformacao ativa. Nao da para deduzir do modelId: o candy invisivel (reserved9 "0" no client_skills, ex. 10813
	 * Classic_Candy_SHAPE_INVISIBLE_EXCHANGE_50) transforma no modelo 0, e o S_POLYMORPH oficial manda exatamente 0.
	 */
	private boolean active;
	private int modelId;
	private int eventModelId;
	private TransformType originalType;
	private TransformType transformType;
	private int panelId;
	private int skillId;
	private TribeClass transformTribe;

	// restrictions
	protected boolean cantUseSkills;
	protected boolean cantMove;
	protected boolean cantRecall;
	protected boolean cantJump;
	protected boolean cantAttack;
	protected boolean cantUseItems;
	protected boolean cantFly;

	public TransformModel(Creature creature) {
		this.originalType = creature instanceof Player ? TransformType.PC : TransformType.NONE;
		this.transformType = TransformType.NONE;
		this.owner = creature;
	}

	/**
	 * Transformacao sem skill (//morph). 0 ou o proprio modelo desfaz.
	 */
	public void apply(int modelId) {
		if (modelId == 0)
			reset();
		else
			apply(modelId, originalType, 0, 0, false, false, false, false, false, false, false);
	}

	/**
	 * Function that activates transform. modelId 0 e o modelo invisivel, nao o fim da transformacao (ver {@link #reset()}).
	 */
	public void apply(int modelId, TransformType type, int panelId, int skillId, boolean cantUseSkills, boolean cantMove, boolean cantRecall, boolean cantJump, boolean cantAttack, boolean cantUseItems, boolean cantFly) {
		if (modelId == owner.getObjectTemplate().getTemplateId()) {
			reset();
			return;
		}
		this.active = true;
		this.modelId = modelId;
		this.transformType = type;
		this.panelId = panelId;
		this.skillId = skillId;
		this.cantUseSkills = cantUseSkills;
		this.cantMove = cantMove;
		this.cantRecall = cantRecall;
		this.cantJump = cantJump;
		this.cantAttack = cantAttack;
		this.cantUseItems = cantUseItems;
		this.cantFly = cantFly;
		this.updateVisually();
	}

	/**
	 * Volta ao modelo original. O S_POLYMORPH oficial do fim traz o template do personagem (100000-100003), tipo PC e skill 0.
	 */
	public void reset() {
		this.active = false;
		this.modelId = owner.getObjectTemplate().getTemplateId();
		this.transformType = originalType;
		this.panelId = 0;
		this.skillId = 0;
		this.cantUseSkills = false;
		this.cantMove = false;
		this.cantRecall = false;
		this.cantJump = false;
		this.cantAttack = false;
		this.cantUseItems = false;
		this.cantFly = false;
		this.updateVisually();
	}

	/**
	 * O oficial so manda o S_POLYMORPH depois do S_PUT_USER, e o modelo 0 so para os outros: nas capturas os 18 S_POLYMORPH com modelo 0
	 * eram sempre de outro jogador, nunca do dono da sessao. Mandar o modelo 0 para o proprio dono deixava o personagem sem modelo nenhum.
	 */
	public void updateVisually() {
		if (!owner.isSpawned()) // no login e no teleporte o modelo vai no proprio S_PUT_USER
			return;
		if (getModelId() == 0) // candy "SHAPE_INVISIBLE" (reserved9 "0"): so atributos, sem trocar a aparencia de quem usou
			PacketSendUtility.broadcastPacket(owner, new SM_TRANSFORM(owner));
		else
			PacketSendUtility.broadcastPacketAndReceive(owner, new SM_TRANSFORM(owner));
	}

	private void updateTribeVisually() {
		if (owner instanceof Npc) {
			Npc npc = (Npc) owner;
			npc.getKnownList().forEachPlayer(player -> {
				PacketSendUtility.sendPacket(player, new SM_CUSTOM_SETTINGS(npc.getObjectId(), 0, npc.getType(player).getId(), 0));
			});
		} else if (owner instanceof Player) {
			Player player = (Player) owner;
			player.getKnownList().forEachNpc(npc -> {
				PacketSendUtility.sendPacket(player, new SM_CUSTOM_SETTINGS(npc.getObjectId(), 0, npc.getType(player).getId(), 0));
			});
		}
	}

	/**
	 * @return the modelId
	 */
	public int getModelId() {
		if (eventModelId == owner.getObjectTemplate().getTemplateId() && transformType == TransformType.PC && isUnrestricted()) { // Player removed visual appearance via Nomorph command
			return eventModelId;
		}
		if (isActive())
			return modelId;
		if (eventModelId > 0)
			return eventModelId;
		else
			return owner.getObjectTemplate().getTemplateId();
	}

	public boolean isUnrestricted() {
		return !cantUseSkills && !cantMove && !cantRecall && !cantJump && !cantAttack && !cantUseItems && !cantFly;
	}

	/**
	 * use this functions for events, when you want players/npcs to have such model(skin) for the whole duration of the event, even after getting for
	 * example Feared, or after using candys etc. You need to set it on the start of the event and then unset with setEventModelId(0)
	 * 
	 * @param eventModelId
	 *          the eventModelId to set
	 */
	public void setEventModelId(int eventModelId) {
		this.eventModelId = eventModelId;
	}

	public int getEventModelId() {
		return this.eventModelId;
	}

	/**
	 * @return the type
	 */
	public TransformType getType() {
		return transformType;
	}

	/**
	 * @return the panelId
	 */
	public int getPanelId() {
		return panelId;
	}

	/**
	 * @return skill que transformou (vai no fim do S_POLYMORPH); 0 no //morph e no fim da transformacao
	 */
	public int getSkillId() {
		return skillId;
	}

	public boolean isActive() {
		return active;
	}

	/**
	 * @return true se a transformacao troca a aparencia; o candy "SHAPE_INVISIBLE" (modelo 0) so da atributos
	 */
	public boolean changesAppearance() {
		return active && modelId != 0;
	}

	/**
	 * Modelo que o S_PUT_USER nao consegue levar: la o D do modelo com 0 quer dizer "sem transformacao", entao o oficial manda o template e
	 * logo depois o S_POLYMORPH com o modelo 0 -- so para os outros jogadores (18 de 18 nas capturas), nunca para o dono.
	 */
	public boolean needsPolymorphOnSpawn() {
		return isActive() && getModelId() == 0;
	}

	/**
	 * @return the transformTribe
	 */
	public TribeClass getTribe() {
		return transformTribe;
	}

	/**
	 * @param transformTribe
	 *          the transformTribe to set
	 */
	public void setTribe(TribeClass transformTribe) {
		if (this.transformTribe == transformTribe)
			return;
		this.transformTribe = transformTribe;
		if (owner instanceof Player player)
			RecallService.getInstance().cancel(player, CancelReason.CANCELLED);
		this.updateTribeVisually();
	}

	public boolean cantUseSkills() {
		return cantUseSkills;
	}

	public boolean cantMove() {
		return cantMove;
	}

	public boolean cantRecall() {
		return cantRecall;
	}

	public boolean cantJump() {
		return cantJump;
	}

	public boolean cantAttack() {
		return cantAttack;
	}

	public boolean cantUseItems() {
		return cantUseItems;
	}

	public boolean cantFly() {
		return cantFly;
	}
}

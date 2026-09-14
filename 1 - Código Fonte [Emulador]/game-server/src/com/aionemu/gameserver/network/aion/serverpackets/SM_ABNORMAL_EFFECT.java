package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.Collection;
import java.util.stream.Collectors;

import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.skillengine.model.Effect;
import com.aionemu.gameserver.skillengine.model.SkillTargetSlot;

/**
 * S_ABNORMAL_STATUS_OTHER (0x32). 5.0 oficial: cabeçalho de 20 b e 23 b por efeito, o mesmo layout de efeito do 0x31, para NPC e para jogador.
 *
 * @author Lost Academy Team & Durak
 */
public class SM_ABNORMAL_EFFECT extends AionServerPacket {

	private final Creature effected;
	private final int effectType;
	private final int abnormals;
	private final Collection<Effect> filtered;
	private final int slots;
	private final Effect changed;

	public SM_ABNORMAL_EFFECT(Creature effected) {
		this(effected, effected.getEffectController().getAbnormals(), effected.getEffectController().getAbnormalEffects(), SkillTargetSlot.FULLSLOTS);
	}

	public SM_ABNORMAL_EFFECT(Creature effected, int abnormals, Collection<Effect> effects, int slots) {
		this(effected, abnormals, effects, slots, null);
	}

	/**
	 * @param changed
	 *          efeito que acabou de entrar, marcado como novo; null marca todos (atualização completa)
	 */
	public SM_ABNORMAL_EFFECT(Creature effected, int abnormals, Collection<Effect> effects, int slots, Effect changed) {
		this.effected = effected;
		this.abnormals = abnormals;
		this.filtered = slots == SkillTargetSlot.FULLSLOTS ? effects
			: effects.stream().filter(e -> (slots & e.getTargetSlot().getId()) != 0).collect(Collectors.toList());
		this.slots = slots;
		this.effectType = effected instanceof Player ? 2 : 1;
		this.changed = changed;
	}

	/**
	 * 5.0 oficial: id de template do efetor. NPC manda o npcId (776 de 776); jogador manda 100000 + raça×2 + gênero (141 de 141).
	 */
	public static int effectorTemplateId(Creature effector) {
		if (effector instanceof Player player)
			return 100000 + player.getRace().getRaceId() * 2 + player.getGender().getGenderId();
		if (effector instanceof Npc npc)
			return npc.getNpcId();
		return 0;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(effected.getObjectId());
		writeC(effectType); // unk
		writeD(0); // TODO time
		writeD(abnormals); // unk
		writeD(0); // unk
		writeC(slots); // 4.5
		writeH(filtered.size()); // effects size
		for (Effect effect : filtered) {
			writeD(effect.getEffectorId());
			writeD(effectorTemplateId(effect.getEffector()));
			writeH(effect.getSkillId());
			writeC(effect.getSkillLevel());
			writeC(effect.getTargetSlot().ordinal());
			writeD(effect.getRemainingTimeToDisplay());
			writeD(0);
			writeH(0);
			writeC(changed == null || changed == effect ? 1 : 0);
		}
	}
}

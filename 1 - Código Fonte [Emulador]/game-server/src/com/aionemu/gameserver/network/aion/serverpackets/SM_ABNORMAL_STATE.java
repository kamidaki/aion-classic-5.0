package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.Collection;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.skillengine.model.Effect;

/**
 * S_ABNORMAL_STATUS (0x31). 5.0 oficial: cabeçalho de 15 b e 23 b por efeito (1161 pacotes 0x31/0x32 de 33 capturas).
 *
 * @author Lost Academy Team & Durak
 */
public class SM_ABNORMAL_STATE extends AionServerPacket {

	private final Collection<Effect> effects;
	private final int abnormals;
	private final int slot;
	private final Effect changed;

	public SM_ABNORMAL_STATE(Collection<Effect> effects, int abnormals, int slot) {
		this(effects, abnormals, slot, null);
	}

	/**
	 * @param changed
	 *          efeito que acabou de entrar, marcado como novo; null marca todos (atualização completa)
	 */
	public SM_ABNORMAL_STATE(Collection<Effect> effects, int abnormals, int slot, Effect changed) {
		this.effects = effects;
		this.abnormals = abnormals;
		this.slot = slot;
		this.changed = changed;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(abnormals);
		writeD(0);
		writeD(0); // 4.5
		writeC(slot);
		writeH(effects.size());

		for (Effect effect : effects) {
			writeD(effect.getEffectorId());
			writeD(SM_ABNORMAL_EFFECT.effectorTemplateId(effect.getEffector()));
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

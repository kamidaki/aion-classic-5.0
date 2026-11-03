package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Marcadores da pistola do Phoenix (gunner_skill_dialog, 5 boost_marker). 5.0 oficial: 0x1B2, 8 b, logo depois de todo
 * S_ABNORMAL_STATUS do próprio Gunner (37/37 no tutorial do Phoenix).
 * <ul>
 * <li>acumulando o Overcharge Energy (9185/9187/9189): [D 0][D cargas 1-4];</li>
 * <li>na 5ª carga o acúmulo vira Fire Frenzy (9186/9188/9190, 5 s): [D ms restantes][D 0];</li>
 * <li>sem nenhum dos dois: [D 0][D 0].</li>
 * </ul>
 */
public class SM_CLASS_SKILL_STACK_INFO extends AionServerPacket {

	private final int blendedRemainingMillis;
	private final int stack;

	public SM_CLASS_SKILL_STACK_INFO(int blendedRemainingMillis, int stack) {
		this.blendedRemainingMillis = blendedRemainingMillis;
		this.stack = stack;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(blendedRemainingMillis);
		writeD(stack);
	}
}

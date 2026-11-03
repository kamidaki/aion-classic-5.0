package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.Summon;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.utils.stats.CalculationType;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_SUMMON_PANEL extends AionServerPacket {

	private final Summon summon;

	public SM_SUMMON_PANEL(Summon summon) {
		this.summon = summon;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(summon.getObjectId());
		writeH(summon.getLevel());
		writeD(0);// unk
		writeD(0);// unk
		writeD(summon.getLifeStats().getCurrentHp());
		writeD(summon.getGameStats().getMaxHp().getCurrent());
		writeD(summon.getGameStats().getMainHandPAttack(CalculationType.DISPLAY).getCurrent());
		// 5.0 oficial (S_ADD_PET, 36 b): defesa e resistência mágica em H, depois [D tempo de vida][H 0]
		writeH(summon.getGameStats().getPDef().getCurrent());
		writeH(summon.getGameStats().getMResist().getCurrent());
		writeD(summon.getLiveTime()); // life time
		writeH(0);// unk
	}

}

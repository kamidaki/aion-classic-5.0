package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.Summon;
import com.aionemu.gameserver.model.stats.calc.Stat;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;


public class S_CHANGE_PET_STATUS extends AionServerPacket {

	private Summon summon;

	public S_CHANGE_PET_STATUS(Summon summon) {
		this.summon = summon;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(summon.getLevel());
		writeH(summon.getMode().getId());
		writeD(0);// unk
		writeD(0);// unk
		writeD(summon.getLifeStats().getCurrentHp());

		Stat maxHp = summon.getGameStats().getMaxHp();
		writeD(maxHp.getCurrent());

		Stat mainHandPAttack = summon.getGameStats().getMainHandPAttack();
		writeD(mainHandPAttack.getCurrent());

		Stat pDef = summon.getGameStats().getPDef();
		writeH(pDef.getCurrent());

		Stat mResist = summon.getGameStats().getMResist();
		writeH(mResist.getCurrent());

		Stat accuracy = summon.getGameStats().getMainHandPAccuracy();
		writeH(accuracy.getCurrent());

		Stat mainHandPCritical = summon.getGameStats().getMainHandPCritical();
		writeH(mainHandPCritical.getCurrent());

		Stat mBoost = summon.getGameStats().getMBoost();
		writeH(mBoost.getCurrent());

		Stat mAccuracy = summon.getGameStats().getMAccuracy();
		writeH(mAccuracy.getCurrent());

		Stat mCritical = summon.getGameStats().getMCritical();
		writeH(mCritical.getCurrent());

		Stat parry = summon.getGameStats().getParry();
		writeH(parry.getCurrent());

		Stat evasion = summon.getGameStats().getEvasion();
		writeH(evasion.getCurrent());

		writeD(maxHp.getBase());
		writeD(mainHandPAttack.getBase());
		writeH(pDef.getBase());
		writeH(mResist.getBase());
		writeH(accuracy.getBase());
		writeH(mainHandPCritical.getBase());
		writeH(mBoost.getBase());
		writeH(mAccuracy.getBase());
		writeH(mCritical.getBase());
		writeH(parry.getBase());
		writeH(evasion.getBase());
	}

}

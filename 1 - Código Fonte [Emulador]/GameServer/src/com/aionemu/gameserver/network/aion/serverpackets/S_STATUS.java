package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.PlayerCommonData;
import com.aionemu.gameserver.model.stats.calc.Stat2;
import com.aionemu.gameserver.model.stats.container.PlayerGameStats;
import com.aionemu.gameserver.model.stats.container.PlayerLifeStats;
import com.aionemu.gameserver.model.stats.container.StatEnum;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.utils.gametime.GameTimeManager;

/**
 * S_STATUS (0x0001) - a ficha completa do personagem.
 */
public class S_STATUS extends AionServerPacket {

	private Player player;
	private PlayerGameStats pgs;
	private PlayerLifeStats pls;
	private PlayerCommonData pcd;

	public S_STATUS(Player player) {
		this.player = player;
		this.pcd = player.getCommonData();
		this.pgs = player.getGameStats();
		this.pls = player.getLifeStats();
	}

	@Override
	protected void writeImpl(AionConnection con) {
		Stat2 power = pgs.getPower();
		Stat2 health = pgs.getHealth();
		Stat2 accuracy = pgs.getAccuracy();
		Stat2 agility = pgs.getAgility();
		Stat2 knowledge = pgs.getKnowledge();
		Stat2 will = pgs.getWill();

		Stat2 wr = pgs.getStat(StatEnum.WATER_RESISTANCE, 0);
		Stat2 windr = pgs.getStat(StatEnum.WIND_RESISTANCE, 0);
		Stat2 er = pgs.getStat(StatEnum.EARTH_RESISTANCE, 0);
		Stat2 fr = pgs.getStat(StatEnum.FIRE_RESISTANCE, 0);
		Stat2 erl = pgs.getStat(StatEnum.ELEMENTAL_RESISTANCE_LIGHT, 0);
		Stat2 erd = pgs.getStat(StatEnum.ELEMENTAL_RESISTANCE_DARK, 0);

		Stat2 maxHp = pgs.getMaxHp();
		Stat2 maxMp = pgs.getMaxMp();
		Stat2 maxDp = pgs.getMaxDp();
		Stat2 maxSp = pgs.getMaxSp();
		Stat2 flyTime = pgs.getFlyTime();

		Stat2 mainHandPAtk = pgs.getMainHandPAttack();
		Stat2 offHandPAtk = pgs.getOffHandPAttack();
		Stat2 pdef = pgs.getPDef();
		Stat2 mAtk = pgs.getMAttack();
		Stat2 mresist = pgs.getMResist();
		Stat2 arange = pgs.getAttackRange();
		Stat2 aspeed = pgs.getAttackSpeed();
		Stat2 evasion = pgs.getEvasion();
		Stat2 parry = pgs.getParry();
		Stat2 block = pgs.getBlock();
		Stat2 mainHandPCrit = pgs.getMainHandPCritical();
		Stat2 offHandPCrit = pgs.getOffHandPCritical();
		Stat2 mainHandPAcc = pgs.getMainHandPAccuracy();
		Stat2 offHandPAcc = pgs.getOffHandPAccuracy();
		Stat2 mAcc = pgs.getMAccuracy();
		Stat2 mCrit = pgs.getMCritical();
		Stat2 boostCastTime = pgs.getReverseStat(StatEnum.BOOST_CASTING_TIME, 1000);
		Stat2 concentration = pgs.getStat(StatEnum.CONCENTRATION, 0);
		Stat2 mBoost = pgs.getMBoost();
		Stat2 healBoost = pgs.getStat(StatEnum.HEAL_BOOST, 0);
		Stat2 pCritResist = pgs.getStat(StatEnum.PHYSICAL_CRITICAL_RESIST, 0);
		Stat2 mCritResist = pgs.getStat(StatEnum.MAGICAL_CRITICAL_RESIST, 0);
		Stat2 pCritDamReduce = pgs.getStat(StatEnum.PHYSICAL_CRITICAL_DAMAGE_REDUCE, 0);
		Stat2 mCritDamReduce = pgs.getStat(StatEnum.MAGICAL_CRITICAL_DAMAGE_REDUCE, 0);

		int totalBoostMagicalSkill = mBoost.getCurrent();
		if (totalBoostMagicalSkill > 3200)
			totalBoostMagicalSkill = 3200;

		writeD(player.getObjectId()); // 000
		writeD(GameTimeManager.getGameTime().getTime()); // 004 minutos desde 1/1/00 00:00:00

		writeH(power.getCurrent()); // 008
		writeH(health.getCurrent()); // 010
		writeH(accuracy.getCurrent()); // 012
		writeH(agility.getCurrent()); // 014
		writeH(knowledge.getCurrent()); // 016
		writeH(will.getCurrent()); // 018

		writeH(wr.getCurrent()); // 020 agua
		writeH(windr.getCurrent()); // 022 vento
		writeH(er.getCurrent()); // 024 terra
		writeH(fr.getCurrent()); // 026 fogo
		writeH(erl.getCurrent()); // 028 luz
		writeH(erd.getCurrent()); // 030 trevas

		writeH(player.getLevel()); // 032

		writeH(0); // 034 desconhecido; flags (0, 1 ou 0x400D na captura)
		writeH(0); // 036 desconhecido; flags (0, 1 ou 3 na captura)
		writeH(0); // 038 desconhecido; sempre 0

		writeQ(pcd.getExpNeed()); // 040 exp que o nivel inteiro pede
		writeQ(pcd.getExpRecoverable()); // 048 exp recuperavel
		writeQ(pcd.getExpShown()); // 056 exp dentro do nivel
		writeD(0); // 064 desconhecido; sempre 0

		writeD(maxHp.getCurrent()); // 068
		writeD(pls.getCurrentHp()); // 072
		writeD(maxMp.getCurrent()); // 076
		writeD(pls.getCurrentMp()); // 080

		writeH(maxDp.getCurrent()); // 084
		writeH(pcd.getDp()); // 086

		writeD(maxSp.getCurrent()); // 088 na captura sempre 100
		writeD(pcd.getSp()); // 092 na captura sempre 0

		writeD(flyTime.getCurrent()); // 096 tempo de voo maximo
		writeD(pls.getCurrentFp()); // 100 tempo de voo atual

		writeC(player.getFlyState()); // 104
		writeC(0); // 105 mascara de movimento; 0 parado, 0xC3 voando na captura

		writeH(mainHandPAtk.getCurrent()); // 106
		writeH(offHandPAtk.getCurrent()); // 108
		writeH(pdef.getCurrent()); // 110
		writeH(mAtk.getCurrent()); // 112
		writeH(mresist.getCurrent()); // 114

		writeF(arange.getCurrent() / 1000f); // 116
		writeH(aspeed.getCurrent()); // 120

		writeH(evasion.getCurrent()); // 122
		writeH(parry.getCurrent()); // 124
		writeH(block.getCurrent()); // 126

		writeH(mainHandPCrit.getCurrent()); // 128
		writeH(offHandPCrit.getCurrent()); // 130
		writeH(mainHandPAcc.getCurrent()); // 132
		writeH(offHandPAcc.getCurrent()); // 134

		writeH(2); // 136 desconhecido; 2 nas tres capturas

		writeH(mAcc.getCurrent()); // 138
		writeH(mCrit.getCurrent()); // 140
		writeH(0); // 142 antigo magic boost; sempre 0

		writeF(boostCastTime.getCurrent() / 1000f); // 144

		writeH(concentration.getCurrent()); // 148
		writeH(totalBoostMagicalSkill); // 150
		writeH(healBoost.getCurrent()); // 152
		writeH(pCritResist.getCurrent()); // 154
		writeH(mCritResist.getCurrent()); // 156
		writeH(pCritDamReduce.getCurrent()); // 158
		writeH(mCritDamReduce.getCurrent()); // 160
		writeH(0); // 162 sempre 0 (a 2.8 escrevia 16472 aqui)

		writeD(player.getInventory().getLimit()); // 164 na captura 27
		writeD(player.getInventory().size()); // 168 quantidade de itens (5..17 na captura)
		writeD(0); // 172
		writeD(0); // 176
		writeD(pcd.getPlayerClass().getClassId()); // 180
		writeD(0); // 184
		writeD(0); // 188 desconhecido; quase sempre 0

		writeQ(pcd.getCurrentReposteEnergy()); // 192
		writeQ(pcd.getMaxReposteEnergy()); // 200

		writeC(pcd.getCurrentSalvationPercent()); // 208
		writeB(new byte[7]); // 209 desconhecido; varia na captura, 0 e aceito

		writeD(100); // 216 desconhecido; 100 nas tres capturas
		writeB(new byte[32]); // 220 sempre 0 na captura deste cliente

		writeD(0); // 252 desconhecido; par do 388, cresce com o nivel
		writeD(0); // 256 desconhecido; par do 392, cresce com o nivel
		writeD(0); // 260 sempre 0

		// ---------------------------------------------------------------- bloco "base"
		// (264..395)
		writeH(power.getBase()); // 264
		writeH(health.getBase()); // 266
		writeH(accuracy.getBase()); // 268
		writeH(agility.getBase()); // 270
		writeH(knowledge.getBase()); // 272
		writeH(will.getBase()); // 274

		writeH(wr.getBase()); // 276 agua
		writeH(windr.getBase()); // 278 vento
		writeH(er.getBase()); // 280 terra
		writeH(fr.getBase()); // 282 fogo
		writeH(erl.getBase()); // 284 luz
		writeH(erd.getBase()); // 286 trevas

		writeD(maxHp.getBase()); // 288
		writeD(maxMp.getBase()); // 292
		writeD(maxDp.getBase()); // 296
		writeD(maxSp.getBase()); // 300
		writeD(flyTime.getBase()); // 304
		writeD(100); // 308 desconhecido; 100 nas tres capturas

		writeD(0);

		writeH(mainHandPAtk.getBase()); // 316
		writeH(offHandPAtk.getBase()); // 318
		writeH(mAtk.getBase()); // 320
		writeH(pdef.getBase()); // 322
		writeH(mresist.getBase()); // 324
		writeH(0); // 326 sempre 0

		writeF(arange.getBase() / 1000f); // 328

		writeH(evasion.getBase()); // 332
		writeH(parry.getBase()); // 334
		writeH(block.getBase()); // 336

		writeH(mainHandPCrit.getBase()); // 338
		writeH(offHandPCrit.getBase()); // 340
		writeH(mCrit.getBase()); // 342
		writeH(0); // 344 sempre 0
		writeH(mainHandPAcc.getBase()); // 346
		writeH(offHandPAcc.getBase()); // 348

		writeH(2); // 350 desconhecido; 2 nas tres capturas, par do 136

		writeH(mAcc.getBase()); // 352
		writeH(concentration.getBase()); // 354
		writeH(mBoost.getBase()); // 356
		writeH(healBoost.getBase()); // 358
		writeH(pCritResist.getBase()); // 360
		writeH(mCritResist.getBase()); // 362
		writeH(pCritDamReduce.getBase()); // 364
		writeH(mCritDamReduce.getBase()); // 366

		writeB(new byte[20]); // 368 sempre 0 na captura
		writeD(0); // 388 sempre 0
		writeD(0); // 392 base do campo 252
		writeD(0); // 396 base do campo 256

		writeB(new byte[] {
				-1, -1, -1, -1, -1, -1,
				-1, -1, -1, -1, -1, -1
		}); // 400 doze 0xFF
	}
}
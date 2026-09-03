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

	private int safeCurrent(Stat2 s) {
		return s != null ? s.getCurrent() : 0;
	}

	private int safeBase(Stat2 s) {
		return s != null ? s.getBase() : 0;
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

		int totalBoostMagicalSkill = safeCurrent(mBoost);
		if (totalBoostMagicalSkill > 3200)
			totalBoostMagicalSkill = 3200;

		writeD(player.getObjectId()); // 000
		writeD(GameTimeManager.getGameTime().getTime()); // 004 minutos desde 1/1/00 00:00:00

		writeH(safeCurrent(power)); // 008
		writeH(safeCurrent(health)); // 010
		writeH(safeCurrent(accuracy)); // 012
		writeH(safeCurrent(agility)); // 014
		writeH(safeCurrent(knowledge)); // 016
		writeH(safeCurrent(will)); // 018

		writeH(safeCurrent(wr)); // 020 agua
		writeH(safeCurrent(windr)); // 022 vento
		writeH(safeCurrent(er)); // 024 terra
		writeH(safeCurrent(fr)); // 026 fogo
		writeH(safeCurrent(erl)); // 028 luz
		writeH(safeCurrent(erd)); // 030 trevas

		writeH(player.getLevel()); // 032

		writeH(0); // 034 desconhecido; flags (0, 1 ou 0x400D na captura)
		writeH(0); // 036 desconhecido; flags (0, 1 ou 3 na captura)
		writeH(0); // 038 desconhecido; sempre 0

		writeQ(pcd.getExpNeed()); // 040 exp que o nivel inteiro pede
		writeQ(pcd.getExpRecoverable()); // 048 exp recuperavel
		writeQ(pcd.getExpShown()); // 056 exp dentro do nivel
		writeD(0); // 064 desconhecido; sempre 0

		writeD(safeCurrent(maxHp)); // 068
		writeD(pls.getCurrentHp()); // 072
		writeD(safeCurrent(maxMp)); // 076
		writeD(pls.getCurrentMp()); // 080

		writeH(safeCurrent(maxDp)); // 084
		writeH(pcd.getDp()); // 086

		writeD(safeCurrent(maxSp)); // 088 na captura sempre 100
		writeD(pcd.getSp()); // 092 na captura sempre 0

		writeD(safeCurrent(flyTime)); // 096 tempo de voo maximo
		writeD(pls.getCurrentFp()); // 100 tempo de voo atual

		writeC(player.getFlyState()); // 104
		writeC(0); // 105 mascara de movimento; 0 parado, 0xC3 voando na captura

		writeH(safeCurrent(mainHandPAtk)); // 106
		writeH(safeCurrent(offHandPAtk)); // 108
		writeH(safeCurrent(pdef)); // 110
		writeH(safeCurrent(mAtk)); // 112
		writeH(safeCurrent(mresist)); // 114

		writeF(arange != null ? arange.getCurrent() / 1000f : 1.5f); // 116
		writeH(safeCurrent(aspeed)); // 120

		writeH(safeCurrent(evasion)); // 122
		writeH(safeCurrent(parry)); // 124
		writeH(safeCurrent(block)); // 126

		writeH(safeCurrent(mainHandPCrit)); // 128
		writeH(safeCurrent(offHandPCrit)); // 130
		writeH(safeCurrent(mainHandPAcc)); // 132
		writeH(safeCurrent(offHandPAcc)); // 134

		writeH(2); // 136 desconhecido; 2 nas tres capturas

		writeH(safeCurrent(mAcc)); // 138
		writeH(safeCurrent(mCrit)); // 140
		writeH(0); // 142 antigo magic boost; sempre 0

		writeF(boostCastTime != null ? boostCastTime.getCurrent() / 1000f : 1f); // 144

		writeH(safeCurrent(concentration)); // 148
		writeH(totalBoostMagicalSkill); // 150
		writeH(safeCurrent(healBoost)); // 152
		writeH(safeCurrent(pCritResist)); // 154
		writeH(safeCurrent(mCritResist)); // 156
		writeH(safeCurrent(pCritDamReduce)); // 158
		writeH(safeCurrent(mCritDamReduce)); // 160
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
		writeH(safeBase(power)); // 264
		writeH(safeBase(health)); // 266
		writeH(safeBase(accuracy)); // 268
		writeH(safeBase(agility)); // 270
		writeH(safeBase(knowledge)); // 272
		writeH(safeBase(will)); // 274

		writeH(safeBase(wr)); // 276 agua
		writeH(safeBase(windr)); // 278 vento
		writeH(safeBase(er)); // 280 terra
		writeH(safeBase(fr)); // 282 fogo
		writeH(safeBase(erl)); // 284 luz
		writeH(safeBase(erd)); // 286 trevas

		writeD(safeBase(maxHp)); // 288
		writeD(safeBase(maxMp)); // 292
		writeD(safeBase(maxDp)); // 296
		writeD(safeBase(maxSp)); // 300
		writeD(safeBase(flyTime)); // 304
		writeD(100); // 308 desconhecido; 100 nas tres capturas

		writeD(0);

		writeH(safeBase(mainHandPAtk)); // 316
		writeH(safeBase(offHandPAtk)); // 318
		writeH(safeBase(mAtk)); // 320
		writeH(safeBase(pdef)); // 322
		writeH(safeBase(mresist)); // 324
		writeH(0); // 326 sempre 0

		writeF(arange != null ? arange.getBase() / 1000f : 1.5f); // 328

		writeH(safeBase(evasion)); // 332
		writeH(safeBase(parry)); // 334
		writeH(safeBase(block)); // 336

		writeH(safeBase(mainHandPCrit)); // 338
		writeH(safeBase(offHandPCrit)); // 340
		writeH(safeBase(mCrit)); // 342
		writeH(0); // 344 sempre 0
		writeH(safeBase(mainHandPAcc)); // 346
		writeH(safeBase(offHandPAcc)); // 348

		writeH(2); // 350 desconhecido; 2 nas tres capturas, par do 136

		writeH(safeBase(mAcc)); // 352
		writeH(safeBase(concentration)); // 354
		writeH(safeBase(mBoost)); // 356
		writeH(safeBase(healBoost)); // 358
		writeH(safeBase(pCritResist)); // 360
		writeH(safeBase(mCritResist)); // 362
		writeH(safeBase(pCritDamReduce)); // 364
		writeH(safeBase(mCritDamReduce)); // 366

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
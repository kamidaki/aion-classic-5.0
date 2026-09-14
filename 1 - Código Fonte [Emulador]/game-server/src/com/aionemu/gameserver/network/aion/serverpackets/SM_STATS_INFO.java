package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.PlayerCommonData;
import com.aionemu.gameserver.model.stats.calc.Stat2;
import com.aionemu.gameserver.model.stats.container.PlayerGameStats;
import com.aionemu.gameserver.model.stats.container.PlayerLifeStats;
import com.aionemu.gameserver.model.stats.container.StatEnum;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.services.GameTimeService;
import com.aionemu.gameserver.utils.stats.CalculationType;

/**
 * SM_STATS_INFO (0x0001) - 412 bytes payload verified against official Classic 5.0 PCAP.
 * @author Lost Academy Team & Durak
 */
public class SM_STATS_INFO extends AionServerPacket {

	private Player player;
	private PlayerGameStats pgs;
	private PlayerLifeStats pls;
	private PlayerCommonData pcd;

	public SM_STATS_INFO(Player player) {
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
		Stat2 flyTime = pgs.getFlyTime();

		Stat2 mainHandPAtk = pgs.getMainHandPAttack(CalculationType.DISPLAY);
		Stat2 offHandPAtk = pgs.getOffHandPAttack(CalculationType.DISPLAY);
		Stat2 pdef = pgs.getPDef();
		Stat2 mAtk = pgs.getMainHandMAttack(CalculationType.DISPLAY);
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
		Stat2 mSkillBoostResist = pgs.getStat(StatEnum.MAGIC_SKILL_BOOST_RESIST, 0);
		Stat2 mCritResist = pgs.getStat(StatEnum.MAGICAL_CRITICAL_RESIST, 0);
		Stat2 pCritDamReduce = pgs.getStat(StatEnum.PHYSICAL_CRITICAL_DAMAGE_REDUCE, 0);
		Stat2 mCritDamReduce = pgs.getStat(StatEnum.MAGICAL_CRITICAL_DAMAGE_REDUCE, 0);


		int totalBoostMagicalSkill = safeCurrent(mBoost);
		if (totalBoostMagicalSkill > 3200)
			totalBoostMagicalSkill = 3200;

		writeD(player.getObjectId()); // 000
		writeD(GameTimeService.getInstance().getGameTime().getTime()); // 004

		writeH(safeCurrent(power)); // 008
		writeH(safeCurrent(health)); // 010
		writeH(safeCurrent(accuracy)); // 012
		writeH(safeCurrent(agility)); // 014
		writeH(safeCurrent(knowledge)); // 016
		writeH(safeCurrent(will)); // 018

		writeH(safeCurrent(wr)); // 020
		writeH(safeCurrent(windr)); // 022
		writeH(safeCurrent(er)); // 024
		writeH(safeCurrent(fr)); // 026
		writeH(safeCurrent(erl)); // 028
		writeH(safeCurrent(erd)); // 030

		writeH(player.getLevel()); // 032

		writeH(0); // 034
		writeH(0); // 036
		writeH(0); // 038

		writeQ(pcd.getExpNeed()); // 040
		writeQ(pcd.getExpRecoverable()); // 048
		writeQ(pcd.getExpShown()); // 056
		writeD(0); // 064

		writeD(safeCurrent(maxHp)); // 068
		writeD(pls.getCurrentHp()); // 072
		writeD(safeCurrent(maxMp)); // 076
		writeD(pls.getCurrentMp()); // 080

		writeH(safeCurrent(maxDp)); // 084
		writeH(pcd.getDp()); // 086

		writeD(100); // 088 maxSp (constant 100 on 5.0 wire)
		writeD(0); // 092 sp (constant 0 on 5.0 wire)

		writeD(safeCurrent(flyTime)); // 096
		writeD(pls.getCurrentFp()); // 100

		writeC(player.getFlyState()); // 104
		writeC(player.getMoveController() != null ? player.getMoveController().getMovementMask() : 0); // 105

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

		writeH(2); // 136

		writeH(safeCurrent(mAcc)); // 138
		writeH(safeCurrent(mCrit)); // 140
		writeH(0); // 142

		writeF(boostCastTime != null ? boostCastTime.getCurrent() / 1000f : 1f); // 144

		writeH(safeCurrent(concentration)); // 148
		writeH(totalBoostMagicalSkill); // 150
		writeH(safeCurrent(mSkillBoostResist)); // 152 supressão mágica (5.0 oficial: +68 ao vestir um torso com 68)
		writeH(safeCurrent(healBoost)); // 154 heal boost (5.0 oficial: acompanha as peças, 21/36/50/65/96)
		writeH(safeCurrent(mCritResist)); // 156
		writeH(safeCurrent(pCritDamReduce)); // 158
		writeH(safeCurrent(mCritDamReduce)); // 160
		writeH(0); // 162

		writeD(player.getInventory().getLimit()); // 164
		writeD(player.getInventory().size()); // 168
		writeD(0); // 172
		writeD(0); // 176
		writeD(pcd.getPlayerClass().getClassId()); // 180
		writeD(0); // 184
		writeD(0); // 188

		writeQ(pcd.getCurrentReposeEnergy()); // 192
		writeQ(pcd.getMaxReposeEnergy()); // 200

		writeC(pcd.getCurrentSalvationPercent()); // 208
		writeB(new byte[7]); // 209

		writeD(100); // 216
		writeB(new byte[32]); // 220

		int cp = com.aionemu.gameserver.services.CombatTalentService.calculateCombatPower(player);
		writeD(cp); // 252
		writeD(0); // 256
		writeD(0); // 260

		// ----------------------------- Base Block (264..399) -----------------------------
		writeH(safeBase(power)); // 264
		writeH(safeBase(health)); // 266
		writeH(safeBase(accuracy)); // 268
		writeH(safeBase(agility)); // 270
		writeH(safeBase(knowledge)); // 272
		writeH(safeBase(will)); // 274

		writeH(safeBase(wr)); // 276
		writeH(safeBase(windr)); // 278
		writeH(safeBase(er)); // 280
		writeH(safeBase(fr)); // 282
		writeH(safeBase(erl)); // 284
		writeH(safeBase(erd)); // 286

		writeD(safeBase(maxHp)); // 288
		writeD(safeBase(maxMp)); // 292
		writeD(safeBase(maxDp)); // 296
		writeD(100); // 300 base maxSp (constant 100 on 5.0 wire)
		writeD(safeBase(flyTime)); // 304
		writeD(100); // 308
		writeD(0); // 312

		writeH(safeBase(mainHandPAtk)); // 316
		writeH(safeBase(offHandPAtk)); // 318
		writeH(safeBase(mAtk)); // 320
		writeH(safeBase(pdef)); // 322
		writeH(safeBase(mresist)); // 324
		writeH(0); // 326

		writeF(arange != null ? arange.getBase() / 1000f : 1.5f); // 328

		writeH(safeBase(evasion)); // 332
		writeH(safeBase(parry)); // 334
		writeH(safeBase(block)); // 336

		writeH(safeBase(mainHandPCrit)); // 338
		writeH(safeBase(offHandPCrit)); // 340
		writeH(safeBase(mCrit)); // 342
		writeH(0); // 344
		writeH(safeBase(mainHandPAcc)); // 346
		writeH(safeBase(offHandPAcc)); // 348

		writeH(2); // 350

		writeH(safeBase(mAcc)); // 352
		writeH(safeBase(concentration)); // 354
		writeH(safeBase(mBoost)); // 356
		writeH(safeBase(mSkillBoostResist)); // 358 base da supressão mágica (5.0 oficial: os 68 sem bônus do torso e1)
		writeH(safeBase(healBoost)); // 360 base do heal boost (0 em todas as capturas)
		writeH(safeBase(mCritResist)); // 362
		writeH(safeBase(pCritDamReduce)); // 364
		writeH(safeBase(mCritDamReduce)); // 366

		writeB(new byte[20]); // 368
		writeD(cp); // 388
		writeD(0); // 392
		writeD(0); // 396

		// 400: Exactly twelve 0xFF bytes
		writeB(new byte[] {
				-1, -1, -1, -1, -1, -1,
				-1, -1, -1, -1, -1, -1
		});
	}
}


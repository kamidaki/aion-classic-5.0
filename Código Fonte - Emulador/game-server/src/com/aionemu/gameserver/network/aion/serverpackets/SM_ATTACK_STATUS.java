package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_ATTACK_STATUS extends AionServerPacket {

	private Creature creature;
	private Creature attacker;
	private TYPE type;
	private int skillId;
	private int value;
	private int logId;

	public static enum TYPE {
		// missing
		TYPE1(1),
		TYPE2(2),
		TYPE9(9),
		TYPE11(11),
		TYPE12(12),
		TYPE14(14),
		TYPE25(25),

		NATURAL_HP(3),
		USED_HP(4), // when skill uses hp as cost parameter
		REGULAR(5),
		ABSORBED_HP(6),
		DAMAGE(7),
		HP(7),
		PROTECTDMG(8),
		DELAYDAMAGE(10),
		DROWNING(12),
		HPAFTERRES(13), // when setting hp after resurrection, TODO implement
		MAGICCOUNTERATK(15),
		DISPELBUFFCOUNTERATK(16), // TODO implement
		FALL_DAMAGE(17),
		DOOR_REPAIR(18),
		HEAL_MP(19),
		DAMAGE_MP(20),
		ABSORBED_MP(20),
		MP(21),
		NATURAL_MP(22),
		FP_HEAL(23),
		FP_RINGS(24),
		FP(26),
		FP_DAMAGE(26),
		NATURAL_FP(27);

		private int value;

		private TYPE(int value) {
			this.value = value;
		}

		public int getValue() {
			return this.value;
		}

	}

	public static enum LOG {

		SPELLATK(1),
		HEAL(3),
		MPHEAL(4),
		CASEHEAL(21),
		SKILLLATKDRAININSTANT(23),
		SPELLATKDRAININSTANT(24),
		POISON(25),
		BLEED(26),
		PROCATKINSTANT(93), // changed in 4.5
		DELAYEDSPELLATKINSTANT(97), // changed in 4.5
		MAGICCOUNTERATK(112),
		// 119 unk
		// 131 unk
		SPELLATKDRAIN(132), // changed in 4.5
		FPHEAL(134), // changed in 4.5
		FPATTACK(137),
		MPATTACK(141),
		REGULAR(191); // 4.8

		private int value;

		private LOG(int value) {
			this.value = value;
		}

		public int getValue() {
			return this.value;
		}
	}

	public SM_ATTACK_STATUS(Creature creature, Creature attacker, TYPE type, int skillId, int value, LOG log) {
		this.creature = creature;
		this.attacker = attacker;
		this.type = type;
		this.skillId = skillId;
		this.value = value;
		this.logId = log.getValue();
	}

	public SM_ATTACK_STATUS(Creature creature, TYPE type, int skillId, int value, LOG log) {
		this(creature, null, type, skillId, value, log);
	}

	public SM_ATTACK_STATUS(Creature creature, TYPE type, int skillId, int value) {
		this(creature, null, type, skillId, value, LOG.REGULAR);
	}

	public SM_ATTACK_STATUS(Creature creature, int value) {
		this(creature, null, TYPE.REGULAR, 0, value, LOG.REGULAR);
	}

	@Override
	protected void writeImpl(AionConnection con) {
		int hpPercentage = creature.getLifeStats().getHpPercentage();
		writeD(creature.getObjectId());
		switch (type) {
			case DAMAGE:
			case DELAYDAMAGE:
			case FALL_DAMAGE:
			case FP_DAMAGE:
			case MAGICCOUNTERATK:
			case DISPELBUFFCOUNTERATK:
			case USED_HP:
			case DROWNING:
			case DAMAGE_MP:
				writeD(-value);
				break;
			default:
				writeD(value);
		}
		writeC(type.getValue());
		writeC(hpPercentage);
		writeH(skillId);
		writeH(0); // 5.0 Classic unk1
		writeH(logId);
		writeD(attacker != null ? attacker.getObjectId() : 0); // 5.0 Classic attacker objectId
		writeD(0); // 5.0 Classic unk2
	}

	/**
	 * logId depends on effecttemplate
	 * effecttemplate (TYPE) LOG.getValue()
	 * 
	 * spellattack (7) 1 (as negative value)//checked 4.5
	 * heal(7) 3 //checked 4.5
	 * mpheal (21) 4 //checked 4.5
	 * SpellAtkDrainInstantEffect(20) 24 (refactoring shard, soul absorption) //checked 4.5
	 * poison(hp) 25
	 * bleed(hp) 26
	 * procatkinstant - (7) 93 // checked in 4.5
	 * delaydamage(10) 97 (lava tsunami) // checked in 4.5
	 * falldmg (17) 170 hp as cost
	 * parameter(4) 187 // checked in 4.5
	 * mp regen(natural_mp) 187 //187 in 4.5
	 * hp regen(natural_hp) 187 //187 in 4.5
	 * fp regen(natural_fp) 187 //187 in 4.5
	 * fp pot(fp) 171
	 * prochp(7) 187 //checked in 4.5
	 * procmp(21) 187 //checked in 4.5
	 * heal_instant (regular) 171 protecteffect on protector - (8) 171 4.5
	 * type="MP(21)" skillId="17722" logId="UNKNOWN(141) - mpattack
	 * type="UNKNOWN(15)" skillId="2196" logId="UNKNOWN(112) - magiccounteratk
	 * type="DAMAGE_HEAL_HP(7)" skillId="2858" logId="UNKNOWN(3073)" - spellatk(Flame Cage only)???
	 * type="DAMAGE_HEAL_HP(7)"  skillId="8759" logId="UNKNOWN(132)" - spellatkdrain
	 * type="DAMAGE_HEAL_HP(7)"  skillId="2391" logId="UNKNOWN(21)" - caseheal(hp)
	 * type="DAMAGE_HEAL_FP(26)" skillId="8772" logId="UNKNOWN(134) - fpheal
	 * type="UNKNOWN(16)" skillId="0" logId="REGULAR(187)" - dispelbuffcounteratk(2404)
	 * type="UNKNOWN(13)" skillId="0" logId="REGULAR(187)" - setting hp after resurrect
	 * TODO find rest of logIds
	 */
}

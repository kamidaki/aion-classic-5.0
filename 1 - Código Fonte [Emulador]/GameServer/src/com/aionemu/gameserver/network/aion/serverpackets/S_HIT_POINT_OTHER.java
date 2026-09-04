package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.configs.main.GSConfig;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

public class S_HIT_POINT_OTHER extends AionServerPacket
{
    private Creature attacked;
    private Creature attacker;
    private TYPE type;
    private int skillId;
    private int value;
    private int logId;
	
    public static enum TYPE {
        NATURAL_HP(3),
		USED_HP(4),
		REGULAR(5),
		ABSORBED_HP(6),
		DAMAGE(7),
		HP(7),
		PROTECTDMG(8),
		DELAYDAMAGE(10),
		FALL_DAMAGE(17),
		HEAL_MP(19),
		ABSORBED_MP(20),
		MP(21),
		NATURAL_MP(22),
		ATTACK(23),
		FP_RINGS(24),
		FP(25),
		NATURAL_FP(26),
		NATURAL_FP2(27);
		
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
		SKILLLATKDRAININSTANT(23),
		SPELLATKDRAININSTANT(24),
		POISON(25),
		BLEED(26),
		PROCATKINSTANT(92),
		DELAYEDSPELLATKINSTANT(95),
		SPELLATKDRAIN(130),
		FPHEAL(133),
		REGULARHEAL(170),
        REGULAR(178),
        ATTACK(172);
		
        private int value;
		
        private LOG(int value) {
            this.value = value;
        }
		
        public int getValue() {
            return this.value;
        }
    }
	
	public S_HIT_POINT_OTHER(Creature attacked, Creature attacker, TYPE type, int skillId, int value, LOG log) {
        this.attacked = attacked;
        this.attacker = attacker;
        this.type = type;
        this.skillId = skillId;
        this.value = value;
        this.logId = log.getValue();
    }
	
    public S_HIT_POINT_OTHER(Creature attacked, Creature attacker, TYPE type, int skillId, int value) {
        this(attacked, attacker, type, skillId, value, LOG.REGULAR);
    }
	
    public S_HIT_POINT_OTHER(Creature attacked, Creature attacker, int value) {
        this(attacked, attacker, TYPE.REGULAR, 0, value, LOG.REGULAR);
    }
	
    protected void writeImpl(AionConnection con) {
        writeD(this.attacked.getObjectId());
        switch (this.type) {
            case DAMAGE:
            case DELAYDAMAGE:
                writeD(-this.value);
            break;
            default:
            writeD(this.value);
        }
        writeC(this.type.getValue());
        if ((this.type.getValue() == 19) || (this.type.getValue() == 20) || (this.type.getValue() == 21) || (this.type.getValue() == 22)) {
            writeC(this.attacked.getLifeStats().getMpPercentage());
        } else {
            writeC(this.attacked.getLifeStats().getHpPercentage());
        }
        // 24 bytes, medidos por variancia nas 3669 amostras da captura oficial (subida-1-60,
        // sessao 1 -- todas com 24 bytes). Os campos aparecem sozinhos: off 0-3 o atingido, 4-7 o
        // valor, 8 o tipo, 9 a porcentagem de vida (100 valores distintos, 0..100), 10-11 o
        // skillId, 12-13 sempre zero, 14 o logId, 15 sempre zero, 16-19 o objectId do ATACANTE
        // (os mesmos padroes de byte do off 0), 20-23 sempre zero.
        // O nosso saia com 14: faltavam os dez bytes do logId em diante, e o logId ainda estava
        // escrito como H no lugar onde o fio tem um H(0).
        writeH(skillId);
        writeH(0);
        writeC(logId);
        writeC(0);
        writeD(attacker != null ? attacker.getObjectId() : 0);
        writeD(0);
    }
}
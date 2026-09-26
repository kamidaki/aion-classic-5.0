package ai;

import com.aionemu.commons.utils.Rnd;
import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.stats.calc.Stat2;
import com.aionemu.gameserver.skillengine.model.Effect;

/**
 * Cubo mimico do tutorial Land of Shadows.
 *
 * A captura oficial confirma dano fixo de 1, o primeiro crescimento no primeiro acerto e ate quatro formas
 * (skills 19981-19984). Crescimentos posteriores variam entre execucoes; 10% e a taxa inferida da amostra atual
 * (4 crescimentos adicionais em 54 oportunidades), isolada aqui para ser refinada com novas capturas.
 */
@AIName("shadowrealm_cube")
public class ShadowrealmCubeAI extends GeneralNpcAI {

	private static final int MAX_LEVEL = 5;
	private static final int INFERRED_EXTRA_GROWTH_CHANCE = 10;
	private int cubeLevel = 1;

	public ShadowrealmCubeAI(Npc owner) {
		super(owner);
	}

	@Override
	protected void handleAttack(Creature creature) {
		// O cubo e um alvo destrutivel, nao um monstro combatente. Entrar em FIGHT fazia a IA sem movimento
		// desistir do alvo e iniciar a restauracao natural de 50% do HP a cada ciclo.
		getOwner().getLifeStats().cancelRestoreTask();
		if (cubeLevel >= MAX_LEVEL)
			return;
		if (cubeLevel == 1 || Rnd.chance() < INFERRED_EXTRA_GROWTH_CHANCE) {
			getOwner().getController().useSkill(19980 + cubeLevel);
			cubeLevel++;
		}
	}

	@Override
	public float modifyDamage(Creature attacker, float damage, Effect effect) {
		return 1;
	}

	@Override
	public float modifyOwnerDamage(float damage, Creature effected, Effect effect) {
		return 1;
	}

	@Override
	public void modifyOwnerStat(Stat2 stat) {
		switch (stat.getStat()) {
			case MAGICAL_RESIST:
			case EVASION:
				stat.setBase(0);
				stat.setBonus(0);
		}
	}

}

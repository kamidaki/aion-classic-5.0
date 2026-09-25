package ai;

import com.aionemu.commons.utils.Rnd;
import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.Npc;

/**
 * Cubo mimico do tutorial Land of Shadows.
 *
 * A captura oficial confirma dano fixo de 1, o primeiro crescimento no primeiro acerto e ate quatro formas
 * (skills 19981-19984). Crescimentos posteriores variam entre execucoes; 10% e a taxa inferida da amostra atual
 * (4 crescimentos adicionais em 54 oportunidades), isolada aqui para ser refinada com novas capturas.
 */
@AIName("shadowrealm_cube")
public class ShadowrealmCubeAI extends OneDmgAI {

	private static final int MAX_LEVEL = 5;
	private static final int INFERRED_EXTRA_GROWTH_CHANCE = 10;
	private int cubeLevel = 1;

	public ShadowrealmCubeAI(Npc owner) {
		super(owner);
	}

	@Override
	protected void handleAttack(Creature creature) {
		super.handleAttack(creature);
		if (cubeLevel >= MAX_LEVEL)
			return;
		if (cubeLevel == 1 || Rnd.chance() < INFERRED_EXTRA_GROWTH_CHANCE) {
			getOwner().getController().useSkill(19980 + cubeLevel);
			cubeLevel++;
		}
	}

}

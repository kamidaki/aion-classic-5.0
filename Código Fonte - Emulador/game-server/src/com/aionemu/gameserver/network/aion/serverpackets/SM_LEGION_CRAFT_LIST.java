package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S 0x15A, receitas de produção da Legion: [H n] n x ([D receita][D ?][D ?][H m] m x ([D item][D doado]) [C ?]) [C 1].
 * <p>
 * No login e na criação vem a lista inteira (40 receitas, 1059 b, Lost Academy 22/09); depois de uma doação, só a receita doada (34 b). Os dois D
 * e o C de cada receita foram 0 nas 25 variantes: PENDENTE_DE_COMPROVACAO (provavelmente início, fim e estado da produção, que nenhuma captura
 * mostra).
 */
public class SM_LEGION_CRAFT_LIST extends AionServerPacket {

	public record Component(int itemId, long donated) {}

	public record Recipe(int recipeId, List<Component> components) {}

	private final List<Recipe> recipes;

	public SM_LEGION_CRAFT_LIST(List<Recipe> recipes) {
		this.recipes = recipes;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(recipes.size());
		for (Recipe recipe : recipes) {
			writeD(recipe.recipeId());
			writeD(0);
			writeD(0);
			writeH(recipe.components().size());
			for (Component component : recipe.components()) {
				writeD(component.itemId());
				writeD((int) Math.min(component.donated(), Integer.MAX_VALUE));
			}
			writeC(0);
		}
		writeC(1);
	}
}

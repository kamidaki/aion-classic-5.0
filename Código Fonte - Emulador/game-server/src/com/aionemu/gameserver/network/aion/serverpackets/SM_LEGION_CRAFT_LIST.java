package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S 0x15A, receitas de produção da Legion: [H n] n x ([D receita][D início da produção][D ?][H m] m x ([D item][D doado]) [C ?]) [C 1].
 * <p>
 * No login e na criação vem a lista inteira (40 receitas, 1059 b, Lost Academy 22/09); depois de uma doação ou produção, só a receita (34 b e
 * 18 b). O início da produção é a hora em que a Lost Academy fez uma essência (receita 1, 0x6AB2FFCC, 22/09 19:22). PENDENTE_DE_COMPROVACAO: o
 * segundo D e o C de cada receita, 0 em todas as variantes.
 */
public class SM_LEGION_CRAFT_LIST extends AionServerPacket {

	public record Component(int itemId, long donated) {}

	public record Recipe(int recipeId, int craftStart, List<Component> components) {

		public Recipe(int recipeId, List<Component> components) {
			this(recipeId, 0, components);
		}
	}

	private final List<Recipe> recipes;

	public SM_LEGION_CRAFT_LIST(List<Recipe> recipes) {
		this.recipes = recipes;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(recipes.size());
		for (Recipe recipe : recipes) {
			writeD(recipe.recipeId());
			writeD(recipe.craftStart());
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

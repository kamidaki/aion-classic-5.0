package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S 0x15A, receitas de produção da Legion: [H n] n x ([D receita][D início da produção][D ?][H m] m x ([D item][D doado]) [C ?]) [C 1].
 * <p>
 * No login e na criação vem a lista inteira (40 receitas, 1059 b, Lost Academy 22/09); depois de uma doação ou produção, só a receita (34 b e
 * 18 b). O início da produção é a hora em que a Lost Academy fez uma essência (receita 1, 0x6AB2FFCC, 22/09 19:22). PENDENTE_DE_COMPROVACAO: o
 * segundo D, 0 em todas as variantes. O C de cada receita é o favorito (C_GUILD 0x16): 1 nas receitas 1 a 3 e 13 nos logins da Nova Pasta
 * 2026-09-29 16:40 e 16:49 depois de marcá-las, 0 depois de desmarcar.
 */
public class SM_LEGION_CRAFT_LIST extends AionServerPacket {

	public record Component(int itemId, long donated) {}

	public record Recipe(int recipeId, int craftStart, boolean bookmarked, List<Component> components) {

		public Recipe(int recipeId, int craftStart, List<Component> components) {
			this(recipeId, craftStart, false, components);
		}

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
			writeC(recipe.bookmarked() ? 1 : 0);
		}
		writeC(1);
	}
}

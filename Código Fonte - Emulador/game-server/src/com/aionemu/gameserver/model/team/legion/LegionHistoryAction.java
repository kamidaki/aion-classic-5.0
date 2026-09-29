package com.aionemu.gameserver.model.team.legion;

/**
 * @author Lost Academy Team & Durak
 */
public enum LegionHistoryAction {

	CREATE(0, Type.LEGION), // No parameters
	JOIN(1, Type.LEGION), // Parameter: name
	KICK(2, Type.LEGION), // Parameter: name
	LEVEL_UP(3, Type.LEGION), // Parameter: legion level
	APPOINTED(4, Type.LEGION), // Parameter: legion level
	EMBLEM_REGISTER(5, Type.LEGION), // No parameters
	EMBLEM_MODIFIED(6, Type.LEGION), // No parameters
	// 7 to 10 are not used anymore or never implemented
	DEFENSE(11, Type.REWARD), // Parameter: name = kinah amount, description = fortress id
	OCCUPATION(12, Type.REWARD), // Parameter: name = kinah amount, description = fortress id
	LEGION_RENAME(13, Type.LEGION), // Parameter: old name, new name
	CHARACTER_RENAME(14, Type.LEGION), // Parameter: old name, new name
	ITEM_DEPOSIT(15, Type.WAREHOUSE), // Parameter: name
	ITEM_WITHDRAW(16, Type.WAREHOUSE), // Parameter: name
	KINAH_DEPOSIT(17, Type.WAREHOUSE), // Parameter: name
	KINAH_WITHDRAW(18, Type.WAREHOUSE), // Parameter: name
	CAMPAIGN_CHANGE(27, Type.LEGION), // 5.0, troca da atividade de campanha (Nova Pasta 2026-09-29 16:14), sem parâmetros
	// 5.0, histórico de produção (tipo 3) da Lost Academy (Nova Pasta 2026-09-29 16:02 e outros2 2026-09-22 19:22)
	CRAFT_START(20, Type.CRAFT), // name = quem iniciou, description = [item_text:produto]
	CRAFT_COMPLETE(21, Type.CRAFT), // name = [item_text:produto]
	ESSENCE_START(24, Type.CRAFT), // name = quem iniciou
	ESSENCE_COMPLETE(25, Type.CRAFT); // sem parâmetros

	private final byte id;
	private final Type type;

	LegionHistoryAction(int id, Type type) {
		this.id = (byte) id;
		this.type = type;
	}

	public byte getId() {
		return id;
	}

	public Type getType() {
		return type;
	}

	/**
	 * Aba do histórico: o cliente pede cada uma pelo número (dec 0xFFFF [D página][C tipo]); a 3 é a de produção da 5.0.
	 */
	public enum Type { LEGION, REWARD, WAREHOUSE, CRAFT }
}

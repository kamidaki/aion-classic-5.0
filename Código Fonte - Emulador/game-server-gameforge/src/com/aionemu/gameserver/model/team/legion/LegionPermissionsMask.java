package com.aionemu.gameserver.model.team.legion;

/**
 * @author Lost Academy Team & Durak
 */
public enum LegionPermissionsMask {

	EDIT(0x200),
	INVITE(0x8),
	KICK(0x10),
	WH_WITHDRAWAL(0x4),
	WH_DEPOSIT(0x1000),
	ARTIFACT(0x400),
	GUARDIAN_STONE(0x800),
	// Nova Pasta 2026-09-29 16:40: as caixas do Tribunus (Deputy) desmarcadas uma a uma de cima para baixo deram 0x7C1C, 0x7C14, 0x7C04, 0x7C00,
	// 0x6C00, 0x6800, 0x6000, 0x4000 e 0; a penúltima é Craft/Favourite e a última Enchant/Activate/Reset Buff.
	CRAFT(0x2000),
	BUFF(0x4000);

	private int rank;

	private LegionPermissionsMask(int rank) {
		this.rank = rank;
	}

	public boolean can(int permission) {
		return (rank & permission) != 0;
	}
}

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
	// Nova Pasta 2026-09-29 16:14: C_GUILD 0x0D do Deputy com 0x5E0C e 0x3E0C (as duas caixas novas desmarcadas, uma de cada vez) e 0x7E1C com
	// tudo marcado; a ordem das linhas da janela (Craft/Favourite antes de Enchant/Activate/Reset Buff) dá 0x2000 à produção e 0x4000 ao buff.
	// PENDENTE_DE_COMPROVACAO: a ligação de cada envio à caixa desmarcada.
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

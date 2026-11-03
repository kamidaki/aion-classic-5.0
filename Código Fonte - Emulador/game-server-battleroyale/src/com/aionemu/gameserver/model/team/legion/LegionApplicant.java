package com.aionemu.gameserver.model.team.legion;

/**
 * Candidatura a uma Legion pela busca de Legion (C 0x119), como o líder a vê no S 0x152: quem se candidatou, classe, sexo, nível, a
 * apresentação e a hora. {@code refused} marca a recusa ainda não avisada ao candidato (STR_GUILD_JOIN_REFUSAL no login seguinte).
 */
public record LegionApplicant(int playerId, int legionId, String name, int playerClass, int gender, int level, String intro, int applyTime,
	boolean refused) {}

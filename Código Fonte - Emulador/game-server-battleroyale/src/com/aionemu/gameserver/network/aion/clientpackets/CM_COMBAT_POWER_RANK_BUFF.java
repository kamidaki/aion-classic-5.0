package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.templates.ranking.CombatPowerRankBuff;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_RANK_LIST.RankingEntry;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemUpdateType;
import com.aionemu.gameserver.services.ranking.RankingService;
import com.aionemu.gameserver.skillengine.SkillEngine;
import com.aionemu.gameserver.skillengine.model.SkillTemplate;

/**
 * Compra do buff do 1º lugar do ranking de Combat Talent (o ícone laranja), C 0xFC [D aba][D classe ou -1][D posição][D objeto do ranqueado].
 * <p>
 * Capturas 06_Sistemas_Novos 2026-10-20 02:17 e 02:23: aba 1002 com -1 e aba 1003 com a classe 16. A resposta é o Kinah (S 0x1D, motivo 0x10E)
 * e o buff no S 0x31 (3914 e 3923, 2 h). O preço é o buff_kina (11.500 e 7.300). A confirmação é só do cliente: cancelar não manda nada.
 */
public class CM_COMBAT_POWER_RANK_BUFF extends AionClientPacket {

	private int rankingType;
	private int classId;
	private int rank;
	private int targetObjectId;

	public CM_COMBAT_POWER_RANK_BUFF(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		rankingType = readD();
		classId = readD();
		rank = readD();
		targetObjectId = readD();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		RankingEntry entry = RankingService.getInstance().getEntry(rankingType, targetObjectId);
		if (entry == null || entry.rank() != rank || (classId != -1 && entry.playerClassId() != classId))
			return;
		CombatPowerRankBuff buff = DataManager.COMBAT_POWER_RANK_BUFF_DATA.getBuff(rankingType, rank, entry.playerClassId());
		if (buff == null)
			return;
		SkillTemplate skill = DataManager.SKILL_DATA.getSkillTemplate(buff.getSkillId());
		if (skill == null)
			return;
		if (!player.getInventory().tryDecreaseKinah(buff.getPrice(), ItemUpdateType.DEC_KINAH_RANKING_BUFF)) {
			sendPacket(SM_SYSTEM_MESSAGE.STR_NOT_ENOUGH_MONEY());
			return;
		}
		SkillEngine.getInstance().applyEffectDirectly(skill, skill.getLvl(), player, player);
	}
}

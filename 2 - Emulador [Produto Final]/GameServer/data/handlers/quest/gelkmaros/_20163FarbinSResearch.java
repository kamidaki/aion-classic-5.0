package quest.gelkmaros;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 20163 Farbin's Research. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q20163.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _20163FarbinSResearch extends CampaignQuestHandler {

	public _20163FarbinSResearch() {
		super(20163, 20162);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 799268); // Nysdvor
		talk(1, 2, 2, 799282); // Martinez
		check(2, 3, 3, 799282); // amostras (quest_monster drop@2); check_ok -> SELECT4
		talkGive(3, 4, 4, 182215607, 1, 799282); // Martinez (select4) entrega a pedra de invocação (quest_20163e)
		useObject(4, 5, 700702); // destruir DF4_DranaSuctionDevice_B3_Q20022
		itemUseArea(5, 6, 182215607, "DF4_ITEMUSEAREA_Q20022_220070000"); // CSV Progress(5) itemUseArea
		talk(6, 7, REWARD, 799282); // Martinez, select7 SET_SUCCEED
		reward(799226); // Barretta
	}
}

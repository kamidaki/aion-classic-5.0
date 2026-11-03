package com.aionemu.gameserver.questEngine.handlers;

import static com.aionemu.gameserver.model.DialogAction.*;
import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.dataholders.QuestsData;
import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler.Reply;
import com.aionemu.gameserver.questEngine.model.QuestState;
import com.aionemu.gameserver.questEngine.model.QuestStatus;

/**
 * Máquina de etapas das campanhas contra o que as capturas e o quest_script_monster.csv oficiais mostram.
 */
class CampaignQuestHandlerTest {

	private static QuestsData previous;

	@BeforeAll
	static void emptyQuestData() {
		previous = DataManager.QUEST_DATA;
		DataManager.QUEST_DATA = new QuestsData(); // o construtor do handler só consulta o template (work items)
	}

	@AfterAll
	static void restore() {
		DataManager.QUEST_DATA = previous;
	}

	/** Como a 20542 da captura outros2 (22/09): Udvi 205778, Kusir 205779, área sensorial 206281. */
	private static final class Q20542 extends CampaignQuestHandler {

		Q20542() {
			super(20542, 20541);
		}

		@Override
		protected void defineSteps() {
			talk(0, 1, 1, 205778);
			talk(1, 2, 2, 205779);
			check(2, 3, 3, 205779);
			talk(3, 4, 4, 205779);
			sensory(4, REWARD, 206281);
			reward(205778);
		}
	}

	/** Trechos da 10160, 10161 e 10162 com as vars do CSV oficial. */
	private static final class Mixed extends CampaignQuestHandler {

		Mixed() {
			super(10160);
		}

		@Override
		protected void defineSteps() {
			talk(2, 3, 3, 799025); // Laokoon: SETPRO3 ou SETPRO7
			branch(SETPRO7, 7);
			killSection(5, 1, 1, 6, 216489);
			killSection(5, 2, 1, 6, 216490);
			killSection(5, 3, 1, 6, 216491);
			kill(11, 7, 215502, 215503); // Progress(11~!18)
			talk(18, 13, REWARD, 798950);
			useObjects(20, 5, 700601);
			reward(798927);
		}
	}

	private static QuestState start(int questId, int var) {
		QuestState qs = new QuestState(questId, QuestStatus.START);
		qs.setQuestVar(var);
		return qs;
	}

	@Test
	void dialogPagesFollowTheCapture() {
		Q20542 q = new Q20542();
		QuestState qs = start(20542, 0);
		// 430.00: QUEST_SELECT -> 1011, 1012, 1013, SETPRO1 (10000) -> var 1
		assertEquals(Reply.page(1011), q.decide(qs, 205778, QUEST_SELECT, false));
		assertEquals(Reply.page(1012), q.decide(qs, 205778, 1012, false));
		assertEquals(Reply.page(1013), q.decide(qs, 205778, 1013, false));
		Reply setpro = q.decide(qs, 205778, SETPRO1, false);
		assertEquals(Reply.Type.ADVANCE, setpro.type());
		assertEquals(1, setpro.value());
		// o NPC certo, mas na var errada: nada (o menu do NPC responde a página 10)
		assertEquals(Reply.NONE, q.decide(qs, 205779, QUEST_SELECT, false));
		// 872.13: var 1 -> Kusir select2 (1352) -> 1353.. -> SETPRO2 -> var 2
		CampaignQuestHandler.apply(qs, setpro.value());
		assertEquals(Reply.page(1352), q.decide(qs, 205779, QUEST_SELECT, false));
		assertEquals(Reply.page(1355), q.decide(qs, 205779, 1355, false));
		assertEquals(2, q.decide(qs, 205779, SETPRO2, false).value());
	}

	@Test
	void clickOnMenuNpcDoesNotHijackTheMenu() {
		Q20542 q = new Q20542();
		QuestState qs = start(20542, 0);
		assertEquals(Reply.NONE, q.decide(qs, 205778, USE_OBJECT, false)); // NPC com menu: página 10
		assertEquals(Reply.page(1011), q.decide(qs, 205778, USE_OBJECT, true)); // objeto de quest: abre a página
	}

	@Test
	void checkStepAsksForItems() {
		Q20542 q = new Q20542();
		QuestState qs = start(20542, 2);
		assertEquals(Reply.page(1693), q.decide(qs, 205779, QUEST_SELECT, false));
		Reply check = q.decide(qs, 205779, CHECK_USER_HAS_QUEST_ITEM, false);
		assertEquals(Reply.Type.CHECK, check.type());
		assertEquals(3, check.value());
	}

	@Test
	void rewardFlowFollowsOutros2() {
		Q20542 q = new Q20542();
		QuestState qs = start(20542, 4);
		qs.setStatus(QuestStatus.REWARD);
		// 401.75: clique no NPC de recompensa -> 10002; 1009 -> página de recompensa (sendQuestEndDialog); 23 -> fim
		assertEquals(Reply.page(10002), q.decide(qs, 205778, USE_OBJECT, false));
		assertEquals(Reply.page(10002), q.decide(qs, 205778, QUEST_SELECT, false));
		assertEquals(Reply.END, q.decide(qs, 205778, SELECT_QUEST_REWARD, false));
		assertEquals(Reply.END, q.decide(qs, 205778, SELECTED_QUEST_NOREWARD, false));
		assertEquals(Reply.CLOSE, q.decide(qs, 205778, FINISH_DIALOG, false));
		assertEquals(Reply.NONE, q.decide(qs, 205779, QUEST_SELECT, false)); // outro NPC não entrega
	}

	@Test
	void completedMissionIsInert() {
		Q20542 q = new Q20542();
		QuestState qs = new QuestState(20542, QuestStatus.COMPLETE);
		assertEquals(Reply.NONE, q.decide(qs, 205778, QUEST_SELECT, false));
		assertEquals(Reply.NONE, q.decide(qs, 205778, SELECT_QUEST_REWARD, false));
		assertEquals(CampaignQuestHandler.KILL_IGNORED, new Mixed().countKill(qs, 215502));
		assertEquals(Reply.NONE, q.decide(null, 205778, QUEST_SELECT, false));
	}

	@Test
	void branchSkipsTheWindstream() {
		Mixed q = new Mixed();
		QuestState qs = start(10160, 2);
		assertEquals(3, q.decide(qs, 799025, SETPRO3, false).value());
		assertEquals(7, q.decide(qs, 799025, SETPRO7, false).value());
	}

	@Test
	void killRangeUsesProgressFromCsv() {
		Mixed q = new Mixed();
		QuestState qs = start(10160, 10);
		assertEquals(CampaignQuestHandler.KILL_IGNORED, q.countKill(qs, 215502)); // var 10: ainda não
		qs.setQuestVar(11);
		for (int i = 0; i < 6; i++)
			assertEquals(CampaignQuestHandler.KILL_COUNTED, q.countKill(qs, i % 2 == 0 ? 215502 : 215503));
		assertEquals(17, qs.getQuestVarById(0));
		assertEquals(CampaignQuestHandler.KILL_IGNORED, q.countKill(qs, 216489)); // outro monstro
		assertEquals(18, q.countKill(qs, 215502)); // o 7º abate fecha em 18
		assertEquals(18, qs.getQuestVarById(0));
		assertEquals(CampaignQuestHandler.KILL_IGNORED, q.countKill(qs, 215502)); // não passa de 18
		assertEquals(Reply.Type.ADVANCE, q.decide(qs, 798950, SET_SUCCEED, false).type());
	}

	@Test
	void sectionKillsNeedAllTargets() {
		Mixed q = new Mixed();
		QuestState qs = start(10160, 5);
		assertEquals(CampaignQuestHandler.KILL_COUNTED, q.countKill(qs, 216489));
		assertEquals(CampaignQuestHandler.KILL_IGNORED, q.countKill(qs, 216489)); // SECTION_1<1: já tem
		assertEquals(CampaignQuestHandler.KILL_COUNTED, q.countKill(qs, 216491));
		assertEquals(5, qs.getQuestVarById(0));
		assertEquals(6, q.countKill(qs, 216490));
		assertEquals(6, qs.getQuestVarById(0));
		assertEquals(0, qs.getQuestVarById(1)); // a var nova zera os contadores das seções
	}

	@Test
	void repeatedObjectUsesAdvanceOneByOne() {
		Mixed q = new Mixed();
		QuestState qs = start(10160, 20);
		assertEquals(21, q.decide(qs, 700601, USE_OBJECT, true).value());
		qs.setQuestVar(24);
		assertEquals(25, q.decide(qs, 700601, USE_OBJECT, true).value());
		qs.setQuestVar(25);
		assertEquals(Reply.NONE, q.decide(qs, 700601, USE_OBJECT, true));
	}
}
